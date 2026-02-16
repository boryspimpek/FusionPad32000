# mode_rc.py
import network
import espnow
import machine
import struct
import time
import joystick
import buttons
import ST7735 # type: ignore

# --- KONFIGURACJA ODBIORNIKA ---
RECEIVER_MAC = b'\xff\xff\xff\xff\xff\xff'  # Wpisz MAC adres swojego C3 Zero

def map_to_rc(val, is_pot=False):
    """
    Konwertuje wartości z joysticka (-100 do 100) lub pot (0 do 100)
    na standardowy sygnał RC (1000us - 2000us)
    """
    if is_pot:
        # Potencjometr: 0 -> 1000, 100 -> 2000
        return 1000 + (val * 10)
    else:
        # Joystick: -100 -> 1000, 0 -> 1500, 100 -> 2000
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

    # Kolory
    BLACK = ST7735.TFT.BLACK
    WHITE = ST7735.TFT.WHITE
    GREEN = 0x07E0
    RED   = 0xF800

    tft.fill(BLACK)
    tft.text((10, 10), "MODE: RC (1000-2000us)", GREEN)
    tft.text((10, 110), "Hold SW1+SW2 to EXIT", RED)

    exit_timer = 0
    
    while True:
        # Pobieranie surowych danych (-100 do 100 / 0 do 100)
        joy_data = joystick.get_data() 
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()

        # Mapowanie na standard RC (mikrosekundy)
        ch1 = map_to_rc(joy_data[1])  # LY
        ch2 = map_to_rc(joy_data[0])  # LX
        ch3 = map_to_rc(joy_data[3])  # RY
        ch4 = map_to_rc(joy_data[2])  # RX
        
        # Przyciski SW3/SW4 jako kanały binarne (1000us lub 2000us)
        ch5 = 2000 if btns['sw3'] else 1000
        ch6 = 2000 if btns['sw4'] else 1000
        
        # Potencjometr
        ch7 = map_to_rc(pots['pot1'], is_pot=True)

        # Pakowanie danych (7x short - 14 bajtów)
        data_packet = struct.pack('7h', ch1, ch2, ch3, ch4, ch5, ch6, ch7)

        try:
            e.send(RECEIVER_MAC, data_packet, False)
        except OSError:
            pass

        # Podgląd na ekranie
        tft.fillrect((10, 40), (140, 60), BLACK)
        tft.text((10, 40), f"CH1(LY): {ch1}us", WHITE)
        tft.text((10, 55), f"CH3(RY): {ch3}us", WHITE)
        tft.text((10, 70), f"P1: {ch7}us", WHITE)
        tft.text((10, 85), f"SW: {ch5}/{ch6}", WHITE)

        # Wyjście: SW1 + SW2 przez 2 sekundy
        if btns['sw1'] and btns['sw2']:
            if exit_timer == 0:
                exit_timer = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), exit_timer) > 2000:
                break
        else:
            exit_timer = 0

        time.sleep(0.02)

    e.active(False)
    sta.active(False)