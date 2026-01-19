from .animation import Animation

import math
import time

class LivingAnimation(Animation):
    """
    Chaud mais en manque d'eau :
    - Palette chaude (orange/ambre)
    - Vagues plus marquées (effet "wavy")
    - Intensité qui "retombe" régulièrement (soif)
    """

    def __init__(self, shroom):
        super().__init__(shroom)
        self.t0_ms = time.ticks_ms()

        # Chaud "ambre" (pas trop agressif)
        self.hot_base = (140, 45, 0)     # orange chaud moyen
        self.hot_peak = (255, 135, 25)   # pic chaud

        # Vagues
        self.wave_speed = 1.1     # plus wavy que Lighting
        self.wave_count = 2.2     # nombre de vagues visibles sur le strip

        # Cycle "soif" : baisse globale lente puis remonte
        self.thirst_period_ms = 4200

        # Et une respiration plus rapide (micro-vie)
        self.pulse_period_ms = 1700

    def _lerp(self, a, b, t):
        return int(a + (b - a) * t)

    def _blend(self, c1, c2, t):
        return (
            self._lerp(c1[0], c2[0], t),
            self._lerp(c1[1], c2[1], t),
            self._lerp(c1[2], c2[2], t),
        )

    def _clamp01(self, x):
        return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

    def handle(self):
        n = self.shroom.led_config["span"]

        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self.t0_ms)
        t = elapsed / 1000.0

        # Pulse 0..1 (petit "vivant")
        p_phase = (elapsed % self.pulse_period_ms) / self.pulse_period_ms
        pulse = 0.5 - 0.5 * math.cos(2 * math.pi * p_phase)

        # Thirst 0..1..0 (plus = mieux hydraté)
        th_phase = (elapsed % self.thirst_period_ms) / self.thirst_period_ms
        thirst = 0.5 - 0.5 * math.cos(2 * math.pi * th_phase)

        # On transforme "soif" en "affaiblissement" :
        # quand thirst est bas => on diminue l'intensité globale
        # (reste chaud, mais plus terne)
        global_dim = 0.55 + 0.45 * thirst   # entre ~0.55 et 1.0

        for i in range(n):
            x = i / max(1, (n - 1))

            # Vague principale (plus marquée)
            wave1 = 0.5 + 0.5 * math.sin(2 * math.pi * (self.wave_count * x - self.wave_speed * t))

            # Petite seconde vague (décalée) pour l'effet organique
            wave2 = 0.5 + 0.5 * math.sin(2 * math.pi * ((self.wave_count * 0.6) * x - (self.wave_speed * 1.6) * t + 0.25))

            # Mix wavy + pulse
            wavy = 0.65 * wave1 + 0.35 * wave2
            mix = self._clamp01(0.55 * wavy + 0.45 * pulse)

            # Couleur chaude "vivante"
            r, g, b = self._blend(self.hot_base, self.hot_peak, mix)

            # Applique l'affaiblissement (soif)
            r = int(r * global_dim)
            g = int(g * global_dim)
            b = int(b * global_dim)

            self.shroom.display_pixel(i, (r, g, b))

        self.shroom.leds.display()

    def to_dead(self):
        from .dead_animation import DeadAnimation
        self.shroom.update_animation(DeadAnimation(self.shroom))