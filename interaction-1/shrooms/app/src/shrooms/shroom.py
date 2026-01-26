import time
from framework.components.mcp3008 import Chanel
from framework.components.led_strip import LedStrip
from src.shrooms.animations.animation import Animation
from src.shrooms.animations.dead_animation import DeadAnimation
from src.shrooms.animations.lighting_animation import LightingAnimation
from .light_drop_detector import LightDropDetector

class Shroom:
    def __init__(self, name, chanel, leds: LedStrip, threshold_drop=50, delta_ms=150,
                 cooldown_ms=1000, buf_size=32, start=0, span=3):
        
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

        # Track max level in the current window
        self._max_level = 0
        self._max_level_time = time.ticks_ms()
        self._last_trigger = time.ticks_ms()
        
        # Setup default animation
        self.animation = None
        self.update_animation(DeadAnimation(self))

        self.detector = LightDropDetector(
            drop_trigger=self.threshold_drop,
            cooldown_ms=self.cooldown_ms,
            ema_alpha=0.35,
            baseline_alpha=0.02,
            min_drop_rate=0.0,  # mets 0.15 si tu veux éviter les dérives lentes
        )

    def update_animation(self, animation: Animation):
        print(f"{self.name}: Updating animation")
        self.animation.on_exit() if self.animation is not None else None
        self.animation = animation
        self.animation.on_enter()

    def display_pixel(self, i, color):
        self.leds.set_pixel(i + self.led_config['start_pixel'], color, show=False)

    def display_color(self, color):
        for i in range(self.led_config['start_pixel'], self.led_config['end_pixel'] + 1):
            self.leds.set_pixel(i, color, show=False)
        self.leds.display()

    @property
    def lighten(self):
        return isinstance(self.animation, LightingAnimation)
    
    def reset(self):
        # 1) Reset detector avec la valeur courante (si dispo)
        self.detector.reset()

        # 2) Forcer DeadAnimation (ne dépend pas de l’anim courante)
        self.animation.to_dead()

        # 3) petite fenêtre où on ignore les triggers (stabilisation)
        self._ignore_light_until = time.ticks_add(time.ticks_ms(), 120)

        # 4) LEDs off
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
        self.animation.to_lighting()
        print(f"{self.name}: Light detected, starting glow")

    def to_lighting(self):
        self.animation.to_lighting()

    def to_living(self):
        self.animation.to_living()

    def handle_light_level(self, level, *args):
        if self.chanel is None:
            return

        # Ignore juste après reset
        if hasattr(self, "_ignore_light_until"):
            if time.ticks_diff(time.ticks_ms(), self._ignore_light_until) < 0:
                # Important: on fait quand même tourner le detector pour qu'il se calibre
                self.detector.update(level)
                return

        # Important: même en Lighting, on nourrit le detector (sinon il "gèle")
        triggered = self.detector.update(level)

        # Mais on ne déclenche jamais pendant Lighting
        if self.lighten:
            return

        if triggered:
            self.on_light_detected()
