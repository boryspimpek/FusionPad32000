# mode_gamepad.py
import time
import struct
import bluetooth
from micropython import const
import joystick
import buttons
import ST7735  # type: ignore
import glcdfont

# --- HID REPORT DESCRIPTOR (ANDROID / GAMEPAD TESTER FRIENDLY) ---
# 16 buttons
# 2 analog sticks (X, Y, Rx, Ry)
# 2 analog triggers (L2 = Accelerator, R2 = Brake)

HID_REPORT_DESCRIPTOR = bytes([
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x05,        # Usage (Game Pad)
    0xA1, 0x01,        # Collection (Application)

    # --- Buttons (16) ---
    0x05, 0x09,        # Usage Page (Button)
    0x19, 0x01,        # Usage Minimum (Button 1)
    0x29, 0x10,        # Usage Maximum (Button 16)
    0x15, 0x00,        # Logical Minimum (0)
    0x25, 0x01,        # Logical Maximum (1)
    0x75, 0x01,        # Report Size (1)
    0x95, 0x10,        # Report Count (16)
    0x81, 0x02,        # Input (Data,Var,Abs)

    # --- Analog Sticks ---
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x30,  # X  (Left stick X)
    0x09, 0x31,  # Y  (Left stick Y)
    0x09, 0x32,  # Z  (Right stick X)
    0x09, 0x35,  # Rz (Right stick Y)    0x15, 0x00,        # Logical Minimum (0)
    0x26, 0xFF, 0x00,  # Logical Maximum (255)
    0x75, 0x08,        # Report Size (8)
    0x95, 0x04,        # Report Count (4)
    0x81, 0x02,        # Input (Data,Var,Abs)

    # --- Triggers (L2 / R2) ---
    0x05, 0x02,        # Usage Page (Simulation Controls)
    0x09, 0xC4,        # Usage (Accelerator) -> L2
    0x09, 0xC5,        # Usage (Brake)       -> R2
    0x15, 0x00,        # Logical Minimum (0)
    0x26, 0xFF, 0x00,  # Logical Maximum (255)
    0x75, 0x08,        # Report Size (8)
    0x95, 0x02,        # Report Count (2)
    0x81, 0x02,        # Input (Data,Var,Abs)

    0xC0               # End Collection
])

FONT = {
    "Width": 5,
    "Height": 7,
    "Start": 32,
    "End": 122,
    "Data": glcdfont.font
}

# ------------------------------------------------------------------

class BLE_HID:
    def __init__(self, name="ESP32 Gamepad", on_state_change=None):
        self.name = name
        self.on_state_change = on_state_change
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)
        self.connected = False
        self.conn_handle = None

        # UUIDs
        self.HID_SERVICE = bluetooth.UUID(0x1812)
        self.HID_REPORT = (bluetooth.UUID(0x2A4D), bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY),
        self.HID_MAP = (bluetooth.UUID(0x2A4B), bluetooth.FLAG_READ),
        self.HID_INFO = (bluetooth.UUID(0x2A4A), bluetooth.FLAG_READ),
        self.HID_CTRL = (bluetooth.UUID(0x2A4C), bluetooth.FLAG_WRITE_NO_RESPONSE),

        services = (
            (self.HID_SERVICE,
             self.HID_INFO + self.HID_MAP + self.HID_REPORT + self.HID_CTRL),
        )

        ((self.h_info, self.h_map, self.h_rep, self.h_ctrl),) = \
            self.ble.gatts_register_services(services)

        # HID Information
        self.ble.gatts_write(self.h_info, struct.pack('<HBB', 0x0111, 0x00, 0x03))
        self.ble.gatts_write(self.h_map, HID_REPORT_DESCRIPTOR)

        self._advertise()

    def _advertise(self):
        adv = (
            bytearray(b'\x02\x01\x06') +
            bytearray([len(self.name) + 1, 0x09]) +
            self.name.encode()
        )
        self.ble.gap_advertise(
            100_000,
            adv_data=adv,
            resp_data=bytearray(b'\x03\x19\xC1\x03')
        )

    def _irq(self, event, data):
        if event == 1:  # CONNECT
            self.conn_handle, _, _ = data
            self.connected = True
            if self.on_state_change:
                self.on_state_change(True)

        elif event == 2:  # DISCONNECT
            self.connected = False
            if self.on_state_change:
                self.on_state_change(False)
            self._advertise()

    def send_report(self, buttons_state, axes):
        if not self.connected:
            return
        try:
            self.ble.gatts_notify(
                self.conn_handle,
                self.h_rep,
                struct.pack('<H6B', buttons_state, *axes)
            )
        except:
            pass


# --- Helpers -------------------------------------------------------

def map_axis(val):
    """Mapowanie z [-100, 100] na [0, 255]"""
    return max(0, min(255, int((val + 100) * 1.275)))


# --- MAIN ----------------------------------------------------------

def run(tft):

    def update_screen(is_connected):
        tft.fill(ST7735.TFT.BLACK)
        tft.rect((5, 5), (150, 25), ST7735.TFT.CYAN)
        tft.text((35, 13), "GAMEPAD MODE", ST7735.TFT.CYAN, FONT, 1)

        status_txt = "STATUS: CONNECTED" if is_connected else "STATUS: WAITING..."
        status_clr = ST7735.TFT.GREEN if is_connected else ST7735.TFT.YELLOW
        tft.text((20, 60), status_txt, status_clr, FONT, 1)
        tft.text((20, 110), "HOLD SW4 TO EXIT", ST7735.TFT.RED, FONT, 1)

    update_screen(False)
    hid = BLE_HID("ESP32 Gamepad", on_state_change=update_screen)

    BUTTON_MAP = {
        'bt1': 0, 'bt2': 1, 'bt3': 2, 'bt4': 3,
        'bt5': 4, 'bt6': 5, 'bt7': 6, 'bt8': 7,
        'sw1': 8, 'sw2': 9, 'sw3': 10
    }

    print("Gamepad mode active")

    while True:
        btn_data = buttons.get_data()

        # Exit
        if btn_data.get('sw4', False):
            hid.ble.active(False)
            tft.fill(ST7735.TFT.BLACK)
            return

        if hid.connected:
            joy = joystick.get_data()  # [-100..100]
            pots = joystick.get_potentiometers()  # 0..100

            # Buttons
            b_state = 0
            for name, bit in BUTTON_MAP.items():
                if btn_data.get(name, False):
                    b_state |= (1 << bit)

            # Axes order MUST match descriptor
            axes = [
                map_axis(joy[0]),            # X
                map_axis(-joy[1]),           # Y
                map_axis(joy[2]),            # Rx
                map_axis(-joy[3]),           # Ry
                int(pots['pot1'] * 2.55),    # L2 -> Accelerator
                int(pots['pot2'] * 2.55),    # R2 -> Brake
            ]

            hid.send_report(b_state, axes)

        time.sleep_ms(10)
