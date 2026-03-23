# robot_config.py - Configuration constants for robot controller
import ST7735 # type: ignore

# === FONT CONFIGURATION ===
FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": None}  # Will be set from glcdfont

# === RECEIVER MAC ADDRESSES ===
RECEIVER_MACS = [
    b'\x5c\x01\x3b\x6c\x1c\x48',  # OTTO NINJA
    b'\x98\x88\xe0\xd1\x82\x3c'   # FALLOUT OTTO
]

# === ROBOT NAMES ===
ROBOT_NAMES = {
    b'\x5c\x01\x3b\x6c\x1c\x48': "OTTO NINJA",
    b'\x98\x88\xe0\xd1\x82\x3c': "FALLOUT OTTO"
}

# === COLORS ===
BLACK  = ST7735.TFT.BLACK
WHITE  = ST7735.TFT.WHITE
CYAN   = 0x07FF
YELLOW = 0xFFE0
GREEN  = 0x07E0
RED    = 0xF800
GRAY   = 0x4208

# === SCREEN MODES ===
MODE_MAIN    = 0  # ekran z joystickami
MODE_SCREEN2 = 1  # pierwszy ekran akcji
MODE_SCREEN3 = 2  # drugi ekran akcji
MODE_TRIM    = 3  # ekran trimowania serw

# === ROBOT ACTIONS CONFIGURATION ===
ROBOT_ACTIONS = {
    'screen2': {
        'title': "ACTIONS 1",
        'left': [" Forward L1", "    Back L2", "    Wave L3", "    Tilt L4"],
        'right': ["R1 Forward", "R2 Back", "R3 Arms", "R4 Steps"]
    },
    'screen3': {
        'title': "ACTIONS 2", 
        'left': [" Circles L1", "   Steps L2", "   Steps L3", "    Toes L4"],
        'right': ["R1 Spin", "R2 Boogie", "R3 Balerina", "R4 Weird"]
    }
}

# === SERVO CONFIGURATION ===
SERVO_NAMES = ["RF Right Foot: ", "RL Right Leg: ", "RA Right Arm: ", 
               "LF Left Foot: ", "LL Left Leg: ", "LA Left Arm: "]

# === COMMUNICATION ===
PACKET_FORMAT = '4bBBH'
UPDATE_RATE_MS = 5 
EXIT_HOLD_TIME_MS = 2000
