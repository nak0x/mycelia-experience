from framework.app import App
from machine import Pin
from framework.utils.frames.frame import Frame

class Relay:
    is_open = False

    def __init__(self, pin, normally_open: bool = False):
        self.open_value = 0 if normally_open else 1
        self.close_value = 1 if normally_open else 0
        self.pin = Pin(pin, Pin.OUT, value=self.close_value)

    def open(self):
        self.pin.value(self.open_value)
        self.is_open = True

    def close(self):
        self.pin.value(self.close_value)
        self.is_open = False

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

