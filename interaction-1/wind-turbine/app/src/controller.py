from framework.controller import Controller
from framework.components.microphone import Microphone
from framework.utils.ws.interface import WebsocketInterface
from framework.components.led_strip import LedStrip
from framework.app import App
import time


class WindTurbineController(Controller):

    MAX_LEVEL = 5

    def setup(self):
        # =====================================================
        # 🎚️ MICROPHONE TUNING (EXPO CRITIQUE)
        # =====================================================

        # Niveau sonore (enveloppe)
        self.min_level = 10       # bruit minimum ignoré
        self.max_level = 50       # souffle fort → LED 5

        # Envelope dynamics
        self.mic_attack = 0.35    # montée rapide
        self.mic_release = 0.80   # descente rapide (extinction LEDs)

        # Baseline behavior (anti "souffle long qui s'annule")
        self.mic_alpha_base = 0.01   # vitesse de drift quand calme
        self.mic_gate_ratio = 0.45   # plus bas = baseline gelée plus tôt
        self.mic_gate_offset = 2.0   # marge absolue ADC

        # =====================================================
        # 🎚️ LED / MAPPING
        # =====================================================

        # Courbe convexe : facile au début, dur à la fin
        self.threshold_power = 2.0

        # Hystérésis (stabilité visuelle)
        self.hyst_up = 7
        self.hyst_down = 10

        # Trigger websocket
        self.trigger_cooldown_ms = 1500

        # =====================================================
        # STATE
        # =====================================================
        self.level = 0
        self.last_trigger = 0

        # =====================================================
        # LED STRIP
        # =====================================================
        self.strip = LedStrip(
            pin=17,
            pixel_num=11,
            default_color=(10, 10, 10)
        )
        self.strip.clear()
        self.strip.display()

        # =====================================================
        # BUILD THRESHOLDS
        # =====================================================
        self.thresholds = self.build_thresholds()

        if App().config.debug:
            print("[WindTurbine] thresholds:", [int(t) for t in self.thresholds])

        # =====================================================
        # MICROPHONE
        # =====================================================
        Microphone(
            pin=32,
            on_level=self.on_mic_level,

            # envelope
            attack=self.mic_attack,
            release=self.mic_release,

            # baseline
            alpha_base=self.mic_alpha_base,
            gate_ratio=self.mic_gate_ratio,
            gate_offset=self.mic_gate_offset,

            debug=False
        )

        if App().config.debug:
            print("[WindTurbine] Controller setup done")

    # =====================================================
    # BUILD NON-LINEAR THRESHOLDS
    # =====================================================
    def build_thresholds(self):
        span = self.max_level - self.min_level
        thresholds = []

        for i in range(1, self.MAX_LEVEL + 1):
            t = self.min_level + span * ((i / self.MAX_LEVEL) ** self.threshold_power)
            thresholds.append(t)

        return thresholds

    # =====================================================
    # MICROPHONE CALLBACK
    # =====================================================
    def on_mic_level(self, mic_level: int, raw: int, baseline: int):
        if App().config.debug:
            print(f"[WindTurbine] mic={mic_level} raw={raw} base={baseline}")

        target = self.map_to_5_levels(mic_level)
        new_level = self.apply_hysteresis(mic_level, target)

        if new_level != self.level:
            self.level = new_level
            self.render_level()

        if self.level == self.MAX_LEVEL:
            self.try_trigger()

    # =====================================================
    # LEVEL MAPPING (THRESHOLDS)
    # =====================================================
    def map_to_5_levels(self, mic_level: int) -> int:
        if mic_level <= self.min_level:
            return 0

        level = 0
        for i, thr in enumerate(self.thresholds, start=1):
            if mic_level >= thr:
                level = i

        return level

    # =====================================================
    # HYSTERESIS (ANTI-FLICKER)
    # =====================================================
    def apply_hysteresis(self, mic_level: int, target_level: int) -> int:
        current = self.level

        # Entrée depuis 0
        if current == 0:
            return 1 if mic_level >= (self.thresholds[0] + self.hyst_up) else 0

        # Montée
        if target_level > current:
            next_level = min(current + 1, self.MAX_LEVEL)
            thr_up = self.thresholds[next_level - 1] + self.hyst_up
            return next_level if mic_level >= thr_up else current

        # Descente
        if target_level < current:
            thr_down = self.thresholds[current - 1] - self.hyst_down
            return current - 1 if mic_level <= thr_down else current

        return current

    # =====================================================
    # LED RENDER
    # =====================================================
    def render_level(self):
        self.strip.clear()

        for i in range(self.level):
            index = i + 6
            self.strip.set_pixel(index)

        self.strip.display()

    # =====================================================
    # ACTION
    # =====================================================
    def try_trigger(self):
        now = time.ticks_ms()

        if time.ticks_diff(now, self.last_trigger) < self.trigger_cooldown_ms:
            return

        self.last_trigger = now

        if App().config.debug:
            print("[WindTurbine] 🌬️ LEVEL 5 → WIND TRIGGER")

        WebsocketInterface().send_value("01-wind-toggle", True)

        # Reset visuel
        self.level = 0
        self.render_level()