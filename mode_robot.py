import network # type: ignore
import espnow # type: ignore
import struct
import time
import joystick
import buttons
import ST7735 # type: ignore
import glcdfont

# Konfiguracja
FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": glcdfont.font}
RECEIVER_MAC = b'\x98\x88\xe0\xd1\x82<' 

def run(tft):
    # --- Inicjalizacja transmisji ---
    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    e = espnow.ESPNow()
    e.active(True)
    try:
        e.add_peer(RECEIVER_MAC)
    except OSError:
        pass

    # --- UI ---
    BLACK = ST7735.TFT.BLACK
    WHITE = ST7735.TFT.WHITE
    CYAN  = 0x07FF
    RED   = 0xF800

    tft.fill(BLACK)
    tft.text((25, 20), "ROBOT MODE", CYAN, FONT, 1)
    tft.text((15, 110), "HOLD SW1+SW2 TO EXIT", RED, FONT, 1)

    exit_timer = 0

    # --- Główna pętla ---
    while True:
        # 1. Odczyt danych
        joy = joystick.get_data()
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()

        # 2. Pakowanie przycisków w maskę bitową
        btn_mask = 0

        # bt1–bt8 → bity 0–7
        for i in range(8):
            if btns.get(f'bt{i+1}'):
                btn_mask |= (1 << i)

        # sw3–sw4 → bity 8–9
        if btns.get('sw3'):
            btn_mask |= (1 << 8)
        if btns.get('sw4'):
            btn_mask |= (1 << 9)

        # 3. Ramka binarna (7 bajtów)
        data_packet = struct.pack(
            '4bBH',
            joy[0], joy[1], joy[2], joy[3],
            pots.get('pot1', 0),
            btn_mask
        )

        # 4. Wysyłka (ultra-low latency)
        try:
            e.send(RECEIVER_MAC, data_packet, False)
        except OSError:
            pass

        # 5. HOLD SW1 + SW2 → wyjście
        if btns.get('sw1') and btns.get('sw2'):
            if exit_timer == 0:
                exit_timer = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), exit_timer) > 2000:
                break
        else:
            exit_timer = 0

        time.sleep_ms(20)  # 50 Hz

    # --- Wyjście z trybu: wymuszenie puszczenia przycisków ---
    tft.fill(BLACK)
    tft.text((20, 60), "RELEASE BUTTONS...", WHITE, FONT, 1)

    while buttons.get_data().get('sw1') or buttons.get_data().get('sw2'):
        time.sleep_ms(50)

    # --- Sprzątanie ---
    e.active(False)
    sta.active(False)
