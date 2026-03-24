# wifi_manager.py - WiFi Access Point management for configuration mode
import network
import time

def setup_wifi_ap():
    """Initialize WiFi Access Point for configuration"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='FusionPad-Config', password='')
    
    # Get IP address
    ip = ap.ifconfig()[0]
    
    return ap, ip

def cleanup_wifi(ap):
    """Clean up WiFi connection"""
    try:
        ap.active(False)
    except:
        pass

def get_connection_info(ip):
    """Get formatted connection information for display"""
    return {
        'ssid': 'FusionPad-Config',
        'ip': ip,
        'message': f"Connect to WiFi: FusionPad-Config, IP: {ip}"
    }
    
def is_wifi_active(ap):
    """Check if WiFi AP is still active"""
    try:
        return ap.active()
    except:
        return False
