from machine import Pin
from framework.app import App
from framework.utils.frames.frame import Frame

class Engine:
    is_on = False

    def __init__(self, pin):
        self.pin = Pin(pin, Pin.OUT, Pin.PULL_DOWN)

    def on(self):
        self.pin.on()
        self.is_on = True

    def off(self):
        self.pin.off()
        self.is_on = False
        
