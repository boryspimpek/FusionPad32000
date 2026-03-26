# mode_config.py - WiFi Configuration Mode with Web Interface (Refactored)
import time
import machine # type: ignore
import buttons
import ST7735 # type: ignore
import glcdfont
from robot_mode.robot_config import load_config
from robot_mode.web_config import setup_wifi_ap, cleanup_wifi, get_connection_info, setup_server_socket, check_client_connections

# Font configuration
FONT = {"Width": 5, "Height": 7, "Start": 32, "End": 122, "Data": glcdfont.font}

# Colors
BLACK = ST7735.TFT.BLACK
WHITE = ST7735.TFT.WHITE
CYAN = ST7735.TFT.CYAN
GREEN = ST7735.TFT.GREEN
RED = ST7735.TFT.RED

def center_x(text, screen_w=160, char_w=6):
    return (screen_w - len(text) * char_w) // 2

def display_connection_info(tft, ip):
    """Display WiFi connection information on TFT"""
    tft.fill(BLACK)
    tft.text((center_x("CONFIG MODE"), 10), "CONFIG MODE", CYAN, FONT, 1)
    tft.text((center_x("WiFi: FusionPad-Config"), 30), "WiFi: FusionPad-Config", WHITE, FONT, 1)
    tft.text((center_x(f"IP: {ip}"), 50), f"IP: {ip}", WHITE, FONT, 1)
    tft.text((center_x("Connect to configure"), 70), "Connect to configure", GREEN, FONT, 1)
    tft.text((center_x("Press sw1 to exit"), 90), "Press sw1 to exit", RED, FONT, 1)

def run(tft):
    """Run configuration mode with WiFi AP and web server"""
    # Initialize WiFi AP
    ap, ip = setup_wifi_ap()
    conn_info = get_connection_info(ip)
    
    # Load current configuration
    config = {'robots': {}}
    try:
        robot_names, robot_macs = load_config()
        for mac_bytes, name in robot_names.items():
            mac_hex = mac_bytes.hex()
            # Format MAC address with colons for display
            mac_display = ':'.join([mac_hex[i:i+2] for i in range(0, len(mac_hex), 2)])
            config['robots'][mac_hex] = {
                'name': name,
                'mac': mac_display
            }
    except:
        pass
    
    # Setup server socket
    server_socket = setup_server_socket()
    
    # Display connection info
    display_connection_info(tft, ip)
    print(conn_info['message'])
    
    last_client_check = time.ticks_ms()
    
    while True:
        # Check for exit button
        btns = buttons.get_data()
        if btns['sw1']:
            # Wait for button release
            while buttons.get_data()['sw1']:
                time.sleep(0.01)
            break
        
        # Check for client connections (non-blocking)
        last_client_check = check_client_connections(server_socket, config, last_client_check)
        
        time.sleep(0.01)
    
    # Cleanup
    try:
        server_socket.close()
    except:
        pass
    
    cleanup_wifi(ap)
    tft.fill(BLACK)
    tft.text((center_x("Exiting Config"), 40), "Exiting Config", WHITE, FONT, 1)
    time.sleep(1)
