from .robot_controller import RobotController

def run(tft):
    """Main robot controller function"""
    controller = RobotController()
    controller.run(tft)
