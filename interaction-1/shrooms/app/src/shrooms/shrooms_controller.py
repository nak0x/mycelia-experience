from framework.controller import Controller
from framework.utils.ws.interface import WebsocketInterface
from framework.app import App
import json


class ShroomsController(Controller):
    shrooms = []
    forest_lighten = False

    def __init__(self, led_strip, mcp):
        super().__init__()
        self.leds = led_strip
        self.mcp = mcp

        App().setup.append(self.setup)
        App().update.append(self.update)

    def setup(self):
        print("coucou")
        with open("./shrooms.json", "r") as f:
            self.config = json.loads(f.read())
        self.init_shrooms()

    def init_shrooms(self):
        if self.config is None:
            return

        for shroom in self.config.get('shrooms', []):
            print(shroom)

    def update(self):
        if self.is_shrooms_lighten() and not self.forest_lighten:
            self.forest_lighten = True
            print("Shroom forest lighten !")
            WebsocketInterface().send_value("01-shroom-forest-lighten", self.forest_lighten)

    def is_shrooms_lighten(self):
        checksum = False
        for shroom in self.shrooms:
            checksum = checksum and shroom.lighten
        return checksum
