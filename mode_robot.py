import network # type: ignore
import espnow # type: ignore
import struct
import time
import joystick
import buttons
import ST7735 # type: ignore
import glcdfont

FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": glcdfont.font}
RECEIVER_MAC = b'\x98\x88\xe0\xd1\x82<'

# Kolory
BLACK  = ST7735.TFT.BLACK
WHITE  = ST7735.TFT.WHITE
CYAN   = 0x07FF
YELLOW = 0xFFE0
GREEN  = 0x07E0
RED    = 0xF800
GRAY   = 0x4208

def pad(val, width=4):
    s = str(val)
    return ' ' * (width - len(s)) + s

def draw_btn(tft, x, y, label, pressed):
    color = GREEN if pressed else GRAY
    tft.text((x, y), label, color, FONT, 1)

def center_x(text, screen_w=160, char_w=6):
    return (screen_w - len(text) * char_w) // 2

def run(tft):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    e = espnow.ESPNow()
    e.active(True)
    try:
        e.add_peer(RECEIVER_MAC)
    except OSError:
        pass

    tft.fill(BLACK)

    # --- Układ 160x128, czcionka 5x7 → znak 6x8px ---
    #
    # y=  0  "J1X:" [val]   |  "J2X:" [val]   (dwie kolumny)
    # y= 12  "J1Y:" [val]   |  "J2Y:" [val]
    # y= 24  "POT:" [val]
    # y= 36  "BT:" 1 2 3 4 5 6 7 8
    # y= 52  "SW:" SW1 SW2 SW3 SW4
    # y= 68  "TX:" [count]
    # y= 82  "HOLD SW1+SW2=EXIT"          (90px łącznie → mieści się)

    OX    = 10          # margines lewy (~2 znaki)
    OY    = 40          # margines górny
    COL_L = OX          # lewa kolumna joysticków
    COL_R = OX + 80     # prawa kolumna joysticków
    VAL_L = COL_L + 26  # miejsce na wartość (za 4-znakowym nagłówkiem)
    VAL_R = COL_R + 26

    # Nagłówki — rysujemy raz
    tft.rect((5, 5), (150, 25), ST7735.TFT.CYAN)
    tft.text((center_x("ROBOT CONTROLLER"), 13), "ROBOT CONTROLLER", ST7735.TFT.CYAN, FONT, 1)
    tft.text((COL_L, OY +  0), "J1X:", CYAN,   FONT, 1)
    tft.text((COL_R, OY +  0), "J2X:", CYAN,   FONT, 1)
    tft.text((COL_L, OY + 12), "J1Y:", CYAN,   FONT, 1)
    tft.text((COL_R, OY + 12), "J2Y:", CYAN,   FONT, 1)
    tft.text((COL_L, OY + 24), "POT:", YELLOW, FONT, 1)
    tft.text((COL_L, OY + 36), "BT:",  WHITE,  FONT, 1)
    tft.text((COL_L, OY + 52), "SW:",  WHITE,  FONT, 1)
    tft.text((COL_L, OY + 68), "TX:",  GRAY,   FONT, 1)
    tft.text((center_x("HOLD SW1+SW2=EXIT"), 118), "HOLD SW1+SW2=EXIT", RED, FONT, 1)

    tx_count   = 0
    exit_timer = 0
    prev = {}

    while True:
        joy  = joystick.get_data()
        pots = joystick.get_potentiometers()
        btns = buttons.get_data()

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
            tft.fillrect((x_sw, OY + 52), (160 - x_sw, 8), BLACK)
            x = x_sw
            for sw in ['sw1', 'sw2', 'sw3', 'sw4']:
                pressed = bool(btns.get(sw))
                color = GREEN if pressed else GRAY
                tft.text((x, OY + 52), sw.upper(), color, FONT, 1)
                prev[sw] = pressed
                x += 34

        # Pakowanie i wysyłka
        btn_mask = 0
        for i in range(8):
            if btns.get(f'bt{i+1}'):
                btn_mask |= (1 << i)
        if btns.get('sw3'):
            btn_mask |= (1 << 8)
        if btns.get('sw4'):
            btn_mask |= (1 << 9)

        data_packet = struct.pack(
            '4bBH',
            joy[0], joy[1], joy[2], joy[3],
            pots.get('pot1', 0),
            btn_mask
        )

        try:
            e.send(RECEIVER_MAC, data_packet, False)
            tx_count += 1
        except OSError:
            pass

        if tx_count % 10 == 0:
            tft.fillrect((COL_L + 20, OY + 68), (80, 8), BLACK)
            tft.text((COL_L + 20, OY + 68), str(tx_count), GREEN, FONT, 1)

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
