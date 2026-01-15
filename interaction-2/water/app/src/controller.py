from framework.controller import Controller
from framework.utils.frames.frame import Frame
from framework.components.relay import Relay

class WaterController(Controller):
    
    def setup(self):
        self.relay = Relay(27, "02-balance-toggle")
        self.relay2 = Relay(26, "02-grass-toggle")
        self.grass_counter = 0

    def on_frame_received(self, frame: Frame):
        if frame.action == "02-grass-increment":
            self.grass_counter += 1
            print(f"Grass counter: {self.grass_counter}")
            if self.grass_counter >= 20:
                self.relay2.close()

        elif frame.action == "02-grass-decrement":
            self.grass_counter = max(0, self.grass_counter - 1)
            print(f"Grass counter: {self.grass_counter}")
        
        elif frame.action == "02-reset":
            print(">> RESET command received")
            self.grass_counter = 0
            self.relay.open()
            self.relay2.open()

