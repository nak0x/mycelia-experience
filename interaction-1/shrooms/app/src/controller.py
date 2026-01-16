from framework.controller import Controller
from framework.components.led_strip import LedStrip
from framework.components.mcp3008 import MCP3008
import time

from .shrooms.shrooms_controller import ShroomsController

class MainController(Controller):
    def __init__(self):
        super().__init__()
        leds = LedStrip(27, 430, max_current=2, default_color=(224, 156, 24))
        leds.fill((255, 255, 255))
        leds.display()
        time.sleep(3)
        leds.off()
        leds.clear()
        mcp = MCP3008()
        self.shrooms = ShroomsController(leds, mcp)
