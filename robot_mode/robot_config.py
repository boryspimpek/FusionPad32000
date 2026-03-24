# robot_config.py - Configuration constants for robot controller
import ST7735 # type: ignore
import ujson
import os

# === FONT CONFIGURATION ===
FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": None}  # Will be set from glcdfont

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
                return robot_names
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

def save_config_fixed(robot_names, robots_data=None):
    """Save robot configuration to JSON file with correct path and MAC addresses"""
    try:
        import ujson
        import os
        
        print(f"save_config_fixed called with: {robot_names}")  # Debug
        
        # Convert bytes MACs to hex strings for JSON serialization
        config_robots = {}
        robot_macs = []
        
        for mac_bytes, name in robot_names.items():
            mac_str = mac_bytes.hex()
            # Use the MAC address from the POST data, not reformatted
            # Look for the MAC in the original robots_data
            original_mac = ':'.join([mac_str[i:i+2] for i in range(0, len(mac_str), 2)])
            if robots_data:
                for mac_key, robot_info in robots_data.items():
                    if mac_key == mac_str:
                        original_mac = robot_info.get('mac', original_mac)
                        break
            
            config_robots[mac_str] = {
                "name": name,
                "mac": original_mac
            }
            robot_macs.append(mac_bytes)
        
        config = {'robots': config_robots}
        
        print(f"About to write config: {config}")  # Debug
        
        # Use correct path - mode_config.py is in root directory
        with open('robot_config.json', 'w') as f:
            ujson.dump(config, f)
            print("File written successfully")  # Debug
        
        # Verify file was written
        with open('robot_config.json', 'r') as f:
            content = f.read()
            print(f"File content after save: {content}")  # Debug
        
        return True
    except Exception as e:
        print(f"Save error details: {e}")  # Debug
        import sys
        print(f"Error type: {type(e)}")
        return False
