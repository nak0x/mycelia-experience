import time
from framework.components.mcp3008 import Chanel
from framework.components.led_strip import LedStrip
from src.shrooms.animator import Animator, DeadAnimation
from framework.app import App

class Shroom:
    def __init__(self, name, chanel, leds: LedStrip, threshold_drop=50, delta_ms=150,
                 cooldown_ms=1000, buf_size=32, start=0, span=3, lighten=False):
        
        self.chanel = Chanel(chanel, name, self.handle_light_level) if chanel is not None else None
        self.name = name
        self.leds = leds

        self.led_config = {
            "span": span,
            "start_pixel": start,
            "end_pixel": start + span - 1
        }

        self.threshold_drop = int(threshold_drop)   # required drop amount
        self.delta_ms = int(delta_ms)               # time window in ms
        self.cooldown_ms = int(cooldown_ms)
        self.lighten = lighten

        # Track max level in the current window
        self._max_level = 0
        self._max_level_time = time.ticks_ms()
        self._last_trigger = time.ticks_ms()
        
        # Setup animator with animations
        self.animator = Animator()
        
        # Start the living animation by default
        self.animator.play(DeadAnimation())

        App().update.append(self.update)

    def update(self):
        self.display_color(self.animator.update())

    def display_color(self, color):
        print(f"{self.name}: Display color {color}")
        for i in range(self.led_config['start_pixel'], self.led_config['end_pixel'] + 1):
            self.leds.set_pixel(i, color, show=False)
        self.leds.display()
    
    def reset(self):
        if self.lighten:
            self.lighten = False
            self._max_level = 0
            self._max_level_time = time.ticks_ms()

            self.display_color((0, 0, 0))

        print(f"{self.name}: Reset")

    def setup_leds(self, start_pixel, end_pixel):
        self.led_config["start_pixel"] = start_pixel
        self.led_config["end_pixel"] = end_pixel

    def test_leds(self):
        self.display_color((255, 0, 0))

    def on_light_detected(self):
        if self.lighten:
            return
        
        # Play glow animation
        self.lighten = True
        self.animator.play(self.animator.state.to_lighting() if self.animator.state is not None else None)
        print(f"{self.name}: Light detected, starting glow")

    def glow(self):
        if self.lighten:
            return
        
        self.lighten = True
        self.animator.play(self.animator.state.to_lighting() if self.animator.state is not None else None)
        print(f"{self.name}: Glow triggered programmatically")

    def handle_light_level(self, level, *args):
        if self.chanel is None:
            return

        # print(f"{self.name}: Ch {self.chanel.pin} : Light level {level} : {self.lighten}")
        if self.lighten:
            return

        now = time.ticks_ms()

        # Check for drop threshold first (before window reset)
        drop = self._max_level - level
        if drop >= self.threshold_drop:
            # Check cooldown before triggering
            if time.ticks_diff(now, self._last_trigger) >= self.cooldown_ms:
                self._last_trigger = now
                self._max_level = level  # Reset for next detection
                self._max_level_time = now
                self.on_light_detected()
                return

        # Check if window has expired, reset max level
        if time.ticks_diff(now, self._max_level_time) > self.delta_ms:
            self._max_level = level
            self._max_level_time = now
            return

        # Update max level in current window
        if level > self._max_level:
            self._max_level = level
