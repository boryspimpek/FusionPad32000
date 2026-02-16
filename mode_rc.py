# mode_rc.py
import network
import espnow
import machine
import struct
import time
import joystick
import buttons
import ST7735 # type: ignore
import glcdfont

# Konfiguracja czcionki
FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": glcdfont.font}

# --- KONFIGURACJA ODBIORNIKA ---
RECEIVER_MAC = b'\xff\xff\xff\xff\xff\xff' 

def map_to_rc(val, is_pot=False):
    if is_pot:
        return 1000 + (val * 10)
    else:
        return 1500 + (val * 5)

def run(tft):
    # Inicjalizacja sieci
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    e = espnow.ESPNow()
    e.active(True)
    
    try:
        e.add_peer(RECEIVER_MAC)
    except OSError:
        pass

    BLACK = ST7735.TFT.BLACK
    WHITE = ST7735.TFT.WHITE
    GREEN = 0x07E0
    RED   = 0xF800

    # Rysujemy ekran tylko RAZ na początku
    tft.fill(BLACK)
    tft.text((38, 20), "RC TRANSMITTER", WHITE, FONT, 1)
    tft.text((65, 60), "READY", GREEN, FONT, 1)
    tft.text((20, 115), "HOLD SW1+SW2 TO EXIT", RED, FONT, 1)

    exit_timer = 0
    
    while True:
        # 1. Błyskawiczny odczyt danych
        joy_data = joystick.get_data() 
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()

        # 2. Mapowanie
        current_data = [
            map_to_rc(joy_data[1]),           # CH1: LY
            map_to_rc(joy_data[0]),           # CH2: LX
            map_to_rc(joy_data[3]),           # CH3: RY
            map_to_rc(joy_data[2]),           # CH4: RX
            2000 if btns['sw3'] else 1000,    # CH5: SW3
            2000 if btns['sw4'] else 1000,    # CH6: SW4
            map_to_rc(pots['pot1'], True)     # CH7: POT1
        ]

        # 3. Wysyłka bez czekania na potwierdzenie (False = Turbo)
        try:
            e.send(RECEIVER_MAC, struct.pack('7h', *current_data), False)
        except OSError:
            pass

        # 4. Obsługa wyjścia
        if btns['sw1'] and btns['sw2']:
            if exit_timer == 0:
                exit_timer = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), exit_timer) > 2000:
                break
        else:
            exit_timer = 0

        # Minimalna przerwa, aby nie zapchać bufora, ale utrzymać płynność
        time.sleep_ms(10) # 100Hz - standard profesjonalnych aparatur RC

    # Wyjście z trybu
    tft.fill(BLACK)
    tft.text((20, 60), "RELEASE BUTTONS...", WHITE, FONT, 1)
    while buttons.get_data()['sw1'] or buttons.get_data()['sw2']:
        time.sleep(0.05)
    
    e.active(False)
    sta.active(False)