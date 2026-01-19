from framework.controller import Controller
from framework.utils.frames.frame import Frame
from framework.components.relay import Relay
from framework.utils.ws.interface import WebsocketInterface
import time

class WaterController(Controller):
    
    def setup(self):
        self.relay = Relay(27, False)  # Water (NO)
        self.relay2 = Relay(26, False) # Grass (NC)
        
        self.grass_counter = 0

    def on_frame_received(self, frame: Frame):
        if frame.action == "02-grass-increment":
            self.grass_counter += 1
            if self.grass_counter >= 20:
                print("Watering sequence started")
                
                # Turn OFF Grass (Open Circuit)
                self.relay2.open()
                
                # Turn ON Water (Close Circuit)
                self.relay.open()
                
                print("Watering...")
                WebsocketInterface().send_value("02-water-flow-toggle", True)
                
                time.sleep(10)
                
                # Turn OFF Water (Open Circuit)
                self.relay.close()
                
                # Turn ON Grass (Close Circuit)
                self.relay2.close()
                
                print("Watering finished")

        elif frame.action == "02-grass-decrement":
            self.grass_counter = max(0, self.grass_counter - 1)
        
        elif frame.action == "02-reset":
            print(">> RESET command received")
            self.grass_counter = 0
            self.relay.close()   # Water OFF
            self.relay2.close() # Grass ON

        elif frame.action == "02-water-flow-toggle":
            if isinstance(frame.value, bool):
                self.relay.open() if frame.value == True else self.relay.close()

        elif frame.action == "02-grass-toggle":
            if isinstance(frame.value, bool):
                self.relay2.open() if frame.value == True else self.relay2.close()
