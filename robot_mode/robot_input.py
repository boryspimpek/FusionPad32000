# robot_input.py - Input handling for robot controller
import time
from .robot_config import MODE_MAIN, MODE_SCREEN2, MODE_SCREEN3, MODE_TRIM, EXIT_HOLD_TIME_MS

class RobotInput:
    def __init__(self):
        self.servo_trims = [0, 0, 0, 0, 0, 0]
    
    def get_screen_mode(self, pot_value):
        """Select screen mode based on potentiometer value"""
        # Extend range to 4 modes: 0-25=MAIN, 26-50=SCREEN2, 51-75=SCREEN3, 76-100=TRIM
        if pot_value <= 25:
            return MODE_MAIN
        elif pot_value <= 50:
            return MODE_SCREEN2
        elif pot_value <= 75:
            return MODE_SCREEN3
        else:
            return MODE_TRIM
    
    def check_exit_condition(self, btn_data, exit_timer):
        """Check exit condition (SW1 + SW2 for 2 seconds)"""
        if btn_data.get('sw1') and btn_data.get('sw2'):
            if exit_timer == 0:
                return time.ticks_ms(), False
            elif time.ticks_diff(time.ticks_ms(), exit_timer) > EXIT_HOLD_TIME_MS:
                return exit_timer, True
        return 0, False
    
    def handle_trim_selection(self, pot_value, prev_pot1, selected_servo):
        """Handle servo selection in trim mode"""
        if abs(pot_value - prev_pot1) > 3:  # Small hysteresis
            new_idx = min(int((pot_value * 6) / 101), 5)
            if new_idx != selected_servo:
                return new_idx, pot_value
        return selected_servo, prev_pot1
    
    def handle_trim_adjustment(self, btn_data, prev_btn_data, selected_servo):
        """Handle trim value adjustment"""
        trim_changed = False
        
        # BT1: Increase trim value
        if btn_data.get('bt1') and not prev_btn_data.get('bt1'):
            self.servo_trims[selected_servo] = min(50, self.servo_trims[selected_servo] + 1)
            trim_changed = True
        
        # BT2: Decrease trim value
        if btn_data.get('bt2') and not prev_btn_data.get('bt2'):
            self.servo_trims[selected_servo] = max(-50, self.servo_trims[selected_servo] - 1)
            trim_changed = True
        
        return trim_changed
    
    def check_save_request(self, btn_data, prev_btn_data):
        """Check if save button was pressed"""
        return btn_data.get('bt8') and not prev_btn_data.get('bt8')
    
    def get_servo_trims(self):
        """Get current servo trim values"""
        return self.servo_trims
    
    def set_servo_trims(self, trims):
        """Set servo trim values"""
        self.servo_trims = trims.copy()
    
    def wait_for_button_release(self):
        """Wait for buttons to be released"""
        import buttons
        while buttons.get_data().get('sw1') or buttons.get_data().get('sw2'):
            time.sleep_ms(50)
