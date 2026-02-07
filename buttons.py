# buttons.py
import machine # type: ignore

# Konfiguracja pinów GPIO
GPIO_BUTTONS = {
    'sw1': 14,
    'sw2': 25,
    'sw3': 32,
    'sw4': 33,
}

# Zmienne globalne
i2c = None
PCF_ADDR = None
gpio_pins = {}

def init(i2c_bus, pcf_address=0x20):
    """Inicjalizacja przycisków PCF8574 i GPIO"""
    global i2c, PCF_ADDR, gpio_pins
    
    i2c = i2c_bus
    PCF_ADDR = pcf_address
    
    # Inicjalizacja pinów GPIO z pull-up (przycisk do GND)
    for name, pin_num in GPIO_BUTTONS.items():
        gpio_pins[name] = machine.Pin(pin_num, machine.Pin.IN, machine.Pin.PULL_UP)
    
    print(f"✓ Przyciski zainicjalizowane (PCF8574: 0x{PCF_ADDR:02X}, GPIO: {list(GPIO_BUTTONS.keys())})")

def get_data():
    """
    Zwraca słownik z wszystkimi przyciskami:
    {'bt1': False, 'bt2': True, ..., 'bt8': False, 'sw1': False, ..., 'sw4': True}
    
    True = wciśnięty, False = zwolniony
    """
    if i2c is None or PCF_ADDR is None:
        raise RuntimeError("Moduł buttons nie zainicjalizowany!")
    
    result = {}
    
    # Odczyt PCF8574 (bt1-bt8)
    try:
        raw = i2c.readfrom(PCF_ADDR, 1)[0]
        for i in range(8):
            result[f'bt{i+1}'] = not bool(raw & (1 << i))  # Inwersja: 0 = wciśnięty
    except OSError as e:
        print(f"Błąd odczytu PCF8574: {e}")
        for i in range(8):
            result[f'bt{i+1}'] = False
    
    # Odczyt GPIO (sw1-sw4)
    for name, pin in gpio_pins.items():
        result[name] = not pin.value()  # Inwersja: 0 = wciśnięty (pull-up)
    
    return result

def get_pressed():
    """Zwraca listę nazw aktualnie wciśniętych przycisków"""
    data = get_data()
    return [name for name, pressed in data.items() if pressed]

def is_pressed(button_name):
    """Sprawdza czy konkretny przycisk jest wciśnięty"""
    return get_data().get(button_name, False)