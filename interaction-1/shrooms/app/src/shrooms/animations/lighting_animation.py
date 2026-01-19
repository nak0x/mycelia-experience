from .animation import Animation

import math
import time

class LightingAnimation(Animation):
    """
    Champignon chauffé :
    - Tons chauds (orange / jaune)
    - Luminosité vive
    - Pulsation + légère onde de chaleur
    """

    def __init__(self, shroom):
        super().__init__(shroom)
        self.t0_ms = time.ticks_ms()

        # Couleurs chaudes
        self.base = (180, 60, 0)     # orange chaud
        self.peak = (255, 140, 30)   # jaune/orange vif

        # Vitesse de pulsation
        self.period_ms = 1800

        # Vitesse de propagation de l’onde
        self.wave_speed = 0.6

    def _lerp(self, a, b, t):
        return int(a + (b - a) * t)

    def _blend(self, c1, c2, t):
        return (
            self._lerp(c1[0], c2[0], t),
            self._lerp(c1[1], c2[1], t),
            self._lerp(c1[2], c2[2], t),
        )

    def handle(self):
        n = self.shroom.led_config["span"]

        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self.t0_ms)

        # Pulsation globale 0..1
        phase = (elapsed % self.period_ms) / self.period_ms
        pulse = 0.5 - 0.5 * math.cos(2 * math.pi * phase)

        for i in range(n):
            # Onde de chaleur qui se déplace
            wave = 0.5 + 0.5 * math.sin(
                2 * math.pi * (i / n - elapsed * 0.001 * self.wave_speed)
            )

            # Mélange pulsation + onde
            t = min(1.0, max(0.0, 0.6 * pulse + 0.4 * wave))

            color = self._blend(self.base, self.peak, t)
            self.shroom.display_pixel(i, color)

        self.shroom.leds.display()

    def to_dead(self):
        from .dead_animation import DeadAnimation
        self.shroom.update_animation(DeadAnimation(self.shroom))

    def to_living(self):
        from .living_animation import LivingAnimation
        self.shroom.update_animation(LivingAnimation(self.shroom))