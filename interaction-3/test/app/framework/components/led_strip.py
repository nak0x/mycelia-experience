from framework.app import App
from machine import Pin
from neopixel import NeoPixel
from framework.utils.frames.frame import Frame

def scale_rgb_for_power(
    max_current_a: float,
    led_count: int,
    rgb: tuple
) -> tuple:
    """
    Returns a power-safe RGB tuple for WS2812/NeoPixel LEDs.

    Assumptions:
    - 20 mA per color channel at 255
    - Linear current scaling
    - All LEDs show the same color
    """

    r, g, b = rgb

    # Current per LED for requested color
    current_per_led = (
        (r / 255.0) * 0.02 +
        (g / 255.0) * 0.02 +
        (b / 255.0) * 0.02
    )

    if current_per_led == 0:
        return (0, 0, 0)

    total_current = current_per_led * led_count

    if total_current <= max_current_a:
        return rgb  # already safe

    scale = max_current_a / total_current

    return (
        int(r * scale),
        int(g * scale),
        int(b * scale),
    )


class LedStrip:
    def __init__(self, pin, pixel_num, max_current=2, default_color=(255, 255, 255)):
        self.pixel_num = pixel_num
        self.np = NeoPixel(Pin(pin), pixel_num)
        self.max_current = max_current
        self.default_color = scale_rgb_for_power(max_current, pixel_num, default_color)

        self.pixels = [(0, 0, 0)] * pixel_num
        self.display()

    def scale_color(self, color):
        return scale_rgb_for_power(self.max_current, len(self.pixels), color) if color is not None else None

    def display(self):
        for i, c in enumerate(self.pixels):
            self.np[i] = c
        self.np.write()

    def fill(self, color=None):
        for i in range(len(self.pixels)):
            self.pixels[i] = self.scale_color(color) or self.default_color

    def clear(self):
        self.fill((0, 0, 0))

    def on(self, color=None):
        self.fill(color)
        self.display()

    def off(self):
        self.clear()
        self.display()

    def set_pixel(self, i, color=None, show=False):
        if 0 <= i < len(self.pixels):
            self.pixels[i] = self.scale_color(color) or self.default_color
            if show:
                self.display()

    def _last_index_of_color(self, color=None):
        for i in range(len(self.pixels) - 1, -1, -1):
            if self.pixels[i] == (self.scale_color(color) or self.default_color):
                return i
        return None
    
    def next_pixel(self, color=None, show=False):
        last = self._last_index_of_color(color)

        i = 0 if last is None else min(last + 1, len(self.pixels) - 1)
        self.set_pixel(i, color)

        if show:
            self.display()
        return i

    def previous_pixel(self, color=None, show=False):
        last = self._last_index_of_color(color)
        
        i = (len(self.pixels) - 1) if last is None else max(last - 1, 0)
        self.set_pixel(i, color)

        if show:
            self.display()
        return i
