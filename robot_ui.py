# robot_ui.py - UI Management for robot controller
from glcdfont import FONT
import robot_config
import ST7735

def init_ui():
    """Initialize UI module - font is already initialized at module level"""
    pass
    
def pad(val, width=4):
    """Pad number with spaces for alignment"""
    s = str(val)
    return ' ' * (width - len(s)) + s
    
def mac_to_str(mac):
    """Convert MAC address to readable string"""
    return ':'.join('%02x' % b for b in mac)
    
def center_x(text, screen_w=160, char_w=6):
    """Calculate centered x position for text"""
    return (screen_w - len(text) * char_w) // 2
    
def draw_header(tft, title):
    """Draw screen header"""
    tft.rect((5, 5), (150, 25), ST7735.TFT.CYAN)
    tft.text((center_x(title), 13), title, ST7735.TFT.YELLOW, FONT, 1)
    
def draw_main_screen(tft):
    """Draw main screen with joysticks"""
    tft.fill(ST7735.TFT.BLACK)
    draw_header(tft, "OTTO GAMEPAD")
    
    row_height = 12
    tft.text((10, 40 +  0), "J1X:", ST7735.TFT.CYAN,   FONT, 1)
    tft.text((90, 40 +  0), "J2X:", ST7735.TFT.CYAN,   FONT, 1)
    tft.text((10, 40 + row_height), "J1Y:", ST7735.TFT.CYAN,   FONT, 1)
    tft.text((90, 40 + row_height), "J2Y:", ST7735.TFT.CYAN,   FONT, 1)
    tft.text((10, 40 + 2 * row_height), "POT:", ST7735.TFT.CYAN,   FONT, 1)
    tft.text((10, 40 + 3 * row_height), "BT:",  ST7735.TFT.CYAN,  FONT, 1)
    tft.text((10, 40 + 4 * row_height), "SW:",  ST7735.TFT.CYAN,  FONT, 1)
    tft.text((10, 40 + 5 * row_height), "ROBOT:", ST7735.TFT.CYAN,    FONT, 1)
    tft.text((center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", ST7735.TFT.RED, FONT, 1)
    
def draw_actions_screen(tft, screen_key, current_mac=None):
    """Draw robot actions screen with automatic alignment"""
    tft.fill(ST7735.TFT.BLACK)
    
    # Load configuration to get robot-specific actions
    config = robot_config.load_config()
    robot_actions = config['robot_actions']
    
    # Get actions for current robot or fallback to default
    if current_mac and current_mac in robot_actions:
        actions = robot_actions[current_mac][screen_key]
    else:
        # Fallback to hardcoded actions
        actions = robot_config.ROBOT_ACTIONS[screen_key]
    
    # Create dynamic title based on current robot
    if current_mac:
        robot_names = config['robot_names']
        robot_name = robot_names.get(current_mac, "UNKNOWN ROBOT")
        # Extract action number from original title (e.g., ACTIONS 1" -> "1")
        action_number = actions['title'].split()[-1]
        dynamic_title = f"{robot_name} ACTIONS {action_number}"
    else:
        dynamic_title = actions['title']
    
    draw_header(tft, dynamic_title)
    
    # Calculate positions for symmetrical layout
    char_width = 6
    center_x_pos = 80
    
    # L1-L4 positions (left side, centered)
    l_positions = []
    for i in range(4):
        label = f"L{i+1}"
        x = center_x_pos - 15 - len(label) * char_width // 2
        l_positions.append((x, label))
    
    # R1-R4 positions (right side, centered)
    r_positions = []
    for i in range(4):
        label = f"R{i+1}"
        x = center_x_pos + 15 - len(label) * char_width // 2
        r_positions.append((x, label))
    
    # Draw actions with proper alignment
    for i in range(4):
        y = 50 + i * 12
        
        # Left description (right-aligned to L1-L4)
        left_desc = actions['left'][i]
        l_x, l_label = l_positions[i]
        desc_x = l_x - len(left_desc) * char_width - 2  # 2px gap
        tft.text((desc_x, y), left_desc, ST7735.TFT.CYAN, FONT, 1)
        
        # L1-L4 labels (white)
        tft.text((l_x, y), l_label, ST7735.TFT.WHITE, FONT, 1)
        
        # R1-R4 labels (white)
        r_x, r_label = r_positions[i]
        tft.text((r_x, y), r_label, ST7735.TFT.WHITE, FONT, 1)
        
        # Right description (left-aligned to R1-R4)
        right_desc = actions['right'][i]
        desc_x = r_x + len(r_label) * char_width + 2  # 2px gap
        tft.text((desc_x, y), right_desc, ST7735.TFT.YELLOW, FONT, 1)
    
    tft.text((center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", ST7735.TFT.RED, FONT, 1)
    
def draw_servo_list(tft, servo_trims, selected_servo_index=None, show_cursor=False, current_mac=None):
    """Draw servo list with trim values"""
    
    # Draw vertical separator line
    tft.vline((18, 36), 6 * 12, ST7735.TFT.GRAY)
    
    # List of servos with their trim values
    config = robot_config.load_config()
    servo_names = config['servo_names']
    
    # Get servo names for current robot or fallback to default
    if current_mac and current_mac in servo_names:
        robot_servo_names = servo_names[current_mac]
    else:
        # Fallback to hardcoded servo names
        robot_servo_names = robot_config.SERVO_NAMES
    
    for i in range(6):
        y = 36 + i * 12
        servo_name = robot_servo_names[i]
        trim_value = servo_trims[i]
        
        # Cursor (only in update mode)
        if show_cursor:
            if i == selected_servo_index:
                tft.text((10, y), ">", ST7735.TFT.CYAN, FONT, 1)
            else:
                tft.text((10, y), " ", ST7735.TFT.BLACK, FONT, 1)
        
        # Servo name
        tft.text((25, y), servo_name, ST7735.TFT.WHITE, FONT, 1)
        
        # Trim value
        trim_str = str(trim_value)
        if trim_value >= 0:
            trim_str = "+" + trim_str
        tft.text((136, y), trim_str, ST7735.TFT.YELLOW, FONT, 1)
    
def draw_trim_screen(tft, current_mac=None):
    """Draw static trim screen interface (called once)"""
    tft.fill(ST7735.TFT.BLACK)
    draw_header(tft, "SERVO TRIM")

    # Draw vertical separator line
    tft.vline((18, 36), 6 * 12, ST7735.TFT.GRAY)

    # Draw servo names once at the beginning
    config = robot_config.load_config()
    servo_names = config['servo_names']
    
    # Get servo names for current robot or fallback to default
    if current_mac and current_mac in servo_names:
        robot_servo_names = servo_names[current_mac]
    else:
        # Fallback to hardcoded servo names
        robot_servo_names = robot_config.SERVO_NAMES
    
    for i in range(6):
        y = 36 + i * 12
        tft.text((25, y), robot_servo_names[i], ST7735.TFT.WHITE, FONT, 1)
    
    # Instructions at the bottom
    tft.text((center_x("POT1: SELECT"), 110), "POT1: SELECT", ST7735.TFT.GREEN, FONT, 1)
    tft.text((center_x("BT8: SAVE   BT1: +1 BT2: -1"), 122), "BT8: SAVE   BT1: +1 BT2: -1", ST7735.TFT.GREEN, FONT, 1)
    
def update_joystick_display(tft, joy_data, prev_values):
    """Update joystick values display"""
    vals = {
        'j1x': (joy_data[0], 36, 40),
        'j1y': (joy_data[1], 36, 52),
        'j2x': (joy_data[2], 116, 40),
        'j2y': (joy_data[3], 116, 52),
    }
    
    for key, (value, x, y) in vals.items():
        if prev_values.get(key) != value:
            tft.fillrect((x, y), (30, 8), ST7735.TFT.BLACK)
            tft.text((x, y), pad(value), ST7735.TFT.YELLOW, FONT, 1)
            prev_values[key] = value
    
def update_potentiometer_display(tft, pot_value, prev_values):
    """Update potentiometer display"""
    if prev_values.get('pot') != pot_value:
        tft.fillrect((36, 64), (30, 8), ST7735.TFT.BLACK)
        tft.text((36, 64), pad(pot_value), ST7735.TFT.YELLOW, FONT, 1)
        prev_values['pot'] = pot_value
    
def update_buttons_display(tft, btn_data, prev_values):
    """Update buttons BT1-BT8 display"""
    bt_changed = any(
        prev_values.get(f'bt{i+1}') != bool(btn_data.get(f'bt{i+1}'))
        for i in range(8)
    )
    
    if bt_changed:
        x_bt = 10 + 20
        tft.fillrect((x_bt, 76), (160 - x_bt, 8), ST7735.TFT.BLACK)
        x = x_bt
        for i in range(8):
            pressed = bool(btn_data.get(f'bt{i+1}'))
            color = ST7735.TFT.GREEN if pressed else ST7735.TFT.GRAY
            tft.text((x, 76), str(i + 1), color, FONT, 1)
            prev_values[f'bt{i+1}'] = pressed
            x += 16
    
def update_switches_display(tft, btn_data, prev_values):
    """Update switches SW1-SW4 display"""
    sw_changed = any(
        prev_values.get(sw) != bool(btn_data.get(sw))
        for sw in ['sw1', 'sw2', 'sw3', 'sw4']
    )
    
    if sw_changed:
        x_sw = 10 + 20
        tft.fillrect((x_sw, 88), (160 - x_sw, 8), ST7735.TFT.BLACK)
        x = x_sw
        for sw in ['sw1', 'sw2', 'sw3', 'sw4']:
            pressed = bool(btn_data.get(sw))
            color = ST7735.TFT.GREEN if pressed else ST7735.TFT.GRAY
            tft.text((x, 88), sw.upper(), color, FONT, 1)
            prev_values[sw] = pressed
            x += 34
    
def update_mac_display(tft, mac_address, prev_mac):
    """Update robot name display"""
    if prev_mac != mac_address:
        tft.fillrect((40, 100), (120, 8), ST7735.TFT.BLACK)
        config = robot_config.load_config()
        robot_names = config['robot_names']
        robot_name = robot_names.get(mac_address, "UNKNOWN")
        tft.text((48, 100), robot_name, ST7735.TFT.YELLOW, FONT, 1)
        return mac_address
    return prev_mac
    
def update_trim_display(tft, servo_trims, selected_servo_index, prev_values, force_refresh=False, current_mac=None):
    """Update only cursor and numeric values"""
    
    # Check if robot changed and update servo names if needed
    if current_mac and prev_values.get('last_robot_mac') != current_mac:
        config = robot_config.load_config()
        servo_names = config['servo_names']
        
        # Get servo names for current robot or fallback to default
        if current_mac in servo_names:
            robot_servo_names = servo_names[current_mac]
        else:
            robot_servo_names = robot_config.SERVO_NAMES
        
        # Redraw servo names
        for i in range(6):
            y = 36 + i * 12
            tft.fillrect((25, y), (110, 8), ST7735.TFT.BLACK)
            tft.text((25, y), robot_servo_names[i], ST7735.TFT.WHITE, FONT, 1)
        
        prev_values['last_robot_mac'] = current_mac
    
    # 1. Handle cursor (draw only if changed)
    prev_idx = prev_values.get('last_servo_idx', -1)
    if prev_idx != selected_servo_index or force_refresh:
        # Erase old cursor
        if prev_idx != -1:
            old_y = 36 + prev_idx * 12
            tft.text((10, old_y), " ", ST7735.TFT.BLACK, FONT, 1)
        # Draw new one
        new_y = 36 + selected_servo_index * 12
        tft.text((10, new_y), ">", ST7735.TFT.CYAN, FONT, 1)
        prev_values['last_servo_idx'] = selected_servo_index

    # 2. Handle values (loop through all, but fillrect only for changed ones)
    for i in range(6):
        trim_value = servo_trims[i]
        trim_key = f'trim_{i}'
        
        if prev_values.get(trim_key) != trim_value or force_refresh:
            y = 36 + i * 12
            # Clear only the number area (X adjusted to your layout)
            tft.fillrect((136, y), (35, 8), ST7735.TFT.BLACK)
            
            trim_str = f"{'+' if trim_value >= 0 else ''}{trim_value}"
            tft.text((136, y), trim_str, ST7735.TFT.YELLOW, FONT, 1)
            prev_values[trim_key] = trim_value
    
def show_cleanup_message(tft):
    """Show cleanup message before exit"""
    tft.fill(ST7735.TFT.BLACK)
    tft.text((20, 60), "RELEASE BUTTONS...", ST7735.TFT.WHITE, FONT, 1)
