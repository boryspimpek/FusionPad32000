# mode_rc.py
import network # type: ignore
import espnow # type: ignore
import machine # type: ignore
import struct
import time
import joystick
import buttons
import ST7735 # type: ignore
import glcdfont

# Konfiguracja czcionki
FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": glcdfont.font}

# --- KONFIGURACJA ODBIORNIKA ---
RECEIVER_MAC = b'\x98\x88\xe0\xd1\x82<'

BLACK = ST7735.TFT.BLACK
WHITE = ST7735.TFT.WHITE
GREEN = 0x07E0
RED   = 0xF800
CYAN   = 0x07FF
GRAY   = 0x4208

def clamp(v, min_v, max_v):
    return max(min_v, min(max_v, v))

def center_x(text, screen_w=160, char_w=6):
    return (screen_w - len(text) * char_w) // 2

def run(tft):
    # 1. INICJALIZACJA ESP-NOW
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    e = espnow.ESPNow()
    e.active(True)
    try:
        e.add_peer(RECEIVER_MAC)
    except:
        pass

    # USTAWIENIA POCZĄTKOWE
    trims = [0, 0, 0, 0]        # LY, LX, RY, RX
    d_rates = [1.0, 1.0, 1.0, 1.0]
    current_page = -1
    last_btns = {f'bt{i}': False for i in range(1, 9)}
    exit_timer = 0

    # Timery UI
    last_ui_update = time.ticks_ms()
    ui_interval = 50

    running = True
    while running:
        # --- 1. ODCZYT DANYCH (Szybki) ---
        joy_raw = joystick.get_data()
        # Mapowanie osi: LY, LX, RY, RX
        joy_ordered = [joy_raw[1], joy_raw[0], joy_raw[3], joy_raw[2]]
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()

        # --- 2. MIKSOWANIE I WYSYŁKA (Krytyczne dla serw) ---
        # Aplikujemy Dual Rates i Trimy do osi głównych
        final_channels = [
            1500 + int((clamp((joy_ordered[i] * d_rates[i]) + trims[i], -140, 140)) * 5)
            for i in range(4)
        ]
        # Kanały pomocnicze (Przełączniki i Potencjometr)
        final_channels.extend([
            2000 if btns['sw3'] else 1000,
            2000 if btns['sw4'] else 1000,
            1000 + int(pots['pot1'] * 10)
        ])

        try:
            e.send(RECEIVER_MAC, struct.pack('7h', *final_channels), False)
        except:
            pass

        # --- 3. LOGIKA PRZYCISKÓW (Detekcja kliknięcia - Edge Detection) ---
        changed_trims = False
        changed_dr = False

        # Pary przycisków: (Plus, Minus) dla każdej z 4 osi
        pairs = [('bt8', 'bt7'), ('bt6', 'bt5'), ('bt3', 'bt4'), ('bt1', 'bt2')]

        for i, (p, m) in enumerate(pairs):
            # Logika dla strony TRIM (Strona 1)
            if current_page == 1:
                if btns[p] and not last_btns[p]:
                    trims[i] = clamp(trims[i] + 1, -20, 20)
                    changed_trims = True
                if btns[m] and not last_btns[m]:
                    trims[i] = clamp(trims[i] - 1, -20, 20)
                    changed_trims = True

            # Logika dla strony DUAL RATES (Strona 2)
            elif current_page == 2:
                if btns[p] and not last_btns[p]:
                    d_rates[i] = clamp(d_rates[i] + 0.05, 0.4, 1.4) # Krok 5%
                    changed_dr = True
                if btns[m] and not last_btns[m]:
                    d_rates[i] = clamp(d_rates[i] - 0.05, 0.4, 1.4)
                    changed_dr = True

        # Renderowanie natychmiastowe przy zmianie wartości (płynność UI)
        if changed_trims:
            update_trim_values(tft, trims)
        if changed_dr:
            update_dr_values(tft, d_rates)

        # Aktualizacja stanu przycisków dla następnej pętli
        for k in last_btns:
            last_btns[k] = btns[k]

        # --- 4. PRZEŁĄCZANIE STRON I MONITORING (Co interwał UI) ---
        now = time.ticks_ms()
        if time.ticks_diff(now, last_ui_update) > ui_interval:
            last_ui_update = now

            # Wybór strony potencjometrem pot2 (teraz 4 strony: 0, 1, 2, 3)
            p2 = pots['pot2']
            if p2 < 25: new_page = 0
            elif p2 < 50: new_page = 1
            elif p2 < 75: new_page = 2
            else: new_page = 3

            if new_page != current_page:
                current_page = new_page
                tft.fill(BLACK)
                draw_static_ui(tft, current_page)

                # Wymuszenie odświeżenia wartości przy wejściu na stronę
                if current_page == 0:
                    tft.text((center_x("READY"), 60), "READY", GREEN, FONT, 2)
                elif current_page == 1:
                    update_trim_values(tft, trims)
                elif current_page == 2:
                    update_dr_values(tft, d_rates)
                elif current_page == 3:
                    update_raw_channels(tft)

        # --- 5. ODSWIEŻANIE DANYCH RAW (Jeśli aktywna strona 3) ---
        if current_page == 3 and time.ticks_diff(now, last_ui_update) == 0: # wyzwalane interwałem UI
             update_raw_channels(tft)

        # --- 6. OBSŁUGA WYJŚCIA (SW1 + SW2 przez 2 sekundy) ---
        if btns['sw1'] and btns['sw2']:
            if exit_timer == 0:
                exit_timer = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), exit_timer) > 2000:
                running = False
        else:
            exit_timer = 0

        time.sleep_ms(2) # Minimalny sleep dla stabilności procesora

    # SPRZĄTANIE PO WYJŚCIU
    tft.fill(BLACK)
    tft.text((center_x("RELEASE BUTTONS"), 60), "RELEASE BUTTONS...", WHITE, FONT, 1)
    while buttons.get_data()['sw1'] or buttons.get_data()['sw2']:
        time.sleep_ms(50)

    e.active(False)
    sta.active(False)

# --- FUNKCJE RYSOWANIA GUI ---

def update_trim_values(tft, trims, force=False):
    for i, val in enumerate(trims):
        y = 40 + (i * 22)
        # Czyścimy tylko obszar tekstu i paska kursora
        tft.fillrect((135, y), (25, 8), BLACK)
        tft.text((135, y), str(val), GREEN, FONT, 1)

        # UI paska
        tft.fillrect((30, y-2), (100, 10), BLACK)
        tft.hline((30, y + 3), 100, GRAY)
        tft.vline((80, y), 7, WHITE) # Ponowne rysowanie środka
        tft.vline((80 + (val * 2), y-2), 10, CYAN) # Kursor

def draw_static_ui(tft, page):
    tft.rect((0, 0), (160, 20), CYAN)
    titles = ["MODE: MONITOR", "MODE: TRIMS", "MODE: DUAL RATES", "MODE: RAW ADC"]
    tft.text((center_x(titles[page]), 7), titles[page], CYAN, FONT, 1)

    labels = ["LY", "LX", "RY", "RX"]
    if page == 1: # Trims UI
        for i, label in enumerate(labels):
            y = 40 + (i * 22)
            tft.text((5, y), label, WHITE, FONT, 1)
            tft.hline((30, y + 3), 100, GRAY)
            tft.vline((80, y), 7, WHITE)

    elif page == 2: # Dual Rates UI
        for i, label in enumerate(labels):
            y = 40 + (i * 22)
            tft.text((5, y), f"AXIS {label}:", WHITE, FONT, 1)
            # Rysujemy tło paska (opcjonalnie dla bajeru)
            tft.rect((70, y-2), (52, 10), GRAY)

    elif page == 3: # Raw ADC UI
        for i, label in enumerate(labels):
            y = 40 + (i * 22)
            tft.text((5, y), f"{label} ADC:", WHITE, FONT, 1)

def update_dr_values(tft, d_rates):
    for i, val in enumerate(d_rates):
        y = 40 + (i * 22)
        perc = int(val * 100)
        color = GREEN if val <= 1.0 else RED

        # Czyścimy tylko obszar wartości i paska
        tft.fillrect((71, y-1), (50, 8), BLACK)
        tft.fillrect((125, y), (35, 8), BLACK)

        # Rysujemy mały słupek postępu (wizualizacja DR)
        bar_w = int((val - 0.5) * 60) # Skalowanie paska
        tft.fillrect((71, y-1), (bar_w, 8), color)

        # Tekst procentowy
        tft.text((125, y), f"{perc}%", color, FONT, 1)

def update_raw_channels(tft):
    # Wykorzystujemy globalne instancje ADS z modułu joystick
    try:
        vals = [
            joystick.ads2.read(rate=4, channel1=1), # LY
            joystick.ads2.read(rate=4, channel1=2), # LX
            joystick.ads1.read(rate=4, channel1=2), # RY
            joystick.ads1.read(rate=4, channel1=1), # RX
        ]
        for i, val in enumerate(vals):
            y = 40 + (i * 22)
            tft.fillrect((80, y), (60, 8), BLACK)
            tft.text((80, y), str(val), 0xFFE0, FONT, 1) # Yellow
    except:
        pass
