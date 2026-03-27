# robot_input.py - Input handling for robot controller
import time
import robot_config

# Module-level state for servo trims
_servo_trims = [0, 0, 0, 0, 0, 0]

def init_input():
    """Initialize input module"""
    global _servo_trims
    _servo_trims = [0, 0, 0, 0, 0, 0]

def get_screen_mode(pot_value):
    """Select screen mode based on potentiometer value"""
    # Extend range to 4 modes: 0-25=MAIN, 26-50=SCREEN2, 51-75=SCREEN3, 76-100=TRIM
    if pot_value <= 25:
        return robot_config.MODE_MAIN
    elif pot_value <= 50:
        return robot_config.MODE_SCREEN2
    elif pot_value <= 75:
        return robot_config.MODE_SCREEN3
    else:
        return robot_config.MODE_TRIM

def check_exit_condition(btn_data, exit_timer):
    """Check exit condition (SW1 + SW2 for 2 seconds)"""
    sw1_pressed = btn_data.get('sw1')
    sw2_pressed = btn_data.get('sw2')
    
    if sw1_pressed and sw2_pressed:
        if exit_timer == 0:
            return time.ticks_ms(), False
        if exit_timer and (time.ticks_ms() - exit_timer) >= robot_config.EXIT_HOLD_TIME_MS:
            return exit_timer, True
        else:
            # Keep the timer running, don't reset to 0
            return exit_timer, False
    else:
        # Reset timer when buttons are not both pressed
        return 0, False

def handle_trim_selection(pot_value, prev_pot1, selected_servo):
    """Handle servo selection in trim mode"""
    if abs(pot_value - prev_pot1) > 3:  # Small hysteresis
        new_idx = min(int((pot_value * 6) / 101), 5)
        if new_idx != selected_servo:
            return new_idx, pot_value
    return selected_servo, prev_pot1

def handle_trim_adjustment(btn_data, prev_btn_data, selected_servo):
    """Handle trim value adjustment"""
    global _servo_trims
    trim_changed = False
    
    # BT1: Increase trim value
    if btn_data.get('bt1') and not prev_btn_data.get('bt1'):
        _servo_trims[selected_servo] = min(50, _servo_trims[selected_servo] + 1)
        trim_changed = True
    
    # BT2: Decrease trim value
    if btn_data.get('bt2') and not prev_btn_data.get('bt2'):
        _servo_trims[selected_servo] = max(-50, _servo_trims[selected_servo] - 1)
        trim_changed = True
    
    return trim_changed

def check_save_request(btn_data, prev_btn_data):
    """Check if save button was pressed"""
    return btn_data.get('bt8') and not prev_btn_data.get('bt8')

def get_servo_trims():
    """Get current servo trim values"""
    global _servo_trims
    return _servo_trims

def set_servo_trims(trims):
    """Set servo trim values"""
    global _servo_trims
    _servo_trims = trims.copy()

def wait_for_button_release():
    """Wait for buttons to be released"""
    import buttons
    while buttons.get_data().get('sw1') or buttons.get_data().get('sw2'):
        time.sleep_ms(50)
