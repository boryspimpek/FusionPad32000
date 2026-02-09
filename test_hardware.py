# main.py
import machine
import time
from ads1x15 import ADS1115
import joystick
import buttons

print("Inicjalizacja...")

# === INICJALIZACJA HARDWARE ===
i2c = machine.I2C(0, 
                  scl=machine.Pin(22), 
                  sda=machine.Pin(21),
                  freq=100000)

print(f"I2C devices: {[hex(x) for x in i2c.scan()]}")

ads1 = ADS1115(i2c, address=0x48, gain=1)
ads2 = ADS1115(i2c, address=0x49, gain=1)

joystick.init(ads1, ads2)
buttons.init(i2c, pcf_address=0x20)

print("Start monitoring...\n")
iteration = 0

while True:
    try:
        # Odczyt joysticków i potencjometrów
        lx, ly, rx, ry = joystick.get_axes()
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()
        
        # Format przycisków
        pressed = [name for name, state in sorted(btns.items()) if state]
        btn_status = " ".join(pressed) if pressed else "---"
        
        # Wyświetlanie
        print(f"\rL:[{lx:>4},{ly:>4}] R:[{rx:>4},{ry:>4}] "
              f"POT1:{pots['pot1']:>3}% POT2:{pots['pot2']:>3}% | "
              f"{btn_status:<30} #{iteration:>5}", end='')
        
        iteration += 1
        time.sleep(0.15)
        
    except KeyboardInterrupt:
        print("\n\nZatrzymano.")
        break
    except Exception as e:
        print(f"\nBŁĄD: {e}")
        time.sleep(1)
