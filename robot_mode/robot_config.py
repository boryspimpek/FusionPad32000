# robot_config.py - Configuration constants for robot controller
import ST7735 # type: ignore
import ujson
import os

def load_config():
    """Load robot configuration from JSON file with fallback to hardcoded values"""
    try:
        # Try to open the file directly with absolute path
        try:
            with open('/robot_config.json', 'r') as f:
                config = ujson.load(f)
                # Convert string MACs back to bytes and build ROBOT_NAMES
                robot_names = {}
                for mac_str, name in config.get('robots', {}).items():
                    # Convert hex string back to bytes
                    mac_bytes = bytes.fromhex(mac_str)
                    robot_names[mac_bytes] = name
                print(f"Loaded config from JSON: {robot_names}")  # Debug
                return robot_names
        except OSError:
            # Try relative path as fallback
            with open('../robot_config.json', 'r') as f:
                config = ujson.load(f)
                # Convert string MACs back to bytes and build ROBOT_NAMES
                robot_names = {}
                for mac_str, name in config.get('robots', {}).items():
                    # Convert hex string back to bytes
                    mac_bytes = bytes.fromhex(mac_str)
                    robot_names[mac_bytes] = name
                print(f"Loaded config from JSON (relative): {robot_names}")  # Debug
                return robot_names
    except Exception as e:
        print(f"Load error: {e}")  # Debug
        pass
    
    # Fallback to hardcoded values
    print("Using hardcoded config")  # Debug
    return {
        b'\x5c\x01\x3b\x6c\x1c\x48': "OTTO NINJA",
        b'\x98\x88\xe0\xd1\x82\x3c': "FALLOUT OTTO"
    }

def save_config(robot_names):
    """Save robot configuration to JSON file"""
    try:
        # Convert bytes MACs to hex strings for JSON serialization
        config_robots = {}
        for mac_bytes, name in robot_names.items():
            mac_str = mac_bytes.hex()
            config_robots[mac_str] = name
        
        config = {'robots': config_robots}
        # Use absolute path to ensure we save to the correct location
        with open('../robot_config.json', 'w') as f:
            ujson.dump(config, f)
        return True
    except Exception as e:
        print(f"Save error: {e}")  # Debug
        return False

# === FONT CONFIGURATION ===
FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": None}  # Will be set from glcdfont

# === RECEIVER MAC ADDRESSES ===
RECEIVER_MACS = [
    b'\x5c\x01\x3b\x6c\x1c\x48',  # OTTO NINJA
    b'\x98\x88\xe0\xd1\x82\x3c'   # FALLOUT OTTO
]

# === ROBOT NAMES ===
def get_robot_names():
    """Get current robot names from JSON or fallback"""
    return load_config()

# Keep ROBOT_NAMES for backward compatibility but make it dynamic
ROBOT_NAMES = get_robot_names()

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
        'left': ["Forward", "Back", "Wave", "Tilt"],
        'right': ["Forward", "Back", "Arms", "Steps"]
    },
    'screen3': {
        'title': "ACTIONS 2", 
        'left': ["Circles", "Steps", "Steps", "Toes"],
        'right': ["Spin", "Boogie", "Balerina", "Weird"]
    }
}

# === SERVO CONFIGURATION ===
SERVO_NAMES = ["RF Right Foot: ", "RL Right Leg: ", "RA Right Arm: ", 
               "LF Left Foot: ", "LL Left Leg: ", "LA Left Arm: "]

# === COMMUNICATION ===
PACKET_FORMAT = '4bBBH'
UPDATE_RATE_MS = 5 
EXIT_HOLD_TIME_MS = 2000
