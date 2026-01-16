import time
from framework.controller import Controller
from framework.utils.ws.interface import WebsocketInterface
from framework.app import App
from .shroom import Shroom
from framework.utils.abstract_singleton import SingletonBase
import json


class ShroomsController(Controller, SingletonBase):
    shrooms = []
    forest_lighten = False

    def __init__(self, led_strip, mcp):
        super().__init__()
        self.leds = led_strip
        self.mcp = mcp

    def setup(self):
        with open("./shrooms.json", "r") as f:
            self.config = json.loads(f.read())
        self.init_shrooms()

    def init_shrooms(self):
        if self.config is None:
            return

        # Setup shrooms from config file
        for shroom in self.config.get('shrooms', []):
            self.shrooms.append(Shroom(
                name=shroom.get('name', 'shroom'),
                chanel=shroom.get('chanel', 0),
                controler=self,
                threshold_drop=shroom.get('threshold_drop', 50),
                delta_ms=self.config.get('delta_ms', 150),
                cooldown_ms=self.config.get('cooldown_ms', 1000),
                buf_size=self.config.get('buf_size', 32),
                start=shroom.get('start', 0),
                span=shroom.get('span', 3),
                has_sensor=shroom.get('has_sensor', False),
                lighten=shroom.get('lighten', False)
            ))

        # Setup shroom chanels to MCP3008
        self.mcp.chanels = [shroom.chanel for shroom in self.shrooms if shroom.chanel is not None]

        self.test_shrooms_lights()

    def test_shrooms_lights(self):
        for shroom in self.shrooms:
            print(f"Testing shroom {shroom.name} LEDs from {shroom.led_config['start_pixel']} to {shroom.led_config['end_pixel']}")
            shroom.test_leds()
            # time.sleep(1)

    def update(self):
        self.mcp.update()
        if self.is_shrooms_lighten() and not self.forest_lighten:
            self.forest_lighten = True
            print("Shroom forest lighten !")
            WebsocketInterface().send_value("01-shroom-forest-lighten", self.forest_lighten)

    def is_shrooms_lighten(self):
        return all(shroom.lighten for shroom in self.shrooms)
