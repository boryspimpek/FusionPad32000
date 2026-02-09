# start.py
import machine # type: ignore
import time
from ads1x15 import ADS1115 # type: ignore
import joystick
import buttons
import menu
import ST7735 # type: ignore

# --- I2C ---
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21), freq=400000)
ads1 = ADS1115(i2c, address=0x48, gain=1)
ads2 = ADS1115(i2c, address=0x49, gain=1)
joystick.init(ads1, ads2)
buttons.init(i2c, pcf_address=0x20)

# --- SPI & TFT ---
spi = machine.SPI(
    1,
    baudrate=20000000,
    polarity=0,
    phase=0,
    sck=machine.Pin(18),
    mosi=machine.Pin(23),
    miso=machine.Pin(19)
)

dc_pin = machine.Pin(27, machine.Pin.OUT)
rst_pin = machine.Pin(4, machine.Pin.OUT)
cs_pin = machine.Pin(5, machine.Pin.OUT)

# Inicjalizacja TFT
tft = ST7735.TFT(spi, dc_pin, rst_pin, cs_pin)

# Inicjalizacja wyświetlacza (Red Tab)
tft.initr()
tft.rgb(True)
tft.rotation(1)  # Landscape
tft.fill(ST7735.TFT.BLACK)  # Wyczyść ekran

while True:
    wybor = menu.show(tft)
    
    if wybor == "PC Gamepad":
        import mode_gamepad
        mode_gamepad.run(tft)
    elif wybor == "RC Transmitter":
        import mode_rc
        mode_rc.run(tft)
    elif wybor == "Robot Controller":
        import mode_robot
        mode_robot.run(tft)