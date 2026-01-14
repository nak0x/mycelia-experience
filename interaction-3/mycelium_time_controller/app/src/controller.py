from framework.controller import Controller
from framework.components.encoder import Encoder
from framework.utils.gpio import GPIO
from framework.utils.ws.interface import WebsocketInterface
from framework.utils.timer import Timer

class MainController(Controller):
    def setup(self):
        self.interaction_2_done = False
        self.ws_authorize = True
        self.timer = Timer(200, self._authorize_ws)
        Encoder(pinA=GPIO.GPIO25, pinB=GPIO.GPIO26, onCw=self.increment, onCcw=self.decrement)

    def increment(self):
        if not self.interaction_2_done:
            self._send_ws("02-grass-increment")
        else:
            self._send_ws("03-grow-mycelium")

    def decrement(self):
        if not self.interaction_2_done:
            self._send_ws("02-grass-decrement")
        else:
            self._send_ws("03-shrink-mycelium")

    def _send_ws(self, action):
        if self.ws_authorize:
            print(f"> {action}")
            WebsocketInterface().send_value(action, None)
            self.ws_authorize = False
            self.timer.restart()

    def _authorize_ws(self):
        self.ws_authorize = True

    def on_frame_received(self, frame):
        if frame.action == "02-interaction-done" or frame.action == "03-interaction-start":
            self.interaction_2_done = True
        elif frame.action == "02-reset":
            self.interaction_2_done = False
