# FusionPad-32 🎮

**FusionPad-32** is an advanced, high-performance universal controller powered by the **ESP32**. It features a custom graphical interface, Hall Effect precision joysticks, buttons, switches and potentiometers.

<img src="images/1.jpg" width="400">

## 🛠️ Hardware Specifications

### Control & Inputs:
* **2x PS4 Joysticks (Hall Effect):** Magnetic sensors for zero-drift precision. Includes L3/R3 buttons.
* **2x Rotary Potentiometers:** Smooth analog dials for fine adjustments.
* **8x Tactile Switches:** Managed via the **PCF8574** I2C expander.
* **2x Toggle Switches:** Physical heavy-duty switches for mode selection.
* **2x Shoulder Bumpers:** Front-facing triggers.

### Interface & Power:
* **1.8" TFT Display (ST7735):** Real-time system monitoring.
* **Power System:** Physical ON/OFF switch, status LED, and a **voltage divider** for battery telemetry.
* **Storage:** MicroSD slot for splash screens and data logging.

---

## 💻 Data Acquisition (ADC) Mapping
<img src="images/6.jpg" width="400"> <img src="images/7.jpg" width="400">
The project uses two **ADS1115** (16-bit) converters to handle high-resolution analog data:

### ADS1 (Address: 0x48)
| Channel | Type | Description |
|:---:|:---|:---|
| **A0** | 🎚️ Pot | Potentiometer #1 |
| **A1** | 🕹️ Joy 1 | Axis X (Hall Effect) |
| **A2** | 🕹️ Joy 1 | Axis Y (Hall Effect) |

### ADS2 (Address: 0x49)
| Channel | Type | Description |
|:---:|:---|:---|
| **A0** | 🎚️ Pot | Potentiometer #2 |
| **A1** | 🕹️ Joy 2 | Axis X (Hall Effect) |
| **A2** | 🕹️ Joy 2 | Axis Y (Hall Effect) |
| **A3** | 🔋 Bat | Battery Monitoring |

---
<img src="images/2.jpg" width="400"> <img src="images/3.jpg" width="400">

## 🔌 Full Pinout Mapping (ESP32)

Below is the complete pin configuration as defined in the source code:

### 📺 Display & SD Card (SPI)
| Component | ESP32 Pin | Function |
|:---|:---:|:---|
| **TFT_CS** | 5 | TFT Chip Select |
| **TFT_DC** | 27 | TFT Data/Command |
| **TFT_RST** | 4 | TFT Reset |
| **TFT_BLK** | 15 | Display Backlight (PWM/Digital) |
| **SD_CS** | 13 | SD Card Chip Select |
| **SPI_SCK** | 18 | Shared SPI Clock |
| **SPI_MOSI**| 23 | Shared SPI Data Out |
| **SPI_MISO**| 19 | Shared SPI Data In (SD Card) |

### 🛠️ I2C Bus (Peripherals)
*Used for both ADS1115 ADCs and the PCF8574 Expander.*
| Signal | ESP32 Pin | Description |
|:---|:---:|:---|
| **SDA** | 21 | I2C Data Line |
| **SCL** | 22 | I2C Clock Line |

### 🔘 Direct Digital Inputs (Toggle Switches / Buttons)
| Label | ESP32 Pin | Type |
|:---|:---:|:---|
| **SW 1** | 14 | Digital Input (Internal Pull-up) |
| **SW 2** | 32 | Digital Input (Internal Pull-up) |
| **SW 3** | 33 | Digital Input (Internal Pull-up) |
| **SW 4** | 25 | Digital Input (Internal Pull-up) |

---
> **Note:** The 8 tact switches are not connected directly to the ESP32 but are routed through the **PCF8574** expander at I2C address `0x20`.
## 🚀 Quick Start

1. **Libraries:** Install `Adafruit GFX`, `ST7735`, `ADS1X15`, and `PCF8574` via Arduino Library Manager.
2. **SD Card:** Place `.bmp` assets in the root directory.
3. **Wiring:** Ensure I2C pull-up resistors are installed for the ADS and PCF modules.

