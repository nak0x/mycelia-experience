from framework.controller import Controller
from framework.components.led_strip import LedStrip
from framework.components.mcp3008 import MCP3008

from .shrooms.shrooms_controller import ShroomsController

class MainController(Controller):
    def __init__(self):
        super().__init__()
        leds = LedStrip(27, 300, (224, 156, 24))
        mcp = MCP3008()
        self.shrooms = ShroomsController(leds, mcp)
