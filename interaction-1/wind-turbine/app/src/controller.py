from framework.controller import Controller
from framework.components.microphone import Microphone
from framework.utils.ws.interface import WebsocketInterface
from framework.components.led_strip import LedStrip
from framework.app import App
import time


class WindTurbineController(Controller):

    MAX_LEVEL = 5

    def setup(self):
        # ===== CONFIG =====
        self.min_level = 25      # bruit minimum ignoré (à calibrer)
        self.max_level = 120     # niveau sonore pour atteindre 5 LEDs
        self.trigger_cooldown_ms = 1500  # anti retrigger websocket

        # 0.5..0.8 recommandé (plus petit = encore + facile au début)
        self.curve_gamma = 0.99

        # Anti-clignotement (hystérésis) exprimé en % de la "zone"
        # 0.10 = 10% de marge pour changer de niveau
        self.sensitivity = 0.12

        # ===== STATE =====
        self.level = 0
        self.last_trigger = 0

        # ===== LED STRIP =====
        self.strip = LedStrip(
            pin=17,
            pixel_num=11,
            default_color=(10, 10, 10)
        )
        self.strip.clear()
        self.strip.display()

        # ===== MICROPHONE =====
        Microphone(
            pin=32,
            on_level=self.on_mic_level,
            debug=False
        )

        if App().config.debug:
            print("[WindTurbine] Controller setup done")

    # ===============================
    # MICROPHONE CALLBACK
    # ===============================
    def on_mic_level(self, mic_level: int, raw: int, baseline: int):
        if App().config.debug:
            print(f"[WindTurbine] mic_level={mic_level} raw={raw} baseline={baseline}")

        # Niveau "cible" selon mapping non linéaire
        target = self.map_to_5_levels_curve(mic_level)

        # Applique une hystérésis pour éviter le clignotement
        new_level = self.apply_hysteresis(mic_level, target)

        if new_level != self.level:
            if App().config.debug:
                print(f"[WindTurbine] level changed {self.level} → {new_level}")

            self.level = new_level
            self.render_level()

        if self.level == self.MAX_LEVEL:
            self.try_trigger()

    # ===============================
    # NON-LINEAR LEVEL MAPPING (EXP)
    # ===============================
    def map_to_5_levels_curve(self, mic_level: int) -> int:
        if mic_level <= self.min_level:
            return 0
        if mic_level >= self.max_level:
            return self.MAX_LEVEL

        span = self.max_level - self.min_level
        x = (mic_level - self.min_level) / span  # 0..1

        # gamma < 1 => facile au début, dur à la fin
        y = x ** self.curve_gamma

        mapped = 1 + int(y * (self.MAX_LEVEL - 1))

        if App().config.debug:
            print(f"[WindTurbine] mapped(curve) level={mapped} (x={x:.2f}, y={y:.2f})")

        return mapped

    # ===============================
    # HYSTERESIS (ANTI-FLICKER)
    # ===============================
    def apply_hysteresis(self, mic_level: int, target_level: int) -> int:
        current = self.level

        if current == 0:
            return target_level

        span = self.max_level - self.min_level
        margin = span * self.sensitivity

        # Séparation des niveaux en "y" puis conversion inverse vers "x"
        # y = x^gamma  => x = y^(1/gamma)
        def level_threshold(level_int: int) -> float:
            y = (level_int - 1) / (self.MAX_LEVEL - 1)  # 0..1
            x = y ** (1.0 / self.curve_gamma) if y > 0 else 0.0
            return self.min_level + x * span

        if target_level > current:
            next_level = min(current + 1, self.MAX_LEVEL)
            up_threshold = level_threshold(next_level) + margin
            if App().config.debug:
                print(f"[WindTurbine] hysteresis UP: mic={mic_level} need>{int(up_threshold)}")
            return next_level if mic_level > up_threshold else current

        if target_level < current:
            down_threshold = level_threshold(current) - margin
            if App().config.debug:
                print(f"[WindTurbine] hysteresis DOWN: mic={mic_level} need<{int(down_threshold)}")
            return max(current - 1, 0) if mic_level < down_threshold else current

        return current

    # ===============================
    # LED RENDER
    # ===============================
    def render_level(self):
        if App().config.debug:
            print(f"[WindTurbine] render {self.level} LED(s)")

        self.strip.clear()
        for i in range(self.level):
            index = self.strip.pixel_num - i
            self.strip.set_pixel(index)
        self.strip.display()

    # ===============================
    # ACTION
    # ===============================
    def try_trigger(self):
        now = time.ticks_ms()

        if time.ticks_diff(now, self.last_trigger) < self.trigger_cooldown_ms:
            if App().config.debug:
                print("[WindTurbine] trigger ignored (cooldown)")
            return

        self.last_trigger = now

        if App().config.debug:
            print("[WindTurbine] 🔥 LEVEL 5 reached → trigger wind")

        WebsocketInterface().send_value("01-wind-toggle", True)

        # Reset visuel après déclenchement
        self.level = 0
        self.render_level()