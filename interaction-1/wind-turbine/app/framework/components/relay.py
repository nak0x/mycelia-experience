from framework.app import App
from machine import Pin
from framework.utils.frames.frame import Frame

class Relay:
    is_open = False

    def __init__(self, pin):
        self.pin = Pin(pin, Pin.OUT, value=1)

    def open(self):
        self.pin.value(0)
        self.is_open = True

    def close(self):
        self.pin.value(1)
        self.is_open = False

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()
