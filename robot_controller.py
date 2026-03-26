# robot_controller.py - Main robot controller class
import time
import joystick
import buttons
import robot_config
import robot_ui
import robot_communication
import robot_input

class RobotController:
    def __init__(self):
        self.ui = robot_ui.RobotUI()
        self.communication = robot_communication.RobotCommunication()
        self.input_handler = robot_input.RobotInput()
        
        # Application state
        self.state = {
            'exit_timer': 0,
            'prev_values': {},
            'current_screen': -1,
            'prev_mac': None,
            'prev_btn_data': {},
            'selected_servo': 0,
            'prev_pot1': 0
        }
    
    def run(self, tft):
        """Main robot controller function"""
        # Initialize network
        self.communication.initialize_network()
        self.communication.set_current_mac_index(0)
        
        # Initialize button data dictionary to avoid KeyError
        self.state['prev_btn_data'] = buttons.get_data()

        while True:
            # 1. Read all inputs at the beginning of loop
            joy_data = joystick.get_data()
            pot_data = joystick.get_potentiometers()
            btn_data = buttons.get_data()
            
            # 2. EXIT LOGIC (Priority #1)
            # Check if SW1 and SW2 are physically pressed
            self.state['exit_timer'], should_exit = self.input_handler.check_exit_condition(
                btn_data, self.state['exit_timer']
            )
            if should_exit:
                # CONDITION MET - EXIT
                break

            # 3. MAC ADDRESS CHANGE (Only on SW2 click when SW1 is released)
            # Detect "rising edge" - now pressed, previously not pressed
            old_mac_index = self.communication.current_mac_index
            self.communication.switch_mac_address(btn_data, self.state['prev_btn_data'])
            if self.communication.current_mac_index != old_mac_index:
                self.state['prev_mac'] = None  # Force LCD text refresh

            # 4. SCREEN SELECTION (Potentiometer 2)
            new_screen = self.input_handler.get_screen_mode(pot_data.get('pot2', 0))
            if new_screen != self.state['current_screen']:
                self.state['current_screen'] = new_screen
                self.state['prev_values'].clear()
                
                if self.state['current_screen'] == robot_config.MODE_MAIN:
                    self.ui.draw_main_screen(tft)
                elif self.state['current_screen'] == robot_config.MODE_SCREEN2:
                    self.ui.draw_actions_screen(tft, 'screen2', self.communication.get_current_mac())
                elif self.state['current_screen'] == robot_config.MODE_SCREEN3:
                    self.ui.draw_actions_screen(tft, 'screen3', self.communication.get_current_mac())
                elif self.state['current_screen'] == robot_config.MODE_TRIM:
                    self.ui.draw_trim_screen(tft)

            # 5. UI UPDATE AND TRIM HANDLING
            if self.state['current_screen'] == robot_config.MODE_MAIN:
                self._update_main_screen(tft, joy_data, pot_data, btn_data)

            elif self.state['current_screen'] == robot_config.MODE_TRIM:
                self._update_trim_screen(tft, pot_data, btn_data)

            # 6. SEND CONTROL DATA (only outside TRIM mode)
            if self.state['current_screen'] != robot_config.MODE_TRIM:
                self.communication.send_control_data(
                    joy_data, 
                    pot_data.get('pot1', 0), 
                    self.state['current_screen'], 
                    btn_data
                )

            # 7. SAVE BUTTON STATE FOR NEXT LOOP
            # Make a copy of dictionary so state['prev_btn_data'] doesn't change during processing
            for key in btn_data:
                self.state['prev_btn_data'][key] = btn_data[key]

            time.sleep_ms(robot_config.UPDATE_RATE_MS)

        # AFTER LOOP EXIT
        self._cleanup(tft)
    
    def _update_main_screen(self, tft, joy_data, pot_data, btn_data):
        """Update main screen display"""
        self.ui.update_joystick_display(tft, joy_data, self.state['prev_values'])
        self.ui.update_potentiometer_display(tft, pot_data.get('pot1', 0), self.state['prev_values'])
        self.ui.update_buttons_display(tft, btn_data, self.state['prev_values'])
        self.ui.update_switches_display(tft, btn_data, self.state['prev_values'])
        self.state['prev_mac'] = self.ui.update_mac_display(
            tft, 
            self.communication.get_current_mac(), 
            self.state['prev_mac']
        )
    
    def _update_trim_screen(self, tft, pot_data, btn_data):
        """Update trim screen display and handle trim operations"""
        trim_changed = False
        
        # --- Servo selection (Potentiometer 1) ---
        p1 = pot_data.get('pot1', 0)
        self.state['selected_servo'], self.state['prev_pot1'] = self.input_handler.handle_trim_selection(
            p1, self.state['prev_pot1'], self.state['selected_servo']
        )
        
        # --- Value change (BT1 / BT2) ---
        # Use rising edge (pressed now, not previously)
        trim_changed = self.input_handler.handle_trim_adjustment(
            btn_data, self.state['prev_btn_data'], self.state['selected_servo']
        )
            
        # --- Save ---
        if self.input_handler.check_save_request(btn_data, self.state['prev_btn_data']):
            self.communication.send_save_data()
            # Optionally: flash header green to indicate save

        # --- Communication and UI ---
        if trim_changed:
            # Send packet only when change occurred
            self.communication.send_trim_data(self.input_handler.get_servo_trims())
        
        # Refresh UI (function itself checks what exactly to redraw)
        self.ui.update_trim_display(
            tft, 
            self.input_handler.get_servo_trims(), 
            self.state['selected_servo'], 
            self.state['prev_values']
        )
    
    def _cleanup(self, tft):
        """Clean up resources before exit"""
        self.ui.show_cleanup_message(tft)
        self.input_handler.wait_for_button_release()
        self.communication.cleanup()
