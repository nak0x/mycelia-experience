from framework.app import App
import time

class Timer:
    start_time = None
    started = False

    def __init__(self, duration_ms, on_timeout):
        self.duration_ms = duration_ms
        self.on_timeout = on_timeout

    def start(self):
        self.start_time = time.ticks_ms()
        self.started = True
        App().update.append(self.update)

    def update(self):
        if self.started:
            if time.ticks_ms() - self.start_time >= self.duration_ms:
                self.started = False
                App().update.remove(self.update)
                self.on_timeout()