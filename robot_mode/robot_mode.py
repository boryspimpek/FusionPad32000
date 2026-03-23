# mode_robot.py - Robot Controller Mode
# Clean version without backward compatibility

from .robot_controller import RobotController

def run(tft):
    """Main robot controller function"""
    controller = RobotController()
    controller.run(tft)
