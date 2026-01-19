import time

class LightDropDetector:
    """
    Détecte un "drop" de lumière robuste (ombre/coupure) via :
    - EMA (lissage)
    - baseline adaptative (suivi lent de l'ambiance)
    - drop = baseline - ema
    - hystérésis (arm/disarm) pour éviter double-trigger
    - cooldown
    - optionnel: min_drop_rate (anti dérive lente)

    Usage:
        det = LightDropDetector(...)
        if det.update(level):
            # event detected
    """

    def __init__(
        self,
        drop_trigger=50,
        drop_release=None,
        cooldown_ms=1000,
        ema_alpha=0.35,
        baseline_alpha=0.02,
        min_drop_rate=0.0,
    ):
        self.drop_trigger = int(drop_trigger)
        self.drop_release = int(drop_release) if drop_release is not None else int(self.drop_trigger * 0.4)
        self.cooldown_ms = int(cooldown_ms)

        self.ema_alpha = float(ema_alpha)
        self.baseline_alpha = float(baseline_alpha)
        self.min_drop_rate = float(min_drop_rate)

        self.reset()

    def reset(self, level=None):
        now = time.ticks_ms()
        self._ema = float(level) if level is not None else None
        self._baseline = float(level) if level is not None else None
        self._armed = True

        self._last_trigger = now
        self._last_ema = float(level) if level is not None else None
        self._last_time = now

        self.last_drop = 0.0
        self.last_drop_rate = 0.0

    @property
    def armed(self):
        return self._armed

    @property
    def ema(self):
        return self._ema

    @property
    def baseline(self):
        return self._baseline

    def update(self, level, now_ms=None):
        """
        Retourne True si un événement (drop) est détecté.
        Met à jour aussi:
          - self.last_drop
          - self.last_drop_rate
        """
        if now_ms is None:
            now_ms = time.ticks_ms()

        # Init au premier échantillon
        if self._ema is None:
            self._ema = float(level)
            self._baseline = float(level)
            self._last_ema = self._ema
            self._last_time = now_ms
            return False

        dt = time.ticks_diff(now_ms, self._last_time)
        if dt <= 0:
            dt = 1

        # 1) EMA
        x = float(level)
        self._ema = self._ema + self.ema_alpha * (x - self._ema)

        # 2) Baseline adaptative (monte plus vite que ça ne descend)
        if self._ema > self._baseline:
            self._baseline = self._baseline + self.baseline_alpha * (self._ema - self._baseline)
        else:
            self._baseline = self._baseline + (self.baseline_alpha * 0.25) * (self._ema - self._baseline)

        # 3) drop et vitesse
        drop = self._baseline - self._ema  # >0 si ça baisse
        d_ema = self._last_ema - self._ema
        drop_rate = d_ema / dt  # unités/ms (approx)
        self.last_drop = drop
        self.last_drop_rate = drop_rate

        self._last_ema = self._ema
        self._last_time = now_ms

        # 4) cooldown
        if time.ticks_diff(now_ms, self._last_trigger) < self.cooldown_ms:
            return False

        # 5) hystérésis
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