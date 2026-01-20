from framework.controller import Controller
from framework.components.led_strip import LedStrip
from framework.components.mcp3008 import MCP3008
from framework.app import App
import time

from .shrooms.shrooms_controller import ShroomsController

class MainController(Controller):
    def setup(self):
        leds = LedStrip(27, 430, max_current=2, default_color=(224, 156, 24))
        leds.fill((255, 255, 255))
        leds.display()
        time.sleep(3)
        leds.off()
        leds.clear()
        mcp = MCP3008()
        self.shrooms = ShroomsController(leds, mcp)

    def on_frame_received(self, frame):
        if frame.action == "01-reset" or frame.action == "01-reset-shrooms":
            self.shrooms.reset()
        elif frame.action == "01-shroom-forest-lighten":
            self.shrooms.to_shrooms_lighting()
