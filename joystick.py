# joystick.py

# Kalibracja według FIZYCZNEJ POZYCJI
CAL = {
    "LEFT_X": {"min": 97,  "mid": 13000, "max": 26270},
    "LEFT_Y": {"min": 102, "mid": 12734, "max": 26272},
    "RIGHT_X": {"min": 101, "mid": 12729, "max": 26267},
    "RIGHT_Y": {"min": 101, "mid": 12994, "max": 26267},
}

# Kalibracja potencjometrów (0-100%)
POT_CAL = {
    "POT1": {"min": 100, "max": 26270},  # Potencjometr na ADS1
    "POT2": {"min": 100, "max": 26270},  # Potencjometr na ADS2
}

# Referencje do obiektów
ads1 = None
ads2 = None

def init(ads1_instance, ads2_instance):
    """Przyjmuje gotowe instancje ADS1115"""
    global ads1, ads2
    ads1 = ads1_instance
    ads2 = ads2_instance
    print("✓ Moduł joystick zainicjalizowany")

def _map_axis(val, config, invert=False):
    deadzone = 1000
    if abs(val - config["mid"]) < deadzone:
        return 0
    
    if val < config["mid"]:
        result = int(((val - config["min"]) / (config["mid"] - config["min"]) * 100) - 100)
    else:
        result = int(((val - config["mid"]) / (config["max"] - config["mid"]) * 100))
    
    return -result if invert else result

def _map_pot(val, config, invert=False):
    """Mapuje potencjometr na zakres 0-100%"""
    val = max(config["min"], min(config["max"], val))
    result = int((val - config["min"]) / (config["max"] - config["min"]) * 100)
    return 100 - result if invert else result

def get_data():
    """Zwraca [LEWY_X, LEWY_Y, PRAWY_X, PRAWY_Y]"""
    if ads1 is None or ads2 is None:
        raise RuntimeError("Moduł joystick nie zainicjalizowany!")
    
    try:
        ads1_ch1 = ads1.read(rate=4, channel1=1)
        ads1_ch2 = ads1.read(rate=4, channel1=2)
        ads2_ch1 = ads2.read(rate=4, channel1=1)
        ads2_ch2 = ads2.read(rate=4, channel1=2)
        
        return [
            _map_axis(ads2_ch2, CAL["LEFT_X"]),
            _map_axis(ads2_ch1, CAL["LEFT_Y"]),
            _map_axis(ads1_ch1, CAL["RIGHT_X"], invert=True),
            _map_axis(ads1_ch2, CAL["RIGHT_Y"], invert=True),
        ]
    except OSError as e:
        print(f"Błąd odczytu joysticków: {e}")
        return [0, 0, 0, 0]

def get_potentiometers():
    """Zwraca słownik {'pot1': 0-100, 'pot2': 0-100}"""
    if ads1 is None or ads2 is None:
        raise RuntimeError("Moduł joystick nie zainicjalizowany!")
    
    try:
        pot2_raw = ads1.read(rate=4, channel1=0)
        pot1_raw = ads2.read(rate=4, channel1=0)
        
        return {
            'pot1': _map_pot(pot1_raw, POT_CAL["POT1"], invert=True),  # Zmień na True żeby odwrócić
            'pot2': _map_pot(pot2_raw, POT_CAL["POT2"], invert=True),   # Zmień na True żeby odwrócić
        }
    except OSError as e:
        print(f"Błąd odczytu potencjometrów: {e}")
        return {'pot1': 0, 'pot2': 0}
    
def get_all():
    """Zwraca wszystko razem: (joystick_data, potentiometers)"""
    return get_data(), get_potentiometers()