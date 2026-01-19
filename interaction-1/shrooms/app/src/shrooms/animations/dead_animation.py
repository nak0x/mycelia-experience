from .animation import Animation

import math
import time

class DeadAnimation(Animation):
    """
    Champignon à froid :
    - Tons bleus très faibles (<25)
    - Vague froide + respiration lente (pixel par pixel)
    """

    def __init__(self, shroom):
        super().__init__(shroom)
        self.t0_ms = time.ticks_ms()

        # Palette froide (toutes composantes < 25)
        self.base = (0, 4, 12)   # bleu très sombre
        self.peak = (0, 6, 18)   # bleu/cyan discret, max < 25

        # Respiration très lente
        self.period_ms = 3200

        # Onde froide qui se déplace lentement
        self.wave_speed = 0.25

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

        # Respiration globale 0..1 (très douce)
        phase = (elapsed % self.period_ms) / self.period_ms
        breath = 0.5 - 0.5 * math.cos(2 * math.pi * phase)

        for i in range(n):
            # Onde froide lente
            wave = 0.5 + 0.5 * math.sin(
                2 * math.pi * (i / n - elapsed * 0.001 * self.wave_speed)
            )

            # Mélange (plutôt wave que breath pour un rendu "froid vivant")
            t = min(1.0, max(0.0, 0.35 * breath + 0.65 * wave))

            color = self._blend(self.base, self.peak, t)
            self.shroom.display_pixel(i, color)

        self.shroom.leds.display()

    def to_lighting(self):
        from .lighting_animation import LightingAnimation
        self.shroom.update_animation(LightingAnimation(self.shroom))