# calibration.py
import machine, time
from ads1x15 import ADS1115 # type: ignore

i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21))
ads1 = ADS1115(i2c, address=0x48, gain=1)  # Fizycznie PRAWY joystick
ads2 = ADS1115(i2c, address=0x49, gain=1)  # Fizycznie LEWY joystick

def read_raw(ads, ch):
    return ads.read(rate=4, channel1=ch)

def calibrate():
    print("\n=== START KALIBRACJI ===")
    print("ads1 (0x48) = PRAWY joystick")
    print("ads2 (0x49) = LEWY joystick")
    print("\nKROK 1: Puść drążki (pozycja NEUTRALNA).")
    print("Czekam 3 sekundy...")
    time.sleep(3)
    
    # Pobranie wartości środkowych (średnia z 5 pomiarów dla stabilności)
    mids = [0] * 4
    for _ in range(5):
        mids[0] += read_raw(ads1, 1)  # Prawy X (fizycznie)
        mids[1] += read_raw(ads1, 2)  # Prawy Y (fizycznie)
        mids[2] += read_raw(ads2, 1)  # Lewy X (fizycznie Y)
        mids[3] += read_raw(ads2, 2)  # Lewy Y (fizycznie X)
        time.sleep(0.05)
    mids = [int(x/5) for x in mids]

    print(f"Zapisano środki: {mids}")
    print("\nKROK 2: Masz 10 sekund na kręcenie drążkami!")
    print("Rób pełne kółka, dociskając do krawędzi.")
    
    mins = list(mids)
    maxs = list(mids)
    
    start = time.time()
    while time.time() - start < 10:
        cur = [read_raw(ads1, 1), read_raw(ads1, 2), read_raw(ads2, 1), read_raw(ads2, 2)]
        for i in range(4):
            if cur[i] < mins[i]: mins[i] = cur[i]
            if cur[i] > maxs[i]: maxs[i] = cur[i]
        print(".", end="")
        time.sleep(0.05)

    print("\n\n=== WYNIKI KALIBRACJI ===")
    print("Skopiuj te wartości do joystick.py:\n")
    
    # Nazwy zgodne z joystick.py
    names = ["RIGHT_X", "RIGHT_Y", "LEFT_X", "LEFT_Y"]
    
    print("CAL = {")
    print(f'    "LEFT_X": {{"min": {mins[2]}, "mid": {mids[2]}, "max": {maxs[2]}}},')
    print(f'    "LEFT_Y": {{"min": {mins[3]}, "mid": {mids[3]}, "max": {maxs[3]}}},')
    print(f'    "RIGHT_X": {{"min": {mins[0]}, "mid": {mids[0]}, "max": {maxs[0]}}},')
    print(f'    "RIGHT_Y": {{"min": {mins[1]}, "mid": {mids[1]}, "max": {maxs[1]}}},')
    print("}")
    
    print("\n=== SZCZEGÓŁY ===")
    for i, name in enumerate(names):
        print(f"{name:8}: Min={mins[i]:5}, Mid={mids[i]:5}, Max={maxs[i]:5}")

# Uruchomienie
calibrate()