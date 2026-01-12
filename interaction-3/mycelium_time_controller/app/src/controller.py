from framework.controller import Controller
from framework.components.encoder import Encoder
from framework.utils.gpio import GPIO
from framework.utils.ws.interface import WebsocketInterface

class MainController(Controller):
    def setup(self):
        self.interaction_2_done = False
        Encoder(pinA=GPIO.GPIO25, pinB=GPIO.GPIO26, onCw=self.increment_mycelium, onCcw=self.decrement_mycelium, onChange=self.shake_sphero)

    def shake_sphero(self):
        if not self.interaction_2_done:
            print("> shake sphero")
            WebsocketInterface().send_value("02-shake-sphero", None)

    def increment_mycelium(self):
        if self.interaction_2_done:
            print("> grow mycelium")
            WebsocketInterface().send_value("03-grow-mycelium", None)

    def decrement_mycelium(self):
        if self.interaction_2_done:
            print("> shrink mycelium")
            WebsocketInterface().send_value("03-shrink-mycelium", None)

    def on_frame_received(self, frame):
        if frame.action == "02-interaction-done" or frame.action == "03-interaction-start":
            self.interaction_2_done = True
        elif frame.action == "02-reset":
            self.interaction_2_done = False
