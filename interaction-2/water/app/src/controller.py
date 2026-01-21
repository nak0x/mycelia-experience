from framework.controller import Controller
from framework.utils.frames.frame import Frame
from framework.components.relay import Relay
from framework.utils.ws.interface import WebsocketInterface
from framework.utils.timer import Timer

class WaterController(Controller):
    
    def setup(self):
        self.relay = Relay(27, False)  # Water (NO)
        self.relay2 = Relay(26, False) # Grass (NC)
        
        self.grass_counter = 0
        self.grass_done = False

    def start_watering(self):
        print("Watering started")
        # Turn OFF Grass (Open Circuit)
        self.relay2.open()
        
        # Turn ON Water (Close Circuit)
        WebsocketInterface().send_value("02-water-flow-toggle", True)
        self.relay.open()
    
    def finish_watering(self):
        # Turn OFF Water (Open Circuit)
        WebsocketInterface().send_value("02-water-flow-toggle", False)
        self.relay.close()
        
        # Turn ON Grass (Close Circuit)
        self.relay2.close()
        
        print("Watering finished")

    def on_frame_received(self, frame: Frame):
        if frame.action == "02-grass-increment":
            self.grass_counter += 1
            if self.grass_counter >= 20:
                if self.grass_done:
                    return
                self.grass_done = True
                
                self.start_watering()
                
                # Non-blocking wait using framework Timer
                Timer(20000, self.finish_watering, autostart=True)

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
