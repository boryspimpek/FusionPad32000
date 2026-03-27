# robot_controller.py - Main robot controller functions
import time
import joystick
import buttons
import robot_config
import robot_ui
import robot_communication
import robot_input

# Module-level state for the robot controller
_state = {
    'exit_timer': 0,
    'prev_values': {},
    'current_screen': -1,
    'prev_mac': None,
    'prev_btn_data': {},
    'selected_servo': 0,
    'prev_pot1': 0
}

def init_robot_controller():
    """Initialize robot controller module"""
    global _state
    robot_ui.init_ui()
    robot_communication.init_communication()
    robot_input.init_input()
    
    _state = {
        'exit_timer': 0,
        'prev_values': {},
        'current_screen': -1,
        'prev_mac': None,
        'prev_btn_data': {},
        'selected_servo': 0,
        'prev_pot1': 0
    }

def run_robot_controller(tft):
    """Main robot controller function"""
    # Initialize network
    robot_communication.initialize_network()
    robot_communication.set_current_mac_index(0)
    
    # Initialize button data dictionary to avoid KeyError
    _state['prev_btn_data'] = buttons.get_data()

    while True:
        # 1. Read all inputs at the beginning of loop
        joy_data = joystick.get_data()
        pot_data = joystick.get_potentiometers()
        btn_data = buttons.get_data()
        
        # 2. EXIT LOGIC (Priority #1)
        # Check if SW1 and SW2 are physically pressed
        _state['exit_timer'], should_exit = robot_input.check_exit_condition(
            btn_data, _state['exit_timer']
        )
        if should_exit:
            # CONDITION MET - EXIT
            break

        # 3. MAC ADDRESS CHANGE (Only on SW2 click when SW1 is released)
        # Detect "rising edge" - now pressed, previously not pressed
        old_mac_index = robot_communication.get_current_mac_index()
        robot_communication.switch_mac_address(btn_data, _state['prev_btn_data'])
        if robot_communication.get_current_mac_index() != old_mac_index:
            _state['prev_mac'] = None  # Force LCD text refresh

        # 4. SCREEN SELECTION (Potentiometer 2)
        new_screen = robot_input.get_screen_mode(pot_data.get('pot2', 0))
        if new_screen != _state['current_screen']:
            _state['current_screen'] = new_screen
            _state['prev_values'].clear()
            
            if _state['current_screen'] == robot_config.MODE_MAIN:
                robot_ui.draw_main_screen(tft)
            elif _state['current_screen'] == robot_config.MODE_SCREEN2:
                robot_ui.draw_actions_screen(tft, 'screen2', robot_communication.get_current_mac())
            elif _state['current_screen'] == robot_config.MODE_SCREEN3:
                robot_ui.draw_actions_screen(tft, 'screen3', robot_communication.get_current_mac())
            elif _state['current_screen'] == robot_config.MODE_TRIM:
                robot_ui.draw_trim_screen(tft)

        # 5. UI UPDATE AND TRIM HANDLING
        if _state['current_screen'] == robot_config.MODE_MAIN:
            _update_main_screen(tft, joy_data, pot_data, btn_data)

        elif _state['current_screen'] == robot_config.MODE_TRIM:
            _update_trim_screen(tft, pot_data, btn_data)

        # 6. SEND CONTROL DATA (only outside TRIM mode)
        if _state['current_screen'] != robot_config.MODE_TRIM:
            robot_communication.send_control_data(
                joy_data, 
                pot_data.get('pot1', 0), 
                _state['current_screen'], 
                btn_data
            )

        # 7. SAVE BUTTON STATE FOR NEXT LOOP
        # Make a copy of dictionary so state['prev_btn_data'] doesn't change during processing
        for key in btn_data:
            _state['prev_btn_data'][key] = btn_data[key]

        time.sleep_ms(robot_config.UPDATE_RATE_MS)

    # AFTER LOOP EXIT
    _cleanup(tft)

def _update_main_screen(tft, joy_data, pot_data, btn_data):
    """Update main screen display"""
    robot_ui.update_joystick_display(tft, joy_data, _state['prev_values'])
    robot_ui.update_potentiometer_display(tft, pot_data.get('pot1', 0), _state['prev_values'])
    robot_ui.update_buttons_display(tft, btn_data, _state['prev_values'])
    robot_ui.update_switches_display(tft, btn_data, _state['prev_values'])
    _state['prev_mac'] = robot_ui.update_mac_display(
        tft, 
        robot_communication.get_current_mac(), 
        _state['prev_mac']
    )

def _update_trim_screen(tft, pot_data, btn_data):
    """Update trim screen display and handle trim operations"""
    trim_changed = False
    
    # --- Servo selection (Potentiometer 1) ---
    p1 = pot_data.get('pot1', 0)
    _state['selected_servo'], _state['prev_pot1'] = robot_input.handle_trim_selection(
        p1, _state['prev_pot1'], _state['selected_servo']
    )
    
    # --- Value change (BT1 / BT2) ---
    # Use rising edge (pressed now, not previously)
    trim_changed = robot_input.handle_trim_adjustment(
        btn_data, _state['prev_btn_data'], _state['selected_servo']
    )
        
    # --- Save ---
    if robot_input.check_save_request(btn_data, _state['prev_btn_data']):
        robot_communication.send_save_data()
        # Optionally: flash header green to indicate save

    # --- Communication and UI ---
    if trim_changed:
        # Send packet only when change occurred
        robot_communication.send_trim_data(robot_input.get_servo_trims())
    
    # Refresh UI (function itself checks what exactly to redraw)
    robot_ui.update_trim_display(
        tft, 
        robot_input.get_servo_trims(), 
        _state['selected_servo'], 
        _state['prev_values']
    )

def _cleanup(tft):
    """Clean up resources before exit"""
    robot_ui.show_cleanup_message(tft)
    robot_input.wait_for_button_release()
    robot_communication.cleanup()

def run(tft):
    """Module-level run function for compatibility with main.py"""
    init_robot_controller()
    run_robot_controller(tft)
