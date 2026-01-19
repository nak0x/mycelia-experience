from framework.controller import Controller
from framework.utils.frames.frame import Frame
from framework.components.relay import Relay
from framework.utils.ws.interface import WebsocketInterface
import time

class WaterController(Controller):
    
    def setup(self):
        self.relay = Relay(27, "02-water-flow-toggle")
        self.relay2 = Relay(26, "02-grass-toggle")
        
        # État initial:
        # Relay (Water) NO -> open() = 0 (OFF)
        # Relay2 (Grass) NC -> open() = 0 (ON)
        self.relay.open()
        self.relay2.open()
        
        self.grass_counter = 0

    def on_frame_received(self, frame: Frame):
        if frame.action == "02-grass-increment":
            self.grass_counter += 1
            if self.grass_counter >= 20:
                self.relay2.close()
                print("Watering...")
                WebsocketInterface().send_value("02-water-flow-toggle", True)
                time.sleep(10)
                self.relay.open()
                print("Watering finished")

        elif frame.action == "02-grass-decrement":
            self.grass_counter = max(0, self.grass_counter - 1)
        
        elif frame.action == "02-reset":
            print(">> RESET command received")
            self.grass_counter = 0
            self.relay.open()
            self.relay2.open()

