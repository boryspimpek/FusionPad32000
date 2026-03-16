import network # type: ignore
import espnow # type: ignore
import struct
import time
import joystick
import buttons
import ST7735 # type: ignore
import glcdfont

# === KONFIGURACJA I STAŁE ===
FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": glcdfont.font}

# MAC adresy odbiorników
RECEIVER_MACS = [
    b'\x5c\x01\x3b\x6c\x1c\x48',  # Pierwszy odbiornik
    b'\x98\x88\xe0\xd1\x82\x3c'   # Drugi odbiornik
]

# Kolory
BLACK  = ST7735.TFT.BLACK
WHITE  = ST7735.TFT.WHITE
CYAN   = 0x07FF
YELLOW = 0xFFE0
GREEN  = 0x07E0
RED    = 0xF800
GRAY   = 0x4208

# Tryby ekranów
MODE_MAIN    = 0  # ekran z joystickami
MODE_SCREEN2 = 1  # pierwszy ekran akcji
MODE_SCREEN3 = 2  # drugi ekran akcji

# Layout UI
UI_LAYOUT = {
    'MARGIN_LEFT': 10,
    'MARGIN_TOP': 40,
    'COL_LEFT': 10,          # lewa kolumna
    'COL_RIGHT': 90,         # prawa kolumna
    'VAL_LEFT': 36,          # wartości lewej kolumny
    'VAL_RIGHT': 116,        # wartości prawej kolumny
    'HEADER_HEIGHT': 25,
    'LIST_Y': 45,
    'ROW_HEIGHT': 16,
    'ACTION_X_LEFT': 5,
    'ACTION_X_RIGHT': 89
}

# Konfiguracja akcji robotów
ROBOT_ACTIONS = {
    'screen2': {
        'title': "OTTO ACTIONS 1",
        'left': [" Forward L1", "    Back L2", "    Wave L3", "    Tilt L4"],
        'right': ["R1 Forward", "R2 Back", "R3 Arms", "R4 Steps"]
    },
    'screen3': {
        'title': "OTTO ACTIONS 2", 
        'left': [" Circles L1", "   Steps L2", "   Steps L3", "    Toes L4"],
        'right': ["R1 Spin", "R2 Boogie", "R3 Balerina", "R4 Weird"]
    }
}

# Globalny stan
current_mac_index = 0

# Komunikacja
PACKET_FORMAT = '4bBBH'
UPDATE_RATE_MS = 20  # 50 Hz
EXIT_HOLD_TIME_MS = 2000

def pad(val, width=4):
    s = str(val)
    return ' ' * (width - len(s)) + s

def mac_to_str(mac):
    return ':'.join('%02x' % b for b in mac)

def center_x(text, screen_w=160, char_w=6):
    return (screen_w - len(text) * char_w) // 2

# === FUNKCJE UI ===
def draw_header(tft, title):
    """Rysuje nagłówek ekranu"""
    tft.rect((5, 5), (150, 25), ST7735.TFT.CYAN)
    tft.text((center_x(title), 13), title, ST7735.TFT.YELLOW, FONT, 1)

def draw_main_screen(tft):
    """Rysuje główny ekran z joystickami"""
    tft.fill(BLACK)
    draw_header(tft, "OTTO GAMEPAD")
    
    layout = UI_LAYOUT
    tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] +  0), "J1X:", CYAN,   FONT, 1)
    tft.text((layout['COL_RIGHT'], layout['MARGIN_TOP'] +  0), "J2X:", CYAN,   FONT, 1)
    tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 12), "J1Y:", CYAN,   FONT, 1)
    tft.text((layout['COL_RIGHT'], layout['MARGIN_TOP'] + 12), "J2Y:", CYAN,   FONT, 1)
    tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 24), "POT:", YELLOW, FONT, 1)
    tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 36), "BT:",  WHITE,  FONT, 1)
    tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 48), "SW:",  WHITE,  FONT, 1)
    tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 60), "MAC:", RED,    FONT, 1)
    tft.text((center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", RED, FONT, 1)

def draw_actions_screen(tft, screen_key):
    """Rysuje ekran akcji robotów"""
    tft.fill(BLACK)
    actions = ROBOT_ACTIONS[screen_key]
    draw_header(tft, actions['title'])
    
    layout = UI_LAYOUT
    
    for i in range(4):
        y = layout['LIST_Y'] + i * layout['ROW_HEIGHT']
        tft.text((layout['ACTION_X_LEFT'], y), actions['left'][i], WHITE, FONT, 1)
        tft.text((layout['ACTION_X_RIGHT'], y), actions['right'][i], WHITE, FONT, 1)
    
    tft.text((center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", RED, FONT, 1)

def update_joystick_display(tft, joy_data, prev_values):
    """Aktualizuje wyświetlanie wartości joysticków"""
    layout = UI_LAYOUT
    vals = {
        'j1x': (joy_data[0], layout['VAL_LEFT'], layout['MARGIN_TOP'] +  0),
        'j1y': (joy_data[1], layout['VAL_LEFT'], layout['MARGIN_TOP'] + 12),
        'j2x': (joy_data[2], layout['VAL_RIGHT'], layout['MARGIN_TOP'] +  0),
        'j2y': (joy_data[3], layout['VAL_RIGHT'], layout['MARGIN_TOP'] + 12),
    }
    
    for key, (value, x, y) in vals.items():
        if prev_values.get(key) != value:
            tft.fillrect((x, y), (30, 8), BLACK)
            tft.text((x, y), pad(value), WHITE, FONT, 1)
            prev_values[key] = value

def update_potentiometer_display(tft, pot_value, prev_values):
    """Aktualizuje wyświetlanie potencjometru"""
    layout = UI_LAYOUT
    if prev_values.get('pot') != pot_value:
        tft.fillrect((layout['VAL_LEFT'], layout['MARGIN_TOP'] + 24), (30, 8), BLACK)
        tft.text((layout['VAL_LEFT'], layout['MARGIN_TOP'] + 24), pad(pot_value), WHITE, FONT, 1)
        prev_values['pot'] = pot_value

def update_buttons_display(tft, btn_data, prev_values):
    """Aktualizuje wyświetlanie przycisków BT1-BT8"""
    layout = UI_LAYOUT
    bt_changed = any(
        prev_values.get(f'bt{i+1}') != bool(btn_data.get(f'bt{i+1}'))
        for i in range(8)
    )
    
    if bt_changed:
        x_bt = layout['COL_LEFT'] + 20
        tft.fillrect((x_bt, layout['MARGIN_TOP'] + 36), (160 - x_bt, 8), BLACK)
        x = x_bt
        for i in range(8):
            pressed = bool(btn_data.get(f'bt{i+1}'))
            color = GREEN if pressed else GRAY
            tft.text((x, layout['MARGIN_TOP'] + 36), str(i + 1), color, FONT, 1)
            prev_values[f'bt{i+1}'] = pressed
            x += 16

def update_switches_display(tft, btn_data, prev_values):
    """Aktualizuje wyświetlanie przełączników SW1-SW4"""
    layout = UI_LAYOUT
    sw_changed = any(
        prev_values.get(sw) != bool(btn_data.get(sw))
        for sw in ['sw1', 'sw2', 'sw3', 'sw4']
    )
    
    if sw_changed:
        x_sw = layout['COL_LEFT'] + 20
        tft.fillrect((x_sw, layout['MARGIN_TOP'] + 48), (160 - x_sw, 8), BLACK)
        x = x_sw
        for sw in ['sw1', 'sw2', 'sw3', 'sw4']:
            pressed = bool(btn_data.get(sw))
            color = GREEN if pressed else GRAY
            tft.text((x, layout['MARGIN_TOP'] + 48), sw.upper(), color, FONT, 1)
            prev_values[sw] = pressed
            x += 34

def update_mac_display(tft, mac_address, prev_mac):
    """Aktualizuje wyświetlanie adresu MAC"""
    layout = UI_LAYOUT
    if prev_mac != mac_address:
        tft.fillrect((layout['COL_LEFT'] + 30, layout['MARGIN_TOP'] + 60), (120, 8), BLACK)
        tft.text((layout['COL_LEFT'] + 30, layout['MARGIN_TOP'] + 60), mac_to_str(mac_address), RED, FONT, 1)
        return mac_address
    return prev_mac

# === FUNKCJE KOMUNIKACYJNE ===
def initialize_network():
    """Inicjalizuje sieć WiFi i ESP-NOW"""
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    esp = espnow.ESPNow()
    esp.active(True)
    
    return sta, esp

def add_peer(esp, mac_address):
    """Dodaje peer'a do ESP-NOW"""
    try:
        esp.add_peer(mac_address)
        return True
    except OSError:
        return False

def create_data_packet(joy_data, pot_value, screen_mode, btn_mask):
    """Tworzy pakiet danych do wysłania"""
    return struct.pack(
        PACKET_FORMAT,
        joy_data[0], joy_data[1], joy_data[2], joy_data[3],
        pot_value,
        screen_mode & 0xFF,
        btn_mask
    )

def create_button_mask(btn_data):
    """Tworzy maskę bitową przycisków"""
    btn_mask = 0
    
    # Przyciski BT1-BT8
    for i in range(8):
        if btn_data.get(f'bt{i+1}'):
            btn_mask |= (1 << i)
    
    # Przełączniki SW3, SW4
    if btn_data.get('sw3'):
        btn_mask |= (1 << 8)
    if btn_data.get('sw4'):
        btn_mask |= (1 << 9)
    
    return btn_mask

def send_data(esp, mac_address, data_packet):
    """Wysyła pakiet danych przez ESP-NOW"""
    try:
        esp.send(mac_address, data_packet, False)
        return True
    except OSError:
        return False

# === FUNKCJE STEROWANIA ===
def switch_mac_address(current_index, btn_data, prev_btn_data, esp):
    """Przełącza adres MAC przy wciśnięciu SW2"""
    if btn_data.get('sw2') and not prev_btn_data.get('sw2', False):
        new_index = (current_index + 1) % len(RECEIVER_MACS)
        add_peer(esp, RECEIVER_MACS[new_index])
        return new_index, None  # None zmusza odświeżenie MAC
    return current_index, prev_btn_data.get('current_mac')

def get_screen_mode(pot_value):
    """Wybiera tryb ekranu na podstawie wartości potencjometru"""
    return min(int((pot_value * 3) / 101), MODE_SCREEN3)

def check_exit_condition(btn_data, exit_timer):
    """Sprawdza warunek wyjścia (SW1 + SW2 przez 2 sekundy)"""
    if btn_data.get('sw1') and btn_data.get('sw2'):
        if exit_timer == 0:
            return time.ticks_ms(), False
        elif time.ticks_diff(time.ticks_ms(), exit_timer) > EXIT_HOLD_TIME_MS:
            return exit_timer, True
    return 0, False

def cleanup(tft, esp, sta):
    """Czyści zasoby przed wyjściem"""
    tft.fill(BLACK)
    tft.text((20, 60), "RELEASE BUTTONS...", WHITE, FONT, 1)
    
    while buttons.get_data().get('sw1') or buttons.get_data().get('sw2'):
        time.sleep_ms(50)
    
    esp.active(False)
    sta.active(False)

# === GŁÓWNA FUNKCJA ===
def run(tft):
    """Główna funkcja trybu robota"""
    global current_mac_index
    
    # Inicjalizacja
    sta, esp = initialize_network()
    add_peer(esp, RECEIVER_MACS[current_mac_index])
    
    # Stan aplikacji
    state = {
        'tx_count': 0,
        'exit_timer': 0,
        'prev_values': {},
        'current_screen': -1,
        'prev_mac': None,
        'prev_btn_data': {}
    }
    
    while True:
        # Odczyt danych wejściowych
        joy_data = joystick.get_data()
        pot_data = joystick.get_potentiometers()
        btn_data = buttons.get_data()
        
        # Przełączanie MAC adresu
        current_mac_index, state['prev_mac'] = switch_mac_address(
            current_mac_index, btn_data, state['prev_btn_data'], esp
        )
        state['prev_btn_data']['sw2'] = btn_data.get('sw2')
        
        # Wybór ekranu
        new_screen = get_screen_mode(pot_data.get('pot2', 0))
        if new_screen != state['current_screen']:
            state['current_screen'] = new_screen
            state['prev_values'].clear()
            
            if state['current_screen'] == MODE_MAIN:
                draw_main_screen(tft)
                state['prev_mac'] = None  # Odśwież MAC przy powrocie
            elif state['current_screen'] == MODE_SCREEN2:
                draw_actions_screen(tft, 'screen2')
            else:  # MODE_SCREEN3
                draw_actions_screen(tft, 'screen3')
        
        # Aktualizacja UI dla głównego ekranu
        if state['current_screen'] == MODE_MAIN:
            update_joystick_display(tft, joy_data, state['prev_values'])
            update_potentiometer_display(tft, pot_data.get('pot1', 0), state['prev_values'])
            update_buttons_display(tft, btn_data, state['prev_values'])
            update_switches_display(tft, btn_data, state['prev_values'])
            
            current_mac = RECEIVER_MACS[current_mac_index]
            state['prev_mac'] = update_mac_display(tft, current_mac, state['prev_mac'])
        
        # Komunikacja
        btn_mask = create_button_mask(btn_data)
        data_packet = create_data_packet(
            joy_data, pot_data.get('pot1', 0), state['current_screen'], btn_mask
        )
        
        if send_data(esp, RECEIVER_MACS[current_mac_index], data_packet):
            state['tx_count'] += 1
        
        # Sprawdzenie warunku wyjścia
        state['exit_timer'], should_exit = check_exit_condition(btn_data, state['exit_timer'])
        if should_exit:
            break
        
        time.sleep_ms(UPDATE_RATE_MS)
    
    # Sprzątanie
    cleanup(tft, esp, sta)
