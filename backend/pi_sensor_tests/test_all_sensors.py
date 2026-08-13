"""
pi_sensor_tests/test_all_sensors.py
Run this script ON THE RASPBERRY PI to verify each sensor individually
before running the full application.

Usage (on Pi):
    cd agrosmart/backend
    python pi_sensor_tests/test_all_sensors.py

Each test prints PASS / FAIL / WARN independently so you can identify
which sensors need attention before enabling SENSOR_MODE=hardware.
"""
import sys
import time

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}PASS{RESET}  {msg}")
def warn(msg): print(f"  {YELLOW}WARN{RESET}  {msg}")
def fail(msg): print(f"  {RED}FAIL{RESET}  {msg}")


# ── Test 1: MCP3008 ADC (SPI) — Moisture + pH channels ───────────────────────
def test_adc():
    print("\n[1] MCP3008 ADC (SPI) — moisture & pH channels")
    try:
        import spidev
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1_350_000

        def read_channel(ch):
            resp = spi.xfer2([1, (8 + ch) << 4, 0])
            return ((resp[1] & 3) << 8) | resp[2]

        ch0 = read_channel(0)
        ch1 = read_channel(1)
        spi.close()

        ok(f"Channel 0 (moisture) ADC raw = {ch0}  (expected 310–750)")
        ok(f"Channel 1 (pH)       ADC raw = {ch1}  (expected 300–900)")

        if ch0 == 0 or ch0 == 1023:
            warn("Channel 0 is saturated — check moisture sensor wiring")
        if ch1 == 0 or ch1 == 1023:
            warn("Channel 1 is saturated — check pH sensor wiring")

    except ImportError:
        fail("spidev not installed. Run: pip install spidev")
    except Exception as e:
        fail(f"SPI ADC error: {e}")


# ── Test 2: DS18B20 (1-Wire, GPIO4) ─────────────────────────────────────────
def test_ds18b20():
    print("\n[2] DS18B20 Soil Temperature (1-Wire / GPIO4)")
    try:
        from w1thermsensor import W1ThermSensor
        sensor = W1ThermSensor()
        temp = sensor.get_temperature()
        ok(f"Soil temperature = {temp:.1f} °C")
        if not (-10 <= temp <= 80):
            warn(f"Temperature {temp:.1f}°C is outside expected range (-10–80°C)")
    except ImportError:
        fail("w1thermsensor not installed. Run: pip install w1thermsensor")
    except Exception as e:
        fail(f"DS18B20 error: {e}\n"
             "  Ensure dtoverlay=w1-gpio,gpiopin=4 is in /boot/config.txt\n"
             "  and 4.7kΩ pull-up resistor is on the DATA line")


# ── Test 3: DHT22 (GPIO5) ────────────────────────────────────────────────────
def test_dht22():
    print("\n[3] DHT22 Air Temperature + Humidity (GPIO5)")
    try:
        import adafruit_dht
        import board
        dht = adafruit_dht.DHT22(board.D5)

        for attempt in range(3):
            try:
                temp = dht.temperature
                humi = dht.humidity
                if temp is not None and humi is not None:
                    ok(f"Air temperature = {temp:.1f} °C")
                    ok(f"Air humidity    = {humi:.1f} %")
                    dht.exit()
                    return
            except RuntimeError:
                if attempt < 2:
                    time.sleep(2)

        warn("DHT22 returned no data after 3 attempts (normal on first boot — retry)")
        dht.exit()
    except ImportError:
        fail("adafruit-circuitpython-dht not installed. Run: pip install adafruit-circuitpython-dht")
    except Exception as e:
        fail(f"DHT22 error: {e}")


# ── Test 4: NPK Sensor (RS485 / /dev/ttyUSB0) ────────────────────────────────
def test_npk():
    print("\n[4] NPK Sensor (RS485 Modbus / /dev/ttyUSB0)")
    try:
        import serial

        def crc16(data):
            crc = 0xFFFF
            for b in data:
                crc ^= b
                for _ in range(8):
                    crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
            return crc

        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1.0)
        frame = bytes([0x01, 0x03, 0x00, 0x1E, 0x00, 0x03])
        crc = crc16(frame)
        cmd = frame + bytes([crc & 0xFF, (crc >> 8) & 0xFF])

        ser.reset_input_buffer()
        ser.write(cmd)
        time.sleep(0.2)
        resp = ser.read(11)
        ser.close()

        if len(resp) >= 11:
            import struct
            n = struct.unpack(">H", resp[3:5])[0]
            p = struct.unpack(">H", resp[5:7])[0]
            k = struct.unpack(">H", resp[7:9])[0]
            ok(f"Nitrogen   (N) = {n} mg/kg")
            ok(f"Phosphorus (P) = {p} mg/kg")
            ok(f"Potassium  (K) = {k} mg/kg")
        else:
            warn(f"Short response ({len(resp)} bytes) — check RS485 adapter and baud rate (9600)")

    except ImportError:
        fail("pyserial not installed. Run: pip install pyserial")
    except serial.SerialException as e:
        warn(f"NPK serial port error: {e}\n"
             "  If NPK sensor not connected yet, this is expected.\n"
             "  Connect USB-to-RS485 adapter to /dev/ttyUSB0")
    except Exception as e:
        fail(f"NPK error: {e}")


# ── Test 5: OLED Display (I2C / GPIO2-3) ─────────────────────────────────────
def test_oled():
    print("\n[5] OLED SSD1306 Display (I2C / GPIO2 SDA, GPIO3 SCL)")
    try:
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306
        from luma.core.render import canvas

        serial_i2c = i2c(port=1, address=0x3C)
        device = ssd1306(serial_i2c, width=128, height=64)

        with canvas(device) as draw:
            draw.text((0, 0),  "AgroSmart",       fill="white")
            draw.text((0, 16), "Sensor Test OK",  fill="white")
            draw.text((0, 32), "All systems go!", fill="white")

        ok("OLED display updated successfully — check screen for 'AgroSmart'")
        time.sleep(2)
        device.cleanup()

    except ImportError:
        fail("luma.oled not installed. Run: pip install luma.oled")
    except Exception as e:
        fail(f"OLED error: {e}\n"
             "  Ensure I2C is enabled: sudo raspi-config → Interface Options → I2C")


# ── Test 6: Pi Camera ─────────────────────────────────────────────────────────
def test_camera():
    print("\n[6] Raspberry Pi Camera Module (CSI)")
    try:
        from picamera2 import Picamera2
        cam = Picamera2()
        config = cam.create_still_configuration()
        cam.configure(config)
        cam.start()
        time.sleep(1)
        frame = cam.capture_array()
        cam.stop()
        cam.close()
        ok(f"Camera frame captured: shape={frame.shape}, dtype={frame.dtype}")
        if frame.shape[0] < 100 or frame.shape[1] < 100:
            warn("Frame is very small — check camera cable connection")
    except ImportError:
        fail("picamera2 not installed. Run: pip install picamera2")
    except Exception as e:
        fail(f"Camera error: {e}\n"
             "  Ensure camera is enabled: sudo raspi-config → Interface Options → Camera")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  AgroSmart — Raspberry Pi Sensor Hardware Tests")
    print("=" * 55)

    test_adc()
    test_ds18b20()
    test_dht22()
    test_npk()
    test_oled()
    test_camera()

    print("\n" + "=" * 55)
    print("  Tests complete. Review WARN/FAIL items above.")
    print("  Once all sensors PASS, set SENSOR_MODE=hardware in .env")
    print("=" * 55)
