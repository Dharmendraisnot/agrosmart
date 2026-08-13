"""
hardware/raspberry_pi.py — Real Raspberry Pi 5 sensor implementation.

⚠  IMPORT GUARD: This file must ONLY be imported by hal.py, never directly.
   All GPIO libraries (RPi.GPIO, adafruit_dht, w1thermsensor, etc.) are ARM/Pi
   specific and will fail to import on development machines.

   Install deps ONLY on the Pi:
       pip install -r requirements-pi.txt

Hardware connections (per hardware diagram):
    Capacitive Moisture Sensor  → MCP3008 ADC channel 0  (SPI)
    Soil pH Sensor              → MCP3008 ADC channel 1  (SPI)
    DS18B20 Temperature         → GPIO4  (1-Wire, pull-up required)
    DHT22 Temp + Humidity       → GPIO5
    NPK Sensor (RS485/UART)     → /dev/ttyUSB0  (USB-to-RS485 adapter)
    OLED Display (I2C)          → GPIO2 SDA, GPIO3 SCL  (I2C bus 1)
    Raspberry Pi Camera         → CSI ribbon connector

MCP3008 SPI wiring:
    MCP3008 VDD  → 3.3V
    MCP3008 VREF → 3.3V
    MCP3008 AGND → GND
    MCP3008 CLK  → GPIO11 (SCLK)
    MCP3008 DOUT → GPIO9  (MISO)
    MCP3008 DIN  → GPIO10 (MOSI)
    MCP3008 CS   → GPIO8  (CE0)
    MCP3008 DGND → GND
"""
from __future__ import annotations

import logging
import time
import struct
from typing import Optional

from .hal import SensorInterface, SensorReadError

logger = logging.getLogger(__name__)

# ── Calibration constants (adjust after physical calibration) ─────────────────
# Moisture sensor: raw ADC counts at 0% (dry in air) and 100% (submerged)
MOISTURE_ADC_DRY = 750    # ADC count when sensor is dry in air
MOISTURE_ADC_WET = 310    # ADC count when sensor is fully submerged

# pH sensor: voltage-to-pH linear calibration
# Calibrate with pH 4.0 and pH 7.0 buffer solutions
# pH = PH_SLOPE * voltage + PH_INTERCEPT
PH_SLOPE      = -5.70    # adjust after calibration
PH_INTERCEPT  = 21.34    # adjust after calibration

# MCP3008 SPI reference voltage
ADC_VREF = 3.3

# NPK sensor RS485 command bytes (Modbus RTU)
# These are standard commands for common RS485 NPK soil sensors
NPK_SLAVE_ADDR  = 0x01
NPK_CMD_READ    = 0x03
NPK_REG_START   = 0x001E   # register 30 = N, 31 = P, 32 = K
NPK_REG_COUNT   = 0x0003   # read 3 registers
NPK_BAUD_RATE   = 9600

# OLED display dimensions
OLED_WIDTH  = 128
OLED_HEIGHT = 64


class RaspberryPiSensor(SensorInterface):
    """
    Reads all sensors from real Raspberry Pi 5 hardware.

    Initialisation imports GPIO libraries (ARM only).
    Failed imports raise ImportError which hal.py converts to a user-friendly message.
    """

    def __init__(self):
        logger.info("Initialising RaspberryPiSensor (hardware mode)")
        self._init_adc()
        self._init_dht22()
        self._init_ds18b20()
        self._init_npk()
        self._init_oled()
        logger.info("RaspberryPiSensor initialised successfully")

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_adc(self):
        """Initialise MCP3008 ADC via SPI (for moisture + pH sensors)."""
        import spidev
        self._spi = spidev.SpiDev()
        self._spi.open(0, 0)           # bus 0, device 0 (CE0)
        self._spi.max_speed_hz = 1_350_000
        self._spi.mode = 0
        logger.debug("MCP3008 SPI ADC initialised")

    def _init_dht22(self):
        """Initialise DHT22 temperature + humidity sensor."""
        import adafruit_dht
        import board
        self._dht = adafruit_dht.DHT22(board.D5)  # GPIO5
        logger.debug("DHT22 initialised on GPIO5")

    def _init_ds18b20(self):
        """
        DS18B20 uses the Linux 1-Wire interface (/sys/bus/w1/).
        Requires 'dtoverlay=w1-gpio,gpiopin=4' in /boot/config.txt
        and 'w1-gpio' + 'w1-therm' kernel modules loaded.
        """
        from w1thermsensor import W1ThermSensor
        try:
            self._ds18b20 = W1ThermSensor()
            logger.debug("DS18B20 found on 1-Wire bus")
        except Exception as exc:
            logger.warning("DS18B20 not found on 1-Wire bus: %s — "
                           "soil_temperature will return None", exc)
            self._ds18b20 = None

    def _init_npk(self):
        """Initialise RS485 serial port for NPK sensor."""
        import serial
        try:
            self._serial = serial.Serial(
                port='/dev/ttyUSB0',
                baudrate=NPK_BAUD_RATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
            )
            logger.debug("NPK RS485 serial port opened: /dev/ttyUSB0")
        except Exception as exc:
            logger.warning("NPK sensor serial port unavailable: %s — "
                           "NPK readings will return None", exc)
            self._serial = None

    def _init_oled(self):
        """Initialise SSD1306 OLED display via I2C."""
        try:
            from luma.core.interface.serial import i2c
            from luma.oled.device import ssd1306
            serial_i2c = i2c(port=1, address=0x3C)
            self._oled = ssd1306(serial_i2c,
                                 width=OLED_WIDTH,
                                 height=OLED_HEIGHT)
            logger.debug("OLED SSD1306 initialised on I2C bus 1, address 0x3C")
        except Exception as exc:
            logger.warning("OLED display not available: %s — display writes ignored", exc)
            self._oled = None

    # ── ADC helper (MCP3008) ──────────────────────────────────────────────────

    def _read_adc_channel(self, channel: int) -> int:
        """
        Read a 10-bit value (0–1023) from MCP3008 channel 0–7.
        Uses the standard SPI transfer protocol for MCP3008.
        """
        if not (0 <= channel <= 7):
            raise ValueError(f"MCP3008 channel must be 0–7, got {channel}")
        # SPI message: start bit, single-ended mode, channel select
        msg = [1, (8 + channel) << 4, 0]
        resp = self._spi.xfer2(msg)
        # Extract 10-bit result from response bytes
        return ((resp[1] & 3) << 8) | resp[2]

    def _adc_to_voltage(self, raw: int) -> float:
        """Convert raw 10-bit ADC reading to voltage (0–VREF)."""
        return (raw / 1023.0) * ADC_VREF

    # ── SensorInterface implementation ────────────────────────────────────────

    def read_moisture(self) -> float:
        """
        Read capacitive soil moisture from MCP3008 channel 0.
        Returns percentage 0–100.

        Capacitive sensors output HIGHER voltage when DRY and LOWER when WET
        (inverse of resistive sensors).
        """
        raw = self._read_adc_channel(0)
        # Map ADC count to percentage (inverted: dry=high count, wet=low count)
        pct = (MOISTURE_ADC_DRY - raw) / (MOISTURE_ADC_DRY - MOISTURE_ADC_WET) * 100.0
        pct = max(0.0, min(100.0, pct))
        logger.debug("Moisture ADC raw=%d → %.1f%%", raw, pct)
        return round(pct, 1)

    def read_ph(self) -> float:
        """
        Read soil pH from analog pH sensor via MCP3008 channel 1.
        Uses linear calibration: pH = slope * voltage + intercept.
        Calibrate with pH 4.0 and pH 7.0 buffer solutions.
        """
        raw     = self._read_adc_channel(1)
        voltage = self._adc_to_voltage(raw)
        ph      = PH_SLOPE * voltage + PH_INTERCEPT
        ph      = max(0.0, min(14.0, ph))
        logger.debug("pH ADC raw=%d, voltage=%.3fV → pH=%.2f", raw, voltage, ph)
        return round(ph, 2)

    def read_soil_temperature(self) -> Optional[float]:
        """
        Read soil temperature from DS18B20 (1-Wire, GPIO4).
        Returns None if sensor is not detected.
        """
        if self._ds18b20 is None:
            return None
        try:
            temp = self._ds18b20.get_temperature()
            logger.debug("DS18B20 soil temperature: %.1f°C", temp)
            return round(float(temp), 1)
        except Exception as exc:
            logger.warning("DS18B20 read failed: %s", exc)
            raise SensorReadError(f"DS18B20 read failed: {exc}") from exc

    def read_air_temperature(self) -> Optional[float]:
        """Read ambient air temperature from DHT22 (GPIO5)."""
        return self._read_dht22()[0]

    def read_air_humidity(self) -> Optional[float]:
        """Read ambient humidity from DHT22 (GPIO5)."""
        return self._read_dht22()[1]

    def _read_dht22(self) -> tuple[Optional[float], Optional[float]]:
        """
        DHT22 can occasionally fail; retry up to 3 times with 2s delay.
        Returns (temperature_c, humidity_pct) or (None, None) on failure.
        """
        for attempt in range(3):
            try:
                temp = self._dht.temperature
                humi = self._dht.humidity
                if temp is not None and humi is not None:
                    logger.debug("DHT22 temp=%.1f°C humi=%.1f%%", temp, humi)
                    return round(float(temp), 1), round(float(humi), 1)
            except RuntimeError:
                # DHT22 occasionally throws RuntimeError on bad read; retry
                if attempt < 2:
                    time.sleep(2.0)
        logger.warning("DHT22 failed after 3 attempts")
        return None, None

    def read_npk(self) -> dict:
        """
        Read N, P, K values from RS485 NPK sensor via Modbus RTU.

        Returns dict with keys: nitrogen, phosphorus, potassium (all in mg/kg).
        Values are None if serial port is unavailable.
        """
        if self._serial is None:
            return {"nitrogen": None, "phosphorus": None, "potassium": None}

        try:
            cmd = self._build_npk_command()
            self._serial.reset_input_buffer()
            self._serial.write(cmd)
            time.sleep(0.1)   # Allow sensor response time

            response = self._serial.read(11)  # 11 bytes: addr+func+len+6data+2crc
            if len(response) < 11:
                logger.warning("NPK sensor: short response (%d bytes)", len(response))
                return {"nitrogen": None, "phosphorus": None, "potassium": None}

            n = struct.unpack(">H", response[3:5])[0]
            p = struct.unpack(">H", response[5:7])[0]
            k = struct.unpack(">H", response[7:9])[0]

            logger.debug("NPK raw: N=%d P=%d K=%d mg/kg", n, p, k)
            return {
                "nitrogen":   float(n),
                "phosphorus": float(p),
                "potassium":  float(k),
            }
        except Exception as exc:
            logger.error("NPK sensor read failed: %s", exc)
            return {"nitrogen": None, "phosphorus": None, "potassium": None}

    def _build_npk_command(self) -> bytes:
        """
        Build a Modbus RTU read holding registers command.
        Frame: [addr, func, reg_hi, reg_lo, count_hi, count_lo, crc_lo, crc_hi]
        """
        frame = bytes([
            NPK_SLAVE_ADDR,
            NPK_CMD_READ,
            (NPK_REG_START >> 8) & 0xFF,
            NPK_REG_START & 0xFF,
            (NPK_REG_COUNT >> 8) & 0xFF,
            NPK_REG_COUNT & 0xFF,
        ])
        crc   = self._modbus_crc16(frame)
        return frame + bytes([crc & 0xFF, (crc >> 8) & 0xFF])

    @staticmethod
    def _modbus_crc16(data: bytes) -> int:
        """Compute Modbus CRC-16 checksum."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def read_all(self) -> dict:
        """
        Read all sensors in one efficient pass.
        DHT22 is read once (avoids double 2s retry delay).
        """
        air_temp, air_humi = self._read_dht22()
        npk = self.read_npk()

        data = {
            "moisture":         self.read_moisture(),
            "ph":               self.read_ph(),
            "soil_temperature": self.read_soil_temperature(),
            "air_temperature":  air_temp,
            "air_humidity":     air_humi,
            "nitrogen":         npk["nitrogen"],
            "phosphorus":       npk["phosphorus"],
            "potassium":        npk["potassium"],
        }

        # Write summary to OLED display
        self._update_oled(data)

        return data

    # ── OLED display ──────────────────────────────────────────────────────────

    def _update_oled(self, data: dict) -> None:
        """
        Update the SSD1306 OLED display with a summary of current readings.
        Silently skips if OLED was not initialised.
        """
        if self._oled is None:
            return
        try:
            from luma.core.render import canvas
            from PIL import ImageFont

            with canvas(self._oled) as draw:
                def _fmt(v, unit=""):
                    return f"{v:.1f}{unit}" if v is not None else "N/A"

                lines = [
                    "AgroSmart",
                    f"M:{_fmt(data.get('moisture'), '%')}  pH:{_fmt(data.get('ph'))}",
                    f"T:{_fmt(data.get('soil_temperature'), 'C')}",
                    f"N:{_fmt(data.get('nitrogen'))}  P:{_fmt(data.get('phosphorus'))}",
                    f"K:{_fmt(data.get('potassium'))}",
                ]
                for i, line in enumerate(lines):
                    draw.text((0, i * 13), line, fill="white")

        except Exception as exc:
            logger.debug("OLED update failed (non-fatal): %s", exc)

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def cleanup(self) -> None:
        """
        Release hardware resources gracefully.
        Call on application shutdown (optional — OS handles this on exit).
        """
        try:
            if hasattr(self, '_spi') and self._spi:
                self._spi.close()
            if hasattr(self, '_dht') and self._dht:
                self._dht.exit()
            if hasattr(self, '_serial') and self._serial and self._serial.is_open:
                self._serial.close()
            if hasattr(self, '_oled') and self._oled:
                self._oled.cleanup()
            logger.info("RaspberryPiSensor hardware resources released")
        except Exception as exc:
            logger.warning("Cleanup warning: %s", exc)
