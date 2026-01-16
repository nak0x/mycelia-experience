import time
import random
from framework.components.mcp3008 import Chanel

class Shroom:
    def __init__(self, name, chanel, controler, threshold_drop=50, delta_ms=150,
                 cooldown_ms=1000, buf_size=32, start=0, span=3, has_sensor=False, lighten=False):
        
        3self.chanel = Chanel(chanel, name, self.handle_light_level) if has_sensor else None
        self.name = name
        self.controller = controler

        self.led_config = {
            "span": span,
            "start_pixel": start,
            "end_pixel": start + span - 1
        }

        self.threshold_drop = int(threshold_drop)   # required drop amount
        self.delta_ms = int(delta_ms)               # time window in ms
        self.cooldown_ms = int(cooldown_ms)
        self.lighten = lighten

        # ring buffer: times + levels
        self._ts = [0] * buf_size
        self._lv = [0] * buf_size
        self._n = 0            # number of valid samples (<= buf_size)
        self._head = 0         # next write index

        self._last_trigger = time.ticks_ms()

    def setup_leds(self, start_pixel, end_pixel):
        self.led_config["start_pixel"] = start_pixel
        self.led_config["end_pixel"] = end_pixel

    def test_leds(self):
        leds = self.controller.leds
        for i in range(self.led_config['start_pixel'], self.led_config['end_pixel'] + 1):
            print(f"Lighting pixel {i} of shroom {self.name}")
            leds.set_pixel(i, (255, 155, 25), show=True)

    def on_light_detected(self):
        if self.lighten:
            return

        leds = self.controller.leds
        for l in range(25):
            t = l / 24.0  # Normalize to 0-1
            factor = t * t  # Ease-in quadratic
            r = int(255 * factor)
            g = int(155 * factor)
            b = int(25 * factor)
            print(f"Lighting shroom {self.name} with color ({r}, {g}, {b})")
            for i in range(self.led_config['start_pixel'], self.led_config['end_pixel'] + 1):
                leds.set_pixel(i, (r, g, b), show=False)
            leds.display()
            time.sleep(0.3)

        leds.display()
        self.lighten = True
        print("%s: Lighten" % self.name)

    def handle_light_level(self, level, *args):
        if self.lighten:
            return

        # print(f"{self.name}: {level}")
        now = time.ticks_ms()
        level = int(level)

        # cooldown
        if time.ticks_diff(now, self._last_trigger) < self.cooldown_ms:
            # still store samples or not? typically no, keeps logic clean
            return

        # push into ring buffer
        self._ts[self._head] = now
        self._lv[self._head] = level
        self._head = (self._head + 1) % len(self._ts)
        if self._n < len(self._ts):
            self._n += 1

        if self._n < 2:
            return

        # Find the maximum level within the last delta_ms window.
        # We walk backwards from newest sample until we exit the window or exhaust samples.
        max_lv = level
        i = (self._head - 1) % len(self._ts)  # newest index
        checked = 0

        while checked < self._n:
            t = self._ts[i]
            lv = self._lv[i]

            if time.ticks_diff(now, t) > self.delta_ms:
                break

            if lv > max_lv:
                max_lv = lv

            i = (i - 1) % len(self._ts)
            checked += 1

        drop = max_lv - level
        if drop >= self.threshold_drop:
            self._last_trigger = now
            self.on_light_detected()

            # reset buffer to avoid retriggering on the same falling edge
            self._n = 0
            self._head = 0
