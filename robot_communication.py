# robot_communication.py - ESP-NOW communication for robot controller
import network # type: ignore
import espnow # type: ignore
import struct
import robot_config

class RobotCommunication:
    def __init__(self):
        self.sta = None
        self.esp = None
        self.current_mac_index = 0
        self.receiver_macs = []
    
    def initialize_network(self):
        """Initialize WiFi network and ESP-NOW"""
        # Load configuration to get MAC addresses
        robot_names, robot_macs = robot_config.load_config()
        self.receiver_macs = robot_macs
        
        self.sta = network.WLAN(network.STA_IF)
        self.sta.active(True)
        
        self.esp = espnow.ESPNow()
        self.esp.active(True)
        
        return self.sta, self.esp
    
    def add_peer(self, mac_address):
        """Add peer to ESP-NOW"""
        try:
            self.esp.add_peer(mac_address)
            return True
        except OSError:
            return False
    
    def set_current_mac_index(self, index):
        """Set current MAC address index"""
        if not self.receiver_macs:
            print("Warning: No receiver MAC addresses configured")
            return False
        
        self.current_mac_index = index
        return self.add_peer(self.receiver_macs[index])
    
    def get_current_mac(self):
        """Get current MAC address"""
        if not self.receiver_macs:
            return None
        return self.receiver_macs[self.current_mac_index]
    
    def switch_mac_address(self, btn_data, prev_btn_data):
        """Switch MAC address when SW2 is pressed (but not when SW1 is pressed)"""
        if not self.receiver_macs:
            return self.current_mac_index
            
        if btn_data.get('sw2') and not prev_btn_data.get('sw2', False) and not btn_data.get('sw1'):
            new_index = (self.current_mac_index + 1) % len(self.receiver_macs)
            self.set_current_mac_index(new_index)
            return new_index  # Return new index
        return self.current_mac_index  # Return current index
    
    def create_data_packet(self, joy_data, pot_value, screen_mode, btn_mask):
        """Create data packet to send"""
        return struct.pack(
            'B4bBBH',  # Add Header ID (0x01)
            1,  # CONTROL packet ID
            joy_data[0], joy_data[1], joy_data[2], joy_data[3],
            pot_value,
            screen_mode & 0xFF,
            btn_mask
        )
    
    def create_trim_packet(self, servo_trims):
        """Create trim synchronization packet"""
        return struct.pack('B6b', 2, *servo_trims)  # TRIM_SYNC packet ID (0x02)
    
    def create_save_packet(self):
        """Create save configuration packet"""
        return struct.pack('BB', 3, 1)  # SAVE packet ID (0x03)
    
    def create_button_mask(self, btn_data):
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
    
    def send_data(self, data_packet):
        """Send data packet via ESP-NOW"""
        try:
            self.esp.send(self.get_current_mac(), data_packet, False)
            return True
        except OSError:
            return False
    
    def send_control_data(self, joy_data, pot_value, screen_mode, btn_data):
        """Send control data packet"""
        btn_mask = self.create_button_mask(btn_data)
        data_packet = self.create_data_packet(joy_data, pot_value, screen_mode, btn_mask)
        return self.send_data(data_packet)
    
    def send_trim_data(self, servo_trims):
        """Send trim data packet"""
        data_packet = self.create_trim_packet(servo_trims)
        return self.send_data(data_packet)
    
    def send_save_data(self):
        """Send save configuration packet"""
        data_packet = self.create_save_packet()
        return self.send_data(data_packet)
    
    def cleanup(self):
        """Clean up network resources"""
        if self.esp:
            self.esp.active(False)
        if self.sta:
            self.sta.active(False)
