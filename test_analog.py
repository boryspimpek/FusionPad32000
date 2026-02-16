import machine
import time
from ads1x15 import ADS1115

print("=== RAW TEST ADS1115 / JOYSTICK ===")

# --- I2C ---
i2c = machine.I2C(
    0,
    scl=machine.Pin(22),
    sda=machine.Pin(21),
    freq=400000
)

# --- ADS1115 ---
ads1 = ADS1115(i2c, address=0x48, gain=1)
ads2 = ADS1115(i2c, address=0x49, gain=1)

time.sleep(0.5)
print("Porusz joystickami... Ctrl+C aby wyjść\n")

# --- Pętla RAW ---
while True:
    raw = {
        "LX": ads2.read(rate=4, channel1=2),
        "LY": ads2.read(rate=4, channel1=1),
        "RX": ads1.read(rate=4, channel1=1),
        "RY": ads1.read(rate=4, channel1=2),
        "POT1": ads2.read(rate=4, channel1=0),
        "POT2": ads1.read(rate=4, channel1=0),
    }

    print(
        "LX:{:>5}  LY:{:>5}  RX:{:>5}  RY:{:>5} | P1:{:>5}  P2:{:>5}"
        .format(
            raw["LX"], raw["LY"],
            raw["RX"], raw["RY"],
            raw["POT1"], raw["POT2"]
        )
    )

    time.sleep(0.15)  # ważne dla USB / REPL
