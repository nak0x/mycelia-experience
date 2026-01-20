import time

class LightDropDetector:
    def __init__(
        self,
        drop_trigger=50,
        drop_release=None,
        cooldown_ms=1000,
        ema_alpha=0.35,
        baseline_alpha=0.02,
        min_drop_rate=0.0,
        init_samples=4,           # NEW: warmup samples
    ):
        self.drop_trigger = int(drop_trigger)
        self.drop_release = int(drop_release) if drop_release is not None else int(self.drop_trigger * 0.4)
        self.cooldown_ms = int(cooldown_ms)

        self.ema_alpha = float(ema_alpha)
        self.baseline_alpha = float(baseline_alpha)
        self.min_drop_rate = float(min_drop_rate)

        self.init_samples = int(init_samples)
        self.reset()

    def reset(self):
        now = time.ticks_ms()
        self._armed = True
        self.last_drop = 0.0
        self.last_drop_rate = 0.0

        self._ema = None
        self._baseline = None
        self._last_ema = None

        self._last_time = now
        self._last_trigger = now

    def update(self, level, now_ms=None):
        if now_ms is None:
            now_ms = time.ticks_ms()

        # Init si nécessaire
        if self._ema is None:
            v = float(level)
            self._ema = v
            self._baseline = v
            self._last_ema = v
            self._last_time = now_ms
            self._warmup_left = self.init_samples
            return False

        # Warmup: on stabilise sans détecter
        if self._warmup_left > 0:
            # On fait avancer EMA/Baseline mais on n'autorise pas la détection
            dt = time.ticks_diff(now_ms, self._last_time)
            if dt <= 0:
                dt = 1

            x = float(level)
            self._ema = self._ema + self.ema_alpha * (x - self._ema)

            if self._ema > self._baseline:
                self._baseline = self._baseline + self.baseline_alpha * (self._ema - self._baseline)
            else:
                self._baseline = self._baseline + (self.baseline_alpha * 0.25) * (self._ema - self._baseline)

            self._last_ema = self._ema
            self._last_time = now_ms
            self._warmup_left -= 1
            return False

        dt = time.ticks_diff(now_ms, self._last_time)
        if dt <= 0:
            dt = 1

        x = float(level)
        self._ema = self._ema + self.ema_alpha * (x - self._ema)

        if self._ema > self._baseline:
            self._baseline = self._baseline + self.baseline_alpha * (self._ema - self._baseline)
        else:
            self._baseline = self._baseline + (self.baseline_alpha * 0.25) * (self._ema - self._baseline)

        drop = self._baseline - self._ema
        d_ema = self._last_ema - self._ema
        drop_rate = d_ema / dt

        self.last_drop = drop
        self.last_drop_rate = drop_rate

        self._last_ema = self._ema
        self._last_time = now_ms

        if time.ticks_diff(now_ms, self._last_trigger) < self.cooldown_ms:
            return False

        if self._armed:
            if drop >= self.drop_trigger:
                if self.min_drop_rate > 0.0 and drop_rate < self.min_drop_rate:
                    return False
                self._armed = False
                self._last_trigger = now_ms
                return True
        else:
            if drop <= self.drop_release:
                self._armed = True

        return False