from src.settings import Config
from time import ticks_cpu, sleep

from src.utils.abstract_singleton import SingletonBase


class AppState:
    SETUP = 0
    RUNNING = 1
    STOPPED = 2
    SHUTDOWN = 3


class App(SingletonBase):
    # Event hooks
    setup = []
    update = []
    shutdown = []

    # Constants
    SLOWED = True
    state = AppState.SETUP

    def _init_once(self):
        self.config = Config()
        self.shutdown_request = False
        self.ticks = ticks_cpu

    def run(self):
        for setup in self.setup:
            setup()
        self.state = AppState.RUNNING
        while not self.shutdown_request:
            print(f"App state: {self.state} | slowed: {self.SLOWED}")
            for update in self.update:
                update()
            if self.SLOWED:
                sleep(0.3)
        else:
            self.state = AppState.SHUTDOWN
            for shutdown in self.shutdown:
                shutdown()
