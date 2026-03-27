# robot_config.py - Configuration constants for robot controller
import ST7735 # type: ignore
import ujson
import os

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

# === RECEIVER MAC ADDRESSES ===
# Will be populated from JSON config by load_config()
RECEIVER_MACS = []

def load_config():
    """Load robot configuration from JSON file with fallback to hardcoded values"""
    try:
        # Try to open file directly with absolute path
        try:
            with open('/robot_config.json', 'r') as f:
                config = ujson.load(f)
                # Handle new format with MAC addresses stored separately
                robot_names = {}
                robot_macs = []
                
                if 'robots' in config:
                    for mac_str, robot_data in config['robots'].items():
                        # New format: {"5c013b6c1c48": {"name": "OTTO NINJA", "mac": "5c:01:3b:6c:1c:48"}}
                        if isinstance(robot_data, dict) and 'name' in robot_data:
                            mac_bytes = bytes.fromhex(mac_str)
                            robot_names[mac_bytes] = robot_data['name']
                            robot_macs.append(mac_bytes)
                            print(f"Loaded robot: {mac_str} -> {robot_data['name']}")  # Debug
                        # Old format: {"5c013b6c1c48": "OTTO NINJA"}
                        elif isinstance(robot_data, str):
                            mac_bytes = bytes.fromhex(mac_str)
                            robot_names[mac_bytes] = robot_data
                            robot_macs.append(mac_bytes)
                            print(f"Loaded robot (old format): {mac_str} -> {robot_data}")  # Debug
                
                # Update RECEIVER_MACS dynamically
                if robot_macs:
                    global RECEIVER_MACS
                    RECEIVER_MACS = robot_macs
                
                print(f"Loaded config from JSON: {robot_names}")  # Debug
                return robot_names, robot_macs
        except OSError:
            # Try relative path as fallback
            with open('../robot_config.json', 'r') as f:
                config = ujson.load(f)
                # Same logic as above
                robot_names = {}
                robot_macs = []
                
                if 'robots' in config:
                    for mac_str, robot_data in config['robots'].items():
                        if isinstance(robot_data, dict) and 'name' in robot_data:
                            mac_bytes = bytes.fromhex(mac_str)
                            robot_names[mac_bytes] = robot_data['name']
                            robot_macs.append(mac_bytes)
                            print(f"Loaded robot: {mac_str} -> {robot_data['name']}")  # Debug
                        elif isinstance(robot_data, str):
                            mac_bytes = bytes.fromhex(mac_str)
                            robot_names[mac_bytes] = robot_data
                            robot_macs.append(mac_bytes)
                            print(f"Loaded robot (old format): {mac_str} -> {robot_data}")  # Debug
                
                if robot_macs:
                    global RECEIVER_MACS
                    RECEIVER_MACS = robot_macs
                
                print(f"Loaded config from JSON (relative): {robot_names}")  # Debug
                return robot_names, robot_macs
    except Exception as e:
        print(f"Load error: {e}")  # Debug
        pass
    
    # Fallback to hardcoded values
    print("Using hardcoded config")  # Debug
    robot_names = {
        b'\x5c\x01\x3b\x6c\x1c\x48': "OTTO NINJA",
        b'\x98\x88\xe0\xd1\x82\x3c': "FALLOUT OTTO"
    }
    robot_macs = [b'\x5c\x01\x3b\x6c\x1c\x48', b'\x98\x88\xe0\xd1\x82\x3c']
    return robot_names, robot_macs
