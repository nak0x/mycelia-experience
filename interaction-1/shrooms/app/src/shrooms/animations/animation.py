from framework.app import App

class Animation:

    def __init__(self, shroom):
        self.shroom = shroom

    def on_enter(self):
        if App().config.debug:
            print(f"Enter {self.__class__.__name__}")
        App().update.append(self.handle)

    def on_exit(self):
        if App().config.debug:
            print(f"Exit {self.__class__.__name__}")
        App().update.remove(self.handle)

    def handle(self):
        raise NotImplementedError
    
    def to_dead(self):
        pass

    def to_lighting(self):
        pass

    def to_living(self):
        pass