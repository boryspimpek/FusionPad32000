import network # type: ignore
import espnow # type: ignore
import struct
import time
import joystick
import buttons
import ST7735 # type: ignore
import glcdfont

FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": glcdfont.font}
# Lista MAC adresów odbiorników
RECEIVER_MACS = [
    b'\x5c\x01\x3b\x6c\x1c\x48',  # Pierwszy odbiornik
    b'\x98\x88\xe0\xd1\x82\x3c'   # Drugi odbiornik (zakomentowany wcześniej)
]
current_mac_index = 0  # Indeks aktualnego MAC

# Kolory
BLACK  = ST7735.TFT.BLACK
WHITE  = ST7735.TFT.WHITE
CYAN   = 0x07FF
YELLOW = 0xFFE0
GREEN  = 0x07E0
RED    = 0xF800
GRAY   = 0x4208

# Tryby/ekrany (wysyłane też w ramce ESP-NOW)
MODE_MAIN    = 0  # ekran z joystickami
MODE_SCREEN2 = 1  # pierwszy ekran akcji
MODE_SCREEN3 = 2  # drugi ekran akcji

def pad(val, width=4):
    s = str(val)
    return ' ' * (width - len(s)) + s

def mac_to_str(mac):
    return ':'.join('%02x' % b for b in mac)

def draw_btn(tft, x, y, label, pressed):
    color = GREEN if pressed else GRAY
    tft.text((x, y), label, color, FONT, 1)

def center_x(text, screen_w=160, char_w=6):
    return (screen_w - len(text) * char_w) // 2

def run(tft):
    global current_mac_index
    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    e = espnow.ESPNow()
    e.active(True)
    try:
        e.add_peer(RECEIVER_MACS[current_mac_index])
    except OSError:
        pass

    # --- Układ 160x128, czcionka 5x7 → znak 6x8px ---

    OX    = 10          # margines lewy (~2 znaki)
    OY    = 40          # margines górny
    COL_L = OX          # lewa kolumna joysticków
    COL_R = OX + 80     # prawa kolumna joysticków
    VAL_L = COL_L + 26  # miejsce na wartość (za 4-znakowym nagłówkiem)
    VAL_R = COL_R + 26

    def draw_header(title):
        tft.rect((5, 5), (150, 25), ST7735.TFT.CYAN)
        tft.text((center_x(title), 13), title, ST7735.TFT.YELLOW, FONT, 1)

    def draw_main_screen():
        tft.fill(BLACK)
        draw_header("OTTO GAMEPAD")
        tft.text((COL_L, OY +  0), "J1X:", CYAN,   FONT, 1)
        tft.text((COL_R, OY +  0), "J2X:", CYAN,   FONT, 1)
        tft.text((COL_L, OY + 12), "J1Y:", CYAN,   FONT, 1)
        tft.text((COL_R, OY + 12), "J2Y:", CYAN,   FONT, 1)
        tft.text((COL_L, OY + 24), "POT:", YELLOW, FONT, 1)
        tft.text((COL_L, OY + 36), "BT:",  WHITE,  FONT, 1)
        tft.text((COL_L, OY + 48), "SW:",  WHITE,  FONT, 1)
        tft.text((COL_L, OY + 60), "MAC:", RED,    FONT, 1)
        tft.text((center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", RED, FONT, 1)

    def draw_simple_screen(label):
        tft.fill(BLACK)
        title = "OTTO ACTIONS 1" if label == "screen2" else "OTTO ACTIONS 2"
        draw_header(title)

        # Layout (pod nagłówkiem, nad czerwonym napisem)
        LIST_Y = 45
        ROW_H = 16
        X_L = 5
        X_R = 89

        if label == "screen2":
            left = [" Forward L1", "    Back L2", "    Wave L3", "    Tilt L4"]
            right = ["R1 Forward", "R2 Back", "R3 Arms", "R4 Steps"]
        else:  # "screen3"
            left = [" Circles L1", "   Steps L2", "   Steps L3", "    Toes L4"]
            right = ["R1 Spin", "R2 Boogie", "R3 Balerina", "R4 Weird"]

        for i in range(4):
            y = LIST_Y + i * ROW_H
            tft.text((X_L, y), left[i], WHITE, FONT, 1)
            tft.text((X_R, y), right[i], WHITE, FONT, 1)

        tft.text((center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", RED, FONT, 1)

    tx_count   = 0
    exit_timer = 0
    prev = {}
    current_screen = -1
    prev_mac = None

    while True:
        joy  = joystick.get_data()
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()

        # Przełączanie MAC za pomocą SW2
        if btns.get('sw2') and not prev.get('sw2', False):
            current_mac_index = (current_mac_index + 1) % len(RECEIVER_MACS)
            try:
                e.add_peer(RECEIVER_MACS[current_mac_index])
            except OSError:
                pass
            prev_mac = None  # Zmuszamy odświeżenie MAC
        prev['sw2'] = btns.get('sw2')

        # Wybór ekranu potencjometrem (POT2)
        pot2_val = pots.get('pot2', 0)
        # mapujemy 0–100 → 0,1,2 (MODE_MAIN / MODE_SCREEN2 / MODE_SCREEN3)
        new_screen = min(int((pot2_val * 3) / 101), MODE_SCREEN3)

        if new_screen != current_screen:
            current_screen = new_screen
            prev.clear()
            if current_screen == MODE_MAIN:
                draw_main_screen()
                prev_mac = None  # Zmuszamy odświeżenie MAC przy przejściu na główny ekran
            elif current_screen == MODE_SCREEN2:
                draw_simple_screen("screen2")
            else:  # MODE_SCREEN3
                draw_simple_screen("screen3")

        if current_screen == MODE_MAIN:
            # Joysticki + potencjometr
            vals = {
                'j1x': (joy[0],              VAL_L, OY +  0),
                'j1y': (joy[1],              VAL_L, OY + 12),
                'j2x': (joy[2],              VAL_R, OY +  0),
                'j2y': (joy[3],              VAL_R, OY + 12),
                'pot': (pots.get('pot1', 0), VAL_L, OY + 24),
            }
            for key, (v, x, y) in vals.items():
                if prev.get(key) != v:
                    tft.fillrect((x, y), (30, 8), BLACK)
                    tft.text((x, y), pad(v), WHITE, FONT, 1)
                    prev[key] = v

            # Przyciski bt1–bt8
            bt_changed = any(
                prev.get(f'bt{i+1}') != bool(btns.get(f'bt{i+1}'))
                for i in range(8)
            )
            if bt_changed:
                x_bt = COL_L + 20
                tft.fillrect((x_bt, OY + 36), (160 - x_bt, 8), BLACK)
                x = x_bt
                for i in range(8):
                    pressed = bool(btns.get(f'bt{i+1}'))
                    color = GREEN if pressed else GRAY
                    tft.text((x, OY + 36), str(i + 1), color, FONT, 1)
                    prev[f'bt{i+1}'] = pressed
                    x += 16

            # Switche sw1–sw4
            sw_changed = any(
                prev.get(sw) != bool(btns.get(sw))
                for sw in ['sw1', 'sw2', 'sw3', 'sw4']
            )
            if sw_changed:
                x_sw = COL_L + 20
                tft.fillrect((x_sw, OY + 48), (160 - x_sw, 8), BLACK)
                x = x_sw
                for sw in ['sw1', 'sw2', 'sw3', 'sw4']:
                    pressed = bool(btns.get(sw))
                    color = GREEN if pressed else GRAY
                    tft.text((x, OY + 48), sw.upper(), color, FONT, 1)
                    prev[sw] = pressed
                    x += 34

            # Rysowanie MAC tylko gdy się zmienił
            current_mac = RECEIVER_MACS[current_mac_index]
            if prev_mac != current_mac:
                tft.fillrect((COL_L + 30, OY + 60), (120, 8), BLACK)
                tft.text((COL_L + 30, OY + 60), mac_to_str(current_mac), RED, FONT, 1)
                prev_mac = current_mac

        # Pakowanie i wysyłka
        btn_mask = 0
        for i in range(8):
            if btns.get(f'bt{i+1}'):
                btn_mask |= (1 << i)
        if btns.get('sw3'):
            btn_mask |= (1 << 8)
        if btns.get('sw4'):
            btn_mask |= (1 << 9)

        # Pakiet: 4 * joystick (b), 1 * pot1 (B), 1 * ekran (B), maska przycisków (H)
        # Format: 4bBBH  →  joy0, joy1, joy2, joy3, pot1, screen, btn_mask
        data_packet = struct.pack(
            '4bBBH',
            joy[0], joy[1], joy[2], joy[3],
            pots.get('pot1', 0),
            current_screen & 0xFF,
            btn_mask
        )

        try:
            e.send(RECEIVER_MACS[current_mac_index], data_packet, False)
            tx_count += 1
        except OSError:
            pass

        # Wyjście: SW1 + SW2 przez 2 sekundy
        if btns.get('sw1') and btns.get('sw2'):
            if exit_timer == 0:
                exit_timer = time.ticks_ms()
            elif time.ticks_diff(time.ticks_ms(), exit_timer) > 2000:
                break
        else:
            exit_timer = 0

        time.sleep_ms(20)  # 50 Hz

    tft.fill(BLACK)
    tft.text((20, 60), "RELEASE BUTTONS...", WHITE, FONT, 1)
    while buttons.get_data().get('sw1') or buttons.get_data().get('sw2'):
        time.sleep_ms(50)

    e.active(False)
    sta.active(False)
