# robot_communication.py - ESP-NOW communication for robot controller
import network # type: ignore
import espnow # type: ignore
import struct
import robot_config

# Module-level state for communication
_sta = None
_esp = None
_current_mac_index = 0
_receiver_macs = []

def init_communication():
    """Initialize communication module"""
    global _sta, _esp, _current_mac_index, _receiver_macs
    _sta = None
    _esp = None
    _current_mac_index = 0
    _receiver_macs = []

def initialize_network():
    """Initialize WiFi network and ESP-NOW"""
    global _sta, _esp, _receiver_macs
    # Load configuration to get MAC addresses
    robot_names, robot_macs = robot_config.load_config()
    _receiver_macs = robot_macs
    
    _sta = network.WLAN(network.STA_IF)
    _sta.active(True)
    
    _esp = espnow.ESPNow()
    _esp.active(True)
    
    return _sta, _esp

def add_peer(mac_address):
    """Add peer to ESP-NOW"""
    global _esp
    try:
        _esp.add_peer(mac_address)
        return True
    except OSError:
        return False

def set_current_mac_index(index):
    """Set current MAC address index"""
    global _current_mac_index, _receiver_macs
    if not _receiver_macs:
        print("Warning: No receiver MAC addresses configured")
        return False
    
    _current_mac_index = index
    return add_peer(_receiver_macs[index])

def get_current_mac():
    """Get current MAC address"""
    global _current_mac_index, _receiver_macs
    if not _receiver_macs:
        return None
    return _receiver_macs[_current_mac_index]

def get_current_mac_index():
    """Get current MAC address index"""
    global _current_mac_index
    return _current_mac_index

def switch_mac_address(btn_data, prev_btn_data):
    """Switch MAC address when SW2 is pressed (but not when SW1 is pressed)"""
    global _current_mac_index, _receiver_macs
    if not _receiver_macs:
        return _current_mac_index
        
    if btn_data.get('sw2') and not prev_btn_data.get('sw2', False) and not btn_data.get('sw1'):
        new_index = (_current_mac_index + 1) % len(_receiver_macs)
        set_current_mac_index(new_index)
        return new_index  # Return new index
    return _current_mac_index  # Return current index

def create_data_packet(joy_data, pot_value, screen_mode, btn_mask):
    """Create data packet to send"""
    return struct.pack(
        'B4bBBH',  # Add Header ID (0x01)
        1,  # CONTROL packet ID
        joy_data[0], joy_data[1], joy_data[2], joy_data[3],
        pot_value,
        screen_mode & 0xFF,
        btn_mask
    )

def create_trim_packet(servo_trims):
    """Create trim synchronization packet"""
    return struct.pack('B6b', 2, *servo_trims)  # TRIM_SYNC packet ID (0x02)

def create_save_packet():
    """Create save configuration packet"""
    return struct.pack('BB', 3, 1)  # SAVE packet ID (0x03)

def create_button_mask(btn_data):
    """Create button bit mask"""
    btn_mask = 0
    
    # Buttons BT1-BT8
    for i in range(8):
        if btn_data.get(f'bt{i+1}'):
            btn_mask |= (1 << i)
    
    # Switches SW3, SW4
    if btn_data.get('sw3'):
        btn_mask |= (1 << 8)
    if btn_data.get('sw4'):
        btn_mask |= (1 << 9)
    
    return btn_mask

def send_data(data_packet):
    """Send data packet via ESP-NOW"""
    global _esp
    try:
        _esp.send(get_current_mac(), data_packet, False)
        return True
    except OSError:
        return False

def send_control_data(joy_data, pot_value, screen_mode, btn_data):
    """Send control data packet"""
    btn_mask = create_button_mask(btn_data)
    data_packet = create_data_packet(joy_data, pot_value, screen_mode, btn_mask)
    return send_data(data_packet)

def send_trim_data(servo_trims):
    """Send trim data packet"""
    data_packet = create_trim_packet(servo_trims)
    return send_data(data_packet)

def send_save_data():
    """Send save configuration packet"""
    data_packet = create_save_packet()
    return send_data(data_packet)

def cleanup():
    """Clean up network resources"""
    global _esp, _sta
    if _esp:
        _esp.active(False)
    if _sta:
        _sta.active(False)
