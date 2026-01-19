from framework.controller import Controller
from framework.components.relay import Relay
from framework.utils.gpio import GPIO

class WindController(Controller):
    
    def setup(self):
        self.relay = Relay(GPIO.GPIO27)
    
    def on_frame_received(self, frame):
        if frame.action == "01-wind-toggle":
            self.relay.open() if frame.value == True else self.relay.close()
        elif frame.action == "01-reset":
            self.relay.close()
