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
        # DEBUG
        # =====================================================
        self.debug_progress = True       # <- mets False pour couper
        self.debug_every_ms = 120        # log ~8 fois/sec
        self._last_debug_ms = 0

        # =====================================================
        # EXPERIENCE STATE (one-shot trigger)
        # =====================================================
        self.completed = False  # si True: plus de leds + plus de trigger

        # =====================================================
        # MICROPHONE TUNING
        # =====================================================
        self.min_level = 20

        self.mic_attack = 0.25
        self.mic_release = 0.85

        self.mic_alpha_base = 0.01
        self.mic_gate_ratio = 0.45
        self.mic_gate_offset = 2.0

        # =====================================================
        # AUTO CALIBRATION (ROBUST PEAK TRACKING)
        # =====================================================
        self.peak_cap = 200
        self.peak_min = 80
        self.peak_margin = 1.08
        self.peak_decay = 0.995

        self.observed_peak = float(self.peak_min)

        # =====================================================
        # FEELING PROGRESSION (rampe + courbe)
        # =====================================================
        self.progress = 0.0
        self.progress_up = 0.22
        self.progress_down = 0.20

        self.curve_gamma = 0.25

        self.level_hyst = 0.05
        self.full_on_progress = 0.80

        # =====================================================
        # TRIGGER
        # =====================================================
        self.trigger_cooldown_ms = 1500
        self.trigger_hold_ms = 0
        self._full_since_ms = None

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
    # WEBSOCKET FRAME RECEIVED (RESET)
    # =====================================================
    def on_frame_received(self, frame):
        if frame.action == "01-reset":
            self._reset()

    # =====================================================
    # RESET EXPERIENCE
    # =====================================================
    def _reset(self):
        # Réactive l'expérience
        self.completed = False

        # Reset visuel + progression
        self.progress = 0.0
        self.level = 0
        self._full_since_ms = None
        self.last_trigger = 0

        # Reset auto-calibration
        self.observed_peak = float(self.peak_min)

        # Reset debug throttle
        self._last_debug_ms = 0

        self.strip.clear()
        self.strip.display()

        if App().config.debug:
            print("[WindTurbine] ✅ Reset done")

    # =====================================================
    # MICROPHONE CALLBACK
    # =====================================================
    def on_mic_level(self, mic_level: int, raw: int, baseline: int):
        # Si l'expérience est terminée: on ignore tout et on garde LEDs off
        if self.completed:
            return

        # ---------------------------
        # 1) ROBUST PEAK UPDATE (cap outliers)
        # ---------------------------
        if mic_level > self.min_level:
            mic_clip = mic_level if mic_level < self.peak_cap else self.peak_cap

            if mic_clip > self.observed_peak:
                self.observed_peak = float(mic_clip)
            else:
                self.observed_peak *= self.peak_decay

        if self.observed_peak < self.peak_min:
            self.observed_peak = float(self.peak_min)

        dyn_max = self.observed_peak * self.peak_margin

        # ---------------------------
        # 2) Normalize 0..1 using dyn_max
        # ---------------------------
        span = dyn_max - self.min_level
        if span <= 1:
            return

        x = (mic_level - self.min_level) / span
        if x < 0.0:
            x = 0.0
        elif x > 1.0:
            x = 1.0

        # ---------------------------
        # 3) Ease curve
        # ---------------------------
        x_eased = x ** self.curve_gamma

        # ---------------------------
        # 4) Slew-rate smoothing (rampe)
        # ---------------------------
        a = self.progress_up if x_eased > self.progress else self.progress_down
        self.progress = (1 - a) * self.progress + a * x_eased

        # ---------------------------
        # 5) Progress -> target level (robuste)
        # ---------------------------
        if self.progress >= self.full_on_progress:
            target_level = self.MAX_LEVEL
        else:
            target_level = int(self.progress * self.MAX_LEVEL + 0.5)
            if target_level < 0:
                target_level = 0
            if target_level > self.MAX_LEVEL:
                target_level = self.MAX_LEVEL

        # ---------------------------
        # 6) Anti-flicker hysteresis (fixed)
        # ---------------------------
        new_level = self.apply_level_hysteresis(self.progress, target_level)

        if new_level != self.level:
            self.level = new_level
            self.render_level()

        # Si on atteint 5 visuellement, on trigger immédiatement
        if self.level == self.MAX_LEVEL:
            self.try_trigger()
            return

        # ---------------------------
        # 7) DEBUG THROTTLED + BAR
        # ---------------------------
        self.debug_log(mic_level, raw, baseline, dyn_max, x, x_eased, a)

        # ---------------------------
        # 8) Trigger hold
        # ---------------------------
        self.handle_trigger_hold()

    # =====================================================
    # DEBUG LOG
    # =====================================================
    def debug_log(self, mic_level, raw, baseline, dyn_max, x, x_eased, a):
        if not self.debug_progress:
            return

        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_debug_ms) < self.debug_every_ms:
            return
        self._last_debug_ms = now

        width = 20
        filled = int(self.progress * width)
        if filled < 0:
            filled = 0
        if filled > width:
            filled = width
        bar = "[" + ("#" * filled) + ("-" * (width - filled)) + "]"

        print(
            f"[WindTurbineDBG] mic={mic_level:3d} raw={raw:4d} base={baseline:4d} "
            f"peak={int(self.observed_peak):3d} dyn={int(dyn_max):3d} "
            f"x={x:0.2f} eased={x_eased:0.2f} a={a:0.2f} "
            f"prog={self.progress:0.2f} lvl={self.level} {bar}"
        )

    # =====================================================
    # LEVEL HYSTERESIS (ANTI-FLICKER) - FIXED
    # =====================================================
    def apply_level_hysteresis(self, p: float, target_level: int) -> int:
        current = self.level

        # Force le niveau 5 quand on dépasse le seuil full
        if p >= self.full_on_progress:
            return self.MAX_LEVEL

        if target_level == current:
            return current

        # seuils "milieu" entre niveaux: 0.1,0.3,0.5,0.7,0.9
        def mid_threshold(level_int: int) -> float:
            return (level_int - 0.5) / self.MAX_LEVEL

        if target_level > current:
            next_level = min(current + 1, self.MAX_LEVEL)
            need = mid_threshold(next_level) + self.level_hyst
            return next_level if p >= need else current

        if target_level < current:
            need = mid_threshold(current) - self.level_hyst
            return current - 1 if p <= need else current

        return current

    # =====================================================
    # LED RENDER
    # =====================================================
    def render_level(self):
        # Si terminé, LEDs éteintes
        if self.completed:
            self.strip.clear()
            self.strip.display()
            return

        self.strip.clear()
        for i in range(self.level):
            index = i + 6
            self.strip.set_pixel(index)
        self.strip.display()

    # =====================================================
    # TRIGGER HOLD
    # =====================================================
    def handle_trigger_hold(self):
        now = time.ticks_ms()

        if self.level == self.MAX_LEVEL:
            if self._full_since_ms is None:
                self._full_since_ms = now

            if time.ticks_diff(now, self._full_since_ms) >= self.trigger_hold_ms:
                self.try_trigger()
                self._full_since_ms = None
        else:
            self._full_since_ms = None

    # =====================================================
    # ACTION
    # =====================================================
    def try_trigger(self):
        # One-shot: si déjà terminé, on ne fait rien
        if self.completed:
            return

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_trigger) < self.trigger_cooldown_ms:
            return

        self.last_trigger = now

        if App().config.debug:
            print("[WindTurbine] 🌬️ FULL CHARGE → WIND TRIGGER (ONE-SHOT)")

        WebsocketInterface().send_value("01-wind-toggle", True)

        # Marque l'expérience comme terminée + coupe les LEDs
        self.completed = True
        self.progress = 0.0
        self.level = 0
        self.strip.clear()
        self.strip.display()