from framework.components.led_strip import LedStrip
from framework.app import App
import time  # Use time for delays

class Animation:
    current_step = 0
    steps = []
    step_delay_ms = 500  # Default delay between steps in milliseconds

    def __init__(self):
        self.last_step_time = 0

    def on_enter(self):
        self.last_step_time = time.ticks_ms()

    def on_exit(self):
        pass

    def to_dead(self):
        return DeadAnimation()

    def to_lighting(self):
        return None

    def to_living(self):
        return None

    def play(self):

        if self.current_step >= len(self.steps):
            self.current_step = 0

        current_time = time.ticks_ms()
        elapsed = time.ticks_diff(current_time, self.last_step_time)
        
        # Non-blocking delay: only advance step when enough time has passed
        if elapsed >= self.step_delay_ms:
            self.current_step += 1
            self.last_step_time = current_time
            return self.steps[self.current_step - 1]
        
        # Return current step while waiting
        return self.steps[self.current_step]

class LightingAnimation(Animation):
    steps = [
        (0, 10, 0),
        (10, 0, 0),
        (0, 10, 0),
        (10, 0, 0)
    ]
    step_delay_ms = 300  # Customize delay for this animation

    def __init__(self):
        super().__init__()

    def on_enter(self):
        super().on_enter()
        print("Entering LIGHTING")

    def play(self):
        step = super().play()
        return step

    def on_exit(self):
        print("Exiting LIGHTING")

    def to_living(self):
        return LivingAnimation()


class DeadAnimation(Animation):
    steps = [
        (0, 0, 10),
        (10, 0, 0),
        (0, 0, 10),
        (10, 0, 0)
    ]
    step_delay_ms = 500  # Customize delay for this animation

    def __init__(self):
        super().__init__()

    def on_enter(self):
        super().on_enter()
        print("Entering DEAD")

    def play(self):
        step = super().play()
        return step

    def on_exit(self):
        print("Exiting DEAD")

    def to_lighting(self):
        return LightingAnimation()

class LivingAnimation(Animation):
    steps = [
        (0, 0, 10),
        (0, 10, 0),
        (0, 0, 10),
        (0, 10, 0)
    ]
    step_delay_ms = 400  # Customize delay for this animation

    def __init__(self):
        super().__init__()

    def on_enter(self):
        super().on_enter()
        print("Entering LIVING")

    def play(self):
        step = super().play()
        return step

    def on_exit(self):
        print("Exiting LIVING")

    def to_idle(self):
        return DeadAnimation()


class Animator:
    state = None

    def play(self, new_state):
        if self.state is not None:
            self.state.on_exit()
        self.state = new_state
        self.state.on_enter()

    def update(self):
        if self.state is None:
            return (0, 0, 0)
        return self.state.play()
