# AgroSmart — Hardware Setup Guide

## Overview

This guide covers wiring, enabling interfaces, calibration, and switching
from simulator mode to real hardware mode.

---

## 1. Hardware Required

| Component | Model | Interface |
|-----------|-------|-----------|
| Microcontroller | Raspberry Pi 5 | — |
| ADC Chip | MCP3008 | SPI |
| Soil Moisture Sensor | Capacitive (e.g. STEMMA) | ADC channel 0 |
| Soil pH Sensor | Analog pH probe + module | ADC channel 1 |
| Soil Temperature | DS18B20 | 1-Wire (GPIO4) |
| Ambient Temp + Humidity | DHT22 | GPIO5 |
| NPK Sensor | RS485 UART NPK module | USB-to-RS485 → /dev/ttyUSB0 |
| Display | SSD1306 OLED 128×64 | I2C (GPIO2/3) |
| Camera | Raspberry Pi Camera Module | CSI ribbon |
| Power Supply | 5V 3A Type-C | — |

---

## 2. Wiring Diagram

### MCP3008 ADC (SPI)

```
MCP3008 Pin  →  Raspberry Pi 5
─────────────────────────────────
VDD          →  3.3V  (Pin 1)
VREF         →  3.3V  (Pin 1)
AGND         →  GND   (Pin 6)
CLK          →  GPIO11 SCLK  (Pin 23)
DOUT (MISO)  →  GPIO9  MISO  (Pin 21)
DIN  (MOSI)  →  GPIO10 MOSI  (Pin 19)
CS/SHDN      →  GPIO8  CE0   (Pin 24)
DGND         →  GND   (Pin 6)
```

### Capacitive Moisture Sensor

```
Sensor Pin  →  Connection
─────────────────────────
VCC         →  3.3V
GND         →  GND
AOUT        →  MCP3008 CH0
```

### Soil pH Sensor

```
Sensor Pin  →  Connection
─────────────────────────
VCC         →  3.3V
GND         →  GND
AOUT        →  MCP3008 CH1
```

### DS18B20 Soil Temperature (1-Wire)

```
DS18B20 Pin  →  Connection
──────────────────────────────────────────────
VDD (red)    →  3.3V  (Pin 1)
GND (black)  →  GND   (Pin 6)
DATA (yellow)→  GPIO4 (Pin 7)  + 4.7kΩ pull-up to 3.3V
```

> ⚠ The 4.7 kΩ pull-up resistor between DATA and VDD is **required**.
> Without it the DS18B20 will not respond.

### DHT22 (Air Temperature + Humidity)

```
DHT22 Pin  →  Connection
─────────────────────────
VCC (+)    →  3.3V  (Pin 1)
GND (-)    →  GND   (Pin 6)
DATA       →  GPIO5 (Pin 29)
```

### OLED Display (I2C)

```
OLED Pin  →  Raspberry Pi 5
────────────────────────────
VCC       →  3.3V  (Pin 1)
GND       →  GND   (Pin 6)
SDA       →  GPIO2 (Pin 3)
SCL       →  GPIO3 (Pin 5)
```

### NPK Sensor (RS485 via USB adapter)

```
NPK Module  →  USB-RS485 Adapter
──────────────────────────────────
A+          →  A+ terminal
B-          →  B- terminal
GND         →  GND

USB-RS485 Adapter  →  Raspberry Pi 5
─────────────────────────────────────
USB                →  Any USB port  (/dev/ttyUSB0)
```

---

## 3. Enable Required Interfaces on the Pi

Run `sudo raspi-config` and enable:

```
Interface Options → SPI       → Enable
Interface Options → I2C       → Enable
Interface Options → 1-Wire    → Enable
Interface Options → Camera    → Enable (Legacy Camera if using picamera2)
```

Add to `/boot/config.txt` (reboot after):
```ini
# 1-Wire for DS18B20 on GPIO4
dtoverlay=w1-gpio,gpiopin=4

# SPI for MCP3008
dtparam=spi=on

# I2C for OLED
dtparam=i2c_arm=on
```

Load kernel modules (add to `/etc/modules`):
```
w1-gpio
w1-therm
```

---

## 4. Install Dependencies on the Pi

```bash
# Install system dependencies first
sudo apt update
sudo apt install -y python3-pip libgpiod2 python3-libgpiod

# Install Pi-specific Python packages
cd agrosmart/backend
pip install -r requirements-pi.txt
```

---

## 5. Sensor Calibration

### Moisture Sensor Calibration

1. Run the sensor in air (completely dry) → note ADC raw value → set `MOISTURE_ADC_DRY`
2. Submerge sensor in water → note ADC raw value → set `MOISTURE_ADC_WET`
3. Edit `raspberry_pi.py`:
   ```python
   MOISTURE_ADC_DRY = <your dry reading>
   MOISTURE_ADC_WET = <your wet reading>
   ```

### pH Sensor Calibration (2-point calibration)

1. Place probe in **pH 7.0 buffer** → record voltage `V7`
2. Place probe in **pH 4.0 buffer** → record voltage `V4`
3. Calculate:
   ```
   PH_SLOPE      = (4.0 - 7.0) / (V4 - V7)
   PH_INTERCEPT  = 7.0 - PH_SLOPE * V7
   ```
4. Edit `raspberry_pi.py`:
   ```python
   PH_SLOPE     = <calculated value>
   PH_INTERCEPT = <calculated value>
   ```

### DS18B20 Verification

Compare reading against a reference thermometer.
The DS18B20 is factory-calibrated to ±0.5°C — no software calibration normally needed.

### DHT22 Verification

Compare against a reference hygrometer.
DHT22 accuracy: ±0.5°C temperature, ±2–5% humidity.

---

## 6. Run Individual Sensor Tests

Before starting the full application on Pi, verify each sensor:

```bash
cd agrosmart/backend
python pi_sensor_tests/test_all_sensors.py
```

Expected output for all sensors working:
```
[1] MCP3008 ADC          PASS  Channel 0 raw = 512  Channel 1 raw = 615
[2] DS18B20              PASS  Soil temperature = 24.5 °C
[3] DHT22                PASS  Air temperature = 28.0 °C  Humidity = 65.0%
[4] NPK Sensor           PASS  N=42 P=18 K=156 mg/kg
[5] OLED Display         PASS  Display updated — check screen
[6] Pi Camera            PASS  Frame captured: shape=(1944, 2592, 3)
```

Fix any FAIL items before proceeding.

---

## 7. Switch from Simulator to Hardware Mode

Edit `agrosmart/backend/.env`:

```ini
# Change this line:
SENSOR_MODE=simulator

# To:
SENSOR_MODE=hardware
```

Restart the Flask server:

```bash
cd agrosmart/backend
python run.py
```

Verify with:
```bash
curl http://localhost:5000/api/health
# Should return: {"sensor_mode": "hardware", ...}
```

Then call:
```bash
curl http://localhost:5000/api/sensors/latest
# Should return real sensor values, source: "hardware"
```

---

## 8. Running as a System Service (optional)

Create `/etc/systemd/system/agrosmart.service`:

```ini
[Unit]
Description=AgroSmart Flask Backend
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/agrosmart/backend
Environment=SENSOR_MODE=hardware
ExecStart=/home/pi/agrosmart/backend/.venv/bin/python run.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable agrosmart
sudo systemctl start agrosmart
sudo systemctl status agrosmart
```

---

## 9. Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| DS18B20 not found | Missing pull-up or overlay | Add 4.7kΩ resistor; enable w1-gpio overlay |
| SPI not working | SPI disabled | `raspi-config` → Interface → SPI → Enable |
| DHT22 fails repeatedly | Timing issue | Add 10kΩ pull-up on DATA line; try GPIO pin change |
| OLED blank | Wrong I2C address | Run `i2cdetect -y 1`; change address in `raspberry_pi.py` |
| NPK no response | Wrong baud rate or port | Check `ls /dev/ttyUSB*`; some sensors use 4800 baud |
| `ImportError: No module named 'spidev'` | Wrong requirements file | Use `requirements-pi.txt` not `requirements.txt` |
| Application crashes on Pi import | GPIO library missing | `pip install -r requirements-pi.txt` |
