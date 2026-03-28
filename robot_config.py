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
# Now loaded dynamically from JSON config file
# Hardcoded values used as fallback
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
# Now loaded dynamically from JSON config file
# Hardcoded values used as fallback
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
    """Load complete robot configuration from JSON file with fallback to hardcoded values"""
    try:
        # Try to open file directly with absolute path
        try:
            with open('/robot_config.json', 'r') as f:
                config = ujson.load(f)
                return _parse_config(config)
        except OSError:
            # Try relative path as fallback
            with open('../robot_config.json', 'r') as f:
                config = ujson.load(f)
                return _parse_config(config)
    except Exception as e:
        print(f"Load error: {e}")  # Debug
        pass
    
    # Fallback to hardcoded values
    print("Using hardcoded config")  # Debug
    return _get_hardcoded_config()

def _parse_config(config):
    """Parse configuration from JSON and return complete data structure"""
    robot_names = {}
    robot_macs = []
    robot_actions = {}
    servo_names = {}
    
    if 'robots' in config:
        for mac_str, robot_data in config['robots'].items():
            mac_bytes = bytes.fromhex(mac_str)
            
            # Basic robot info
            if isinstance(robot_data, dict):
                robot_name = robot_data.get('name', f'Robot_{mac_str}')
                robot_names[mac_bytes] = robot_name
                robot_macs.append(mac_bytes)
                
                # Robot-specific actions
                if 'robot_actions' in robot_data:
                    robot_actions[mac_bytes] = robot_data['robot_actions']
                
                # Robot-specific servo names
                if 'servo_names' in robot_data:
                    servo_names[mac_bytes] = robot_data['servo_names']
            
            print(f"Loaded robot: {mac_str} -> {robot_names[mac_bytes]}")  # Debug
    
    # Update RECEIVER_MACS dynamically
    if robot_macs:
        global RECEIVER_MACS
        RECEIVER_MACS = robot_macs
    
    print(f"Loaded complete config from JSON")  # Debug
    return {
        'robot_names': robot_names,
        'robot_macs': robot_macs,
        'robot_actions': robot_actions,
        'servo_names': servo_names
    }

def _get_hardcoded_config():
    """Get hardcoded configuration as fallback"""
    robot_names = {
        b'\x5c\x01\x3b\x6c\x1c\x48': "OTTO NINJA",
        b'\x98\x88\xe0\xd1\x82\x3c': "FALLOUT OTTO"
    }
    robot_macs = [b'\x5c\x01\x3b\x6c\x1c\x48', b'\x98\x88\xe0\xd1\x82\x3c']
    
    # Use hardcoded actions and servo names
    robot_actions = {}
    servo_names = {}
    
    for mac in robot_macs:
        robot_actions[mac] = ROBOT_ACTIONS
        servo_names[mac] = SERVO_NAMES
    
    # Update RECEIVER_MACS
    global RECEIVER_MACS
    RECEIVER_MACS = robot_macs
    
    return {
        'robot_names': robot_names,
        'robot_macs': robot_macs,
        'robot_actions': robot_actions,
        'servo_names': servo_names
    }
