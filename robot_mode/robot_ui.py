# robot_ui.py - UI Management for robot controller
import glcdfont
from .robot_config import FONT, ROBOT_ACTIONS, SERVO_NAMES, ROBOT_NAMES, BLACK, WHITE, CYAN, YELLOW, GREEN, RED, GRAY

class RobotUI:
    def __init__(self):
        # Initialize font with glcdfont data
        FONT["Data"] = glcdfont.font
    
    def pad(self, val, width=4):
        """Pad number with spaces for alignment"""
        s = str(val)
        return ' ' * (width - len(s)) + s
    
    def mac_to_str(self, mac):
        """Convert MAC address to readable string"""
        return ':'.join('%02x' % b for b in mac)
    
    def center_x(self, text, screen_w=160, char_w=6):
        """Calculate centered x position for text"""
        return (screen_w - len(text) * char_w) // 2
    
    def draw_header(self, tft, title):
        """Draw screen header"""
        tft.rect((5, 5), (150, 25), CYAN)
        tft.text((self.center_x(title), 13), title, YELLOW, FONT, 1)
    
    def draw_main_screen(self, tft):
        """Draw main screen with joysticks"""
        tft.fill(BLACK)
        self.draw_header(tft, "OTTO GAMEPAD")
        
        row_height = 12
        tft.text((10, 40 +  0), "J1X:", CYAN,   FONT, 1)
        tft.text((90, 40 +  0), "J2X:", CYAN,   FONT, 1)
        tft.text((10, 40 + row_height), "J1Y:", CYAN,   FONT, 1)
        tft.text((90, 40 + row_height), "J2Y:", CYAN,   FONT, 1)
        tft.text((10, 40 + 2 * row_height), "POT:", CYAN,   FONT, 1)
        tft.text((10, 40 + 3 * row_height), "BT:",  CYAN,  FONT, 1)
        tft.text((10, 40 + 4 * row_height), "SW:",  CYAN,  FONT, 1)
        tft.text((10, 40 + 5 * row_height), "ROBOT:", CYAN,    FONT, 1)
        tft.text((self.center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", RED, FONT, 1)
    
    def draw_actions_screen(self, tft, screen_key, current_mac=None):
        """Draw robot actions screen with automatic alignment"""
        tft.fill(BLACK)
        actions = ROBOT_ACTIONS[screen_key]
        
        # Create dynamic title based on current robot
        if current_mac:
            robot_name = ROBOT_NAMES.get(current_mac, "UNKNOWN ROBOT")
            # Extract action number from original title (e.g., ACTIONS 1" -> "1")
            action_number = actions['title'].split()[-1]
            dynamic_title = f"{robot_name} ACTIONS {action_number}"
        else:
            dynamic_title = actions['title']
        
        self.draw_header(tft, dynamic_title)
        
        # Calculate positions for symmetrical layout
        char_width = 6
        center_x = 80
        
        # L1-L4 positions (left side, centered)
        l_positions = []
        for i in range(4):
            label = f"L{i+1}"
            x = center_x - 15 - len(label) * char_width // 2
            l_positions.append((x, label))
        
        # R1-R4 positions (right side, centered)
        r_positions = []
        for i in range(4):
            label = f"R{i+1}"
            x = center_x + 15 - len(label) * char_width // 2
            r_positions.append((x, label))
        
        # Draw actions with proper alignment
        for i in range(4):
            y = 50 + i * 12
            
            # Left description (right-aligned to L1-L4)
            left_desc = actions['left'][i]
            l_x, l_label = l_positions[i]
            desc_x = l_x - len(left_desc) * char_width - 2  # 2px gap
            tft.text((desc_x, y), left_desc, CYAN, FONT, 1)
            
            # L1-L4 labels (white)
            tft.text((l_x, y), l_label, WHITE, FONT, 1)
            
            # R1-R4 labels (white)
            r_x, r_label = r_positions[i]
            tft.text((r_x, y), r_label, WHITE, FONT, 1)
            
            # Right description (left-aligned to R1-R4)
            right_desc = actions['right'][i]
            desc_x = r_x + len(r_label) * char_width + 2  # 2px gap
            tft.text((desc_x, y), right_desc, YELLOW, FONT, 1)
        
        tft.text((self.center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", RED, FONT, 1)
    
    def draw_servo_list(self, tft, servo_trims, selected_servo_index=None, show_cursor=False):
        """Draw servo list with trim values"""
        
        # Draw vertical separator line
        tft.vline((18, 36), 6 * 12, GRAY)
        
        # List of servos with their trim values
        for i in range(6):
            y = 36 + i * 12
            servo_name = SERVO_NAMES[i]
            trim_value = servo_trims[i]
            
            # Cursor (only in update mode)
            if show_cursor:
                if i == selected_servo_index:
                    tft.text((10, y), ">", CYAN, FONT, 1)
                else:
                    tft.text((10, y), " ", BLACK, FONT, 1)
            
            # Servo name
            tft.text((25, y), servo_name, WHITE, FONT, 1)
            
            # Trim value
            trim_str = str(trim_value)
            if trim_value >= 0:
                trim_str = "+" + trim_str
            tft.text((136, y), trim_str, YELLOW, FONT, 1)
    
    def draw_trim_screen(self, tft):
        """Draw static trim screen interface (called once)"""
        tft.fill(BLACK)
        self.draw_header(tft, "SERVO TRIM")

        # Draw vertical separator line
        tft.vline((18, 36), 6 * 12, GRAY)

        # Draw servo names once at the beginning
        for i in range(6):
            y = 36 + i * 12
            tft.text((25, y), SERVO_NAMES[i], WHITE, FONT, 1)
        
        # Instructions at the bottom
        tft.text((self.center_x("POT1: SELECT"), 110), "POT1: SELECT", GREEN, FONT, 1)
        tft.text((self.center_x("BT8: SAVE   BT1:+1 BT2:-1"), 122), "BT8: SAVE   BT1:+1 BT2:-1", GREEN, FONT, 1)
    
    def update_joystick_display(self, tft, joy_data, prev_values):
        """Update joystick values display"""
        vals = {
            'j1x': (joy_data[0], 36, 40),
            'j1y': (joy_data[1], 36, 52),
            'j2x': (joy_data[2], 116, 40),
            'j2y': (joy_data[3], 116, 52),
        }
        
        for key, (value, x, y) in vals.items():
            if prev_values.get(key) != value:
                tft.fillrect((x, y), (30, 8), BLACK)
                tft.text((x, y), self.pad(value), YELLOW, FONT, 1)
                prev_values[key] = value
    
    def update_potentiometer_display(self, tft, pot_value, prev_values):
        """Update potentiometer display"""
        if prev_values.get('pot') != pot_value:
            tft.fillrect((36, 64), (30, 8), BLACK)
            tft.text((36, 64), self.pad(pot_value), YELLOW, FONT, 1)
            prev_values['pot'] = pot_value
    
    def update_buttons_display(self, tft, btn_data, prev_values):
        """Update buttons BT1-BT8 display"""
        bt_changed = any(
            prev_values.get(f'bt{i+1}') != bool(btn_data.get(f'bt{i+1}'))
            for i in range(8)
        )
        
        if bt_changed:
            x_bt = 10 + 20
            tft.fillrect((x_bt, 76), (160 - x_bt, 8), BLACK)
            x = x_bt
            for i in range(8):
                pressed = bool(btn_data.get(f'bt{i+1}'))
                color = GREEN if pressed else GRAY
                tft.text((x, 76), str(i + 1), color, FONT, 1)
                prev_values[f'bt{i+1}'] = pressed
                x += 16
    
    def update_switches_display(self, tft, btn_data, prev_values):
        """Update switches SW1-SW4 display"""
        sw_changed = any(
            prev_values.get(sw) != bool(btn_data.get(sw))
            for sw in ['sw1', 'sw2', 'sw3', 'sw4']
        )
        
        if sw_changed:
            x_sw = 10 + 20
            tft.fillrect((x_sw, 88), (160 - x_sw, 8), BLACK)
            x = x_sw
            for sw in ['sw1', 'sw2', 'sw3', 'sw4']:
                pressed = bool(btn_data.get(sw))
                color = GREEN if pressed else GRAY
                tft.text((x, 88), sw.upper(), color, FONT, 1)
                prev_values[sw] = pressed
                x += 34
    
    def update_mac_display(self, tft, mac_address, prev_mac):
        """Update robot name display"""
        if prev_mac != mac_address:
            tft.fillrect((40, 100), (120, 8), BLACK)
            robot_name = ROBOT_NAMES.get(mac_address, "UNKNOWN")
            tft.text((48, 100), robot_name, YELLOW, FONT, 1)
            return mac_address
        return prev_mac
    
    def update_trim_display(self, tft, servo_trims, selected_servo_index, prev_values, force_refresh=False):
        """Update only cursor and numeric values"""
        
        # 1. Handle cursor (draw only if changed)
        prev_idx = prev_values.get('last_servo_idx', -1)
        if prev_idx != selected_servo_index or force_refresh:
            # Erase old cursor
            if prev_idx != -1:
                old_y = 36 + prev_idx * 12
                tft.text((10, old_y), " ", BLACK, FONT, 1)
            # Draw new one
            new_y = 36 + selected_servo_index * 12
            tft.text((10, new_y), ">", CYAN, FONT, 1)
            prev_values['last_servo_idx'] = selected_servo_index

        # 2. Handle values (loop through all, but fillrect only for changed ones)
        for i in range(6):
            trim_value = servo_trims[i]
            trim_key = f'trim_{i}'
            
            if prev_values.get(trim_key) != trim_value or force_refresh:
                y = 36 + i * 12
                # Clear only the number area (X adjusted to your layout)
                tft.fillrect((136, y), (35, 8), BLACK)
                
                trim_str = f"{'+' if trim_value >= 0 else ''}{trim_value}"
                tft.text((136, y), trim_str, YELLOW, FONT, 1)
                prev_values[trim_key] = trim_value
    
    def show_cleanup_message(self, tft):
        """Show cleanup message before exit"""
        tft.fill(BLACK)
        tft.text((20, 60), "RELEASE BUTTONS...", WHITE, FONT, 1)
