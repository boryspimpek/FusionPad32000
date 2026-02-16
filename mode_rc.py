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
FONT = {
    "Width": 5,
    "Height": 7,
    "Start": 32,
    "End": 122,
    "Data": glcdfont.font
}

# --- KONFIGURACJA ODBIORNIKA ---
RECEIVER_MAC = b'\xff\xff\xff\xff\xff\xff' 

def map_to_rc(val, is_pot=False):
    """Konwersja na standard RC 1000-2000us"""
    if is_pot:
        return 1000 + (val * 10)
    else:
        return 1500 + (val * 5)

def run(tft):
    # Inicjalizacja ESP-NOW
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

    tft.fill(BLACK)
    tft.text((10, 5), "RC TRANSMITTER", GREEN, FONT, 1)
    tft.text((10, 115), "HOLD SW1+SW2 TO EXIT", RED, FONT, 1)

    exit_timer = 0
    last_data = [] # Do śledzenia zmian i redukcji mrugania

    while True:
        # Pobieranie danych
        joy_data = joystick.get_data() # [LX, LY, RX, RY]
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()

        # Mapowanie kanałów
        ch1 = map_to_rc(joy_data[1])           # LY
        ch2 = map_to_rc(joy_data[0])           # LX
        ch3 = map_to_rc(joy_data[3])           # RY
        ch4 = map_to_rc(joy_data[2])           # RX
        ch5 = 2000 if btns['sw3'] else 1000    # SW3
        ch6 = 2000 if btns['sw4'] else 1000    # SW4
        ch7 = map_to_rc(pots['pot1'], is_pot=True) # POT1

        current_data = [ch1, ch2, ch3, ch4, ch5, ch6, ch7]

        # Wysyłanie ramki
        data_packet = struct.pack('7h', *current_data)
        try:
            e.send(RECEIVER_MAC, data_packet, False)
        except OSError:
            pass

        # ODŚWIEŻANIE EKRANU (tylko jeśli dane się zmieniły)
        if current_data != last_data:
            # Zamiast czyścić cały obszar fillrect, czyścimy tylko tam gdzie są liczby
            # lub nadpisujemy stary tekst czarnym kolorem przed narysowaniem nowego.
            
            # Sekcja Lewy Joystick
            tft.fillrect((10, 25), (140, 20), BLACK) 
            tft.text((10, 25), f"L-Y: {ch1}us", WHITE, FONT, 1)
            tft.text((85, 25), f"L-X: {ch2}us", WHITE, FONT, 1)

            # Sekcja Prawy Joystick
            tft.fillrect((10, 50), (140, 20), BLACK)
            tft.text((10, 50), f"R-Y: {ch3}us", WHITE, FONT, 1)
            tft.text((85, 50), f"R-X: {ch4}us", WHITE, FONT, 1)

            # Sekcja Dodatki
            tft.fillrect((10, 75), (140, 30), BLACK)
            tft.text((10, 75), f"POT1: {ch7}us", WHITE, FONT, 1)
            tft.text((10, 90), f"SW3: {ch5}  SW4: {ch6}", WHITE, FONT, 1)
            
            last_data = current_data

        # Obsługa wyjścia (SW1 + SW2)
        if btns['sw1'] and btns['sw2']:
            if exit_timer == 0:
                exit_timer = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), exit_timer) > 2000:
                break
        else:
            exit_timer = 0

        time.sleep(0.02) # ~50Hz

# --- POPRAWKA: Czekaj na puszczenie przycisków przed wyjściem ---
    tft.fill(BLACK)
    tft.text((20, 60), "RELEASE BUTTONS...", WHITE, FONT, 1)
    
    while buttons.get_data()['sw1'] or buttons.get_data()['sw2']:
        time.sleep(0.05)

    # Teraz bezpiecznie wyłączamy i wracamy
    e.active(False)
    sta.active(False)