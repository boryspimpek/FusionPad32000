# robot_ui.py - UI Management for robot controller
import glcdfont
from .robot_config import FONT, UI_LAYOUT, ROBOT_ACTIONS, SERVO_NAMES, ROBOT_NAMES, BLACK, WHITE, CYAN, YELLOW, GREEN, RED, GRAY

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
        
        layout = UI_LAYOUT
        tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] +  0), "J1X:", CYAN,   FONT, 1)
        tft.text((layout['COL_RIGHT'], layout['MARGIN_TOP'] +  0), "J2X:", CYAN,   FONT, 1)
        tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 12), "J1Y:", CYAN,   FONT, 1)
        tft.text((layout['COL_RIGHT'], layout['MARGIN_TOP'] + 12), "J2Y:", CYAN,   FONT, 1)
        tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 24), "POT:", CYAN, FONT, 1)
        tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 36), "BT:",  CYAN,  FONT, 1)
        tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 48), "SW:",  CYAN,  FONT, 1)
        tft.text((layout['COL_LEFT'], layout['MARGIN_TOP'] + 60), "ROBOT:", CYAN,    FONT, 1)
        tft.text((self.center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", RED, FONT, 1)
    
    def draw_actions_screen(self, tft, screen_key):
        """Draw robot actions screen"""
        tft.fill(BLACK)
        actions = ROBOT_ACTIONS[screen_key]
        self.draw_header(tft, actions['title'])
        
        layout = UI_LAYOUT
        
        for i in range(4):
            y = layout['LIST_Y'] + i * layout['ROW_HEIGHT']
            tft.text((layout['ACTION_X_LEFT'], y), actions['left'][i], WHITE, FONT, 1)
            tft.text((layout['ACTION_X_RIGHT'], y), actions['right'][i], WHITE, FONT, 1)
        
        tft.text((self.center_x("HOLD SW1 + SW2 = EXIT"), 118), "HOLD SW1 + SW2 = EXIT", RED, FONT, 1)
    
    def draw_servo_list(self, tft, servo_trims, selected_servo_index=None, show_cursor=False):
        """Draw servo list with trim values"""
        layout = UI_LAYOUT
        
        # Draw vertical separator line
        tft.vline((layout['COL_LEFT'] + 8, layout['LIST_Y'] - 10), 
                  6 * layout['ROW_HEIGHT'], GRAY)
        
        # List of servos with their trim values
        for i in range(6):
            y = (layout['LIST_Y'] - 10) + i * layout['ROW_HEIGHT']
            servo_name = SERVO_NAMES[i]
            trim_value = servo_trims[i]
            
            # Cursor (only in update mode)
            if show_cursor:
                if i == selected_servo_index:
                    tft.text((layout['COL_LEFT'], y), ">", CYAN, FONT, 1)
                else:
                    tft.text((layout['COL_LEFT'], y), " ", BLACK, FONT, 1)
            
            # Servo name
            tft.text((layout['COL_LEFT'] + 15, y), servo_name, WHITE, FONT, 1)
            
            # Trim value
            trim_str = str(trim_value)
            if trim_value >= 0:
                trim_str = "+" + trim_str
            tft.text((layout['VAL_LEFT'] + 100, y), trim_str, YELLOW, FONT, 1)
    
    def draw_trim_screen(self, tft):
        """Draw static trim screen interface (called once)"""
        tft.fill(BLACK)
        self.draw_header(tft, "SERVO TRIM")

        layout = UI_LAYOUT

        # Draw vertical separator line
        tft.vline((layout['COL_LEFT'] + 8, layout['LIST_Y'] - 10), 
                  6 * layout['ROW_HEIGHT'], GRAY)

        # Draw servo names once at the beginning
        for i in range(6):
            y = (layout['LIST_Y'] - 10) + i * layout['ROW_HEIGHT']
            tft.text((layout['COL_LEFT'] + 15, y), SERVO_NAMES[i], WHITE, FONT, 1)
        
        # Instructions at the bottom
        tft.text((self.center_x("POT1: SELECT"), 110), "POT1: SELECT", GREEN, FONT, 1)
        tft.text((self.center_x("BT8: SAVE   BT1:+1 BT2:-1"), 122), "BT8: SAVE   BT1:+1 BT2:-1", GREEN, FONT, 1)
    
    def update_joystick_display(self, tft, joy_data, prev_values):
        """Update joystick values display"""
        layout = UI_LAYOUT
        vals = {
            'j1x': (joy_data[0], layout['VAL_LEFT'], layout['MARGIN_TOP'] +  0),
            'j1y': (joy_data[1], layout['VAL_LEFT'], layout['MARGIN_TOP'] + 12),
            'j2x': (joy_data[2], layout['VAL_RIGHT'], layout['MARGIN_TOP'] +  0),
            'j2y': (joy_data[3], layout['VAL_RIGHT'], layout['MARGIN_TOP'] + 12),
        }
        
        for key, (value, x, y) in vals.items():
            if prev_values.get(key) != value:
                tft.fillrect((x, y), (30, 8), BLACK)
                tft.text((x, y), self.pad(value), YELLOW, FONT, 1)
                prev_values[key] = value
    
    def update_potentiometer_display(self, tft, pot_value, prev_values):
        """Update potentiometer display"""
        layout = UI_LAYOUT
        if prev_values.get('pot') != pot_value:
            tft.fillrect((layout['VAL_LEFT'], layout['MARGIN_TOP'] + 24), (30, 8), BLACK)
            tft.text((layout['VAL_LEFT'], layout['MARGIN_TOP'] + 24), self.pad(pot_value), YELLOW, FONT, 1)
            prev_values['pot'] = pot_value
    
    def update_buttons_display(self, tft, btn_data, prev_values):
        """Update buttons BT1-BT8 display"""
        layout = UI_LAYOUT
        bt_changed = any(
            prev_values.get(f'bt{i+1}') != bool(btn_data.get(f'bt{i+1}'))
            for i in range(8)
        )
        
        if bt_changed:
            x_bt = layout['COL_LEFT'] + 20
            tft.fillrect((x_bt, layout['MARGIN_TOP'] + 36), (160 - x_bt, 8), BLACK)
            x = x_bt
            for i in range(8):
                pressed = bool(btn_data.get(f'bt{i+1}'))
                color = GREEN if pressed else GRAY
                tft.text((x, layout['MARGIN_TOP'] + 36), str(i + 1), color, FONT, 1)
                prev_values[f'bt{i+1}'] = pressed
                x += 16
    
    def update_switches_display(self, tft, btn_data, prev_values):
        """Update switches SW1-SW4 display"""
        layout = UI_LAYOUT
        sw_changed = any(
            prev_values.get(sw) != bool(btn_data.get(sw))
            for sw in ['sw1', 'sw2', 'sw3', 'sw4']
        )
        
        if sw_changed:
            x_sw = layout['COL_LEFT'] + 20
            tft.fillrect((x_sw, layout['MARGIN_TOP'] + 48), (160 - x_sw, 8), BLACK)
            x = x_sw
            for sw in ['sw1', 'sw2', 'sw3', 'sw4']:
                pressed = bool(btn_data.get(sw))
                color = GREEN if pressed else GRAY
                tft.text((x, layout['MARGIN_TOP'] + 48), sw.upper(), color, FONT, 1)
                prev_values[sw] = pressed
                x += 34
    
    def update_mac_display(self, tft, mac_address, prev_mac):
        """Update robot name display"""
        layout = UI_LAYOUT
        if prev_mac != mac_address:
            tft.fillrect((layout['COL_LEFT'] + 30, layout['MARGIN_TOP'] + 60), (120, 8), BLACK)
            robot_name = ROBOT_NAMES.get(mac_address, "UNKNOWN")
            tft.text((layout['COL_LEFT'] + 30, layout['MARGIN_TOP'] + 60), robot_name, YELLOW, FONT, 1)
            return mac_address
        return prev_mac
    
    def update_trim_display(self, tft, servo_trims, selected_servo_index, prev_values, force_refresh=False):
        """Update only cursor and numeric values"""
        layout = UI_LAYOUT
        
        # 1. Handle cursor (draw only if changed)
        prev_idx = prev_values.get('last_servo_idx', -1)
        if prev_idx != selected_servo_index or force_refresh:
            # Erase old cursor
            if prev_idx != -1:
                old_y = (layout['LIST_Y'] - 10) + prev_idx * layout['ROW_HEIGHT']
                tft.text((layout['COL_LEFT'], old_y), " ", BLACK, FONT, 1)
            # Draw new one
            new_y = (layout['LIST_Y'] - 10) + selected_servo_index * layout['ROW_HEIGHT']
            tft.text((layout['COL_LEFT'], new_y), ">", CYAN, FONT, 1)
            prev_values['last_servo_idx'] = selected_servo_index

        # 2. Handle values (loop through all, but fillrect only for changed ones)
        for i in range(6):
            trim_value = servo_trims[i]
            trim_key = f'trim_{i}'
            
            if prev_values.get(trim_key) != trim_value or force_refresh:
                y = (layout['LIST_Y'] - 10) + i * layout['ROW_HEIGHT']
                # Clear only the number area (X adjusted to your layout)
                tft.fillrect((layout['VAL_LEFT'] + 100, y), (35, 8), BLACK)
                
                trim_str = f"{'+' if trim_value >= 0 else ''}{trim_value}"
                tft.text((layout['VAL_LEFT'] + 100, y), trim_str, YELLOW, FONT, 1)
                prev_values[trim_key] = trim_value
    
    def show_cleanup_message(self, tft):
        """Show cleanup message before exit"""
        tft.fill(BLACK)
        tft.text((20, 60), "RELEASE BUTTONS...", WHITE, FONT, 1)
