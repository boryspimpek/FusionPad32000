# robot_mode.py - Robot Controller Mode entry point
import robot_controller

def run(tft):
    """Main robot controller function"""
    controller = robot_controller.RobotController()
    controller.run(tft)
