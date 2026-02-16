import machine
import time
from ads1x15 import ADS1115

# --- Konfiguracja I2C ---
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21), freq=400000)

# --- ADS1115 ---
ads1 = ADS1115(i2c, address=0x48, gain=1)
ads2 = ADS1115(i2c, address=0x49, gain=1)

channels = ["LX", "LY", "RX", "RY", "POT1", "POT2"]

def get_raw_values():
    """Odczytuje wszystkie kanały naraz"""
    return [
        ads2.read(rate=4, channel1=2), # LX
        ads2.read(rate=4, channel1=1), # LY
        ads1.read(rate=4, channel1=1), # RX
        ads1.read(rate=4, channel1=2), # RY
        ads2.read(rate=4, channel1=0), # POT1
        ads1.read(rate=4, channel1=0)  # POT2
    ]

# Inicjalizacja słowników dla wyników
mins = [32767] * 6
maxs = [0] * 6
centers = [0] * 6

print("=== START KALIBRACJI ===")

# --- ETAP 1: ŚRODEK (5 sekund) ---
print("\n[1/2] KALIBRACJA ŚRODKA (5 sek) - NIE DOTYKAJ JOYSTICKÓW!")
start_time = time.time()
samples = 0
sums = [0] * 6

while time.time() - start_time < 5:
    current = get_raw_values()
    for i in range(6):
        sums[i] += current[i]
    samples += 1
    time.sleep(0.05)

for i in range(6):
    centers[i] = sums[i] // samples

# --- ETAP 2: MIN/MAX (10 sekund) ---
print("\n[2/2] KALIBRACJA ZAKRESU (10 sek) - PORUSZAJ JOYSTICKAMI WE WSZYSTKIE STRONY!")
start_time = time.time()

while time.time() - start_time < 10:
    current = get_raw_values()
    for i in range(6):
        if current[i] < mins[i]: mins[i] = current[i]
        if current[i] > maxs[i]: maxs[i] = current[i]
    
    # Podgląd na żywo w terminalu
    print("Mins: {}  Maxs: {}".format(mins, maxs), end='\r')
    time.sleep(0.02)

# --- WYNIKI ---
print("\n\n=== WYNIKI KALIBRACJI ===")
print("{:<6} | {:>7} | {:>7} | {:>7}".format("OŚ", "MIN", "CENTER", "MAX"))
print("-" * 35)

for i in range(6):
    print("{:<6} | {:>7} | {:>7} | {:>7}".format(
        channels[i], mins[i], centers[i], maxs[i]
    ))

print("\nSkopiuj te wartości do swojego głównego kodu.")