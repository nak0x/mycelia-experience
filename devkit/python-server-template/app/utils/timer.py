import threading
import time
from typing import Callable, Optional


class Timer:
    """
    Timer 'Python natif' (standard library) basé sur threading.Timer.

    - duration_ms : durée en millisecondes
    - on_timeout  : callback appelé à l'expiration
    - autostart   : démarre immédiatement si True

    Méthodes proches de ta version:
    - start()   : reset + play
    - reset()   : remet le start_time à maintenant
    - play()    : (re)arme le timer si pas déjà en cours
    - stop()    : stoppe (désarme) sans effacer start_time
    - restart() : alias de start()
    - quit()    : stop + nettoyage interne
    """

    def __init__(self, duration_ms: int, on_timeout: Callable[[], None], autostart: bool = False):
        self.duration_ms = int(duration_ms)
        self.on_timeout = on_timeout

        self.start_time: Optional[float] = None  # time.monotonic() en secondes
        self.running = False

        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

        if autostart:
            self.start()

    @property
    def started(self) -> bool:
        return self.start_time is not None

    def _cancel_internal(self) -> None:
        """Annule le threading.Timer si présent."""
        if self._timer is not None:
            try:
                self._timer.cancel()
            except Exception:
                pass
            self._timer = None

    def start(self) -> None:
        self.reset()
        self.play()

    def reset(self) -> None:
        with self._lock:
            self.start_time = time.monotonic()

    def play(self) -> None:
        with self._lock:
            if self.running:
                return

            if self.start_time is None:
                self.start_time = time.monotonic()

            self.running = True

            # Calcule le temps restant (si on relance après un stop)
            elapsed_ms = int((time.monotonic() - self.start_time) * 1000)
            remaining_ms = max(0, self.duration_ms - elapsed_ms)

            self._cancel_internal()
            self._timer = threading.Timer(remaining_ms / 1000.0, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def stop(self) -> None:
        with self._lock:
            self.running = False
            self._cancel_internal()

    def restart(self) -> None:
        self.start()

    def quit(self) -> None:
        # stop + nettoyage d'état
        with self._lock:
            self.running = False
            self._cancel_internal()

    def _fire(self) -> None:
        # Important: désarmer avant callback (comme ton commentaire)
        with self._lock:
            if not self.running:
                return
            self.running = False
            self._timer = None

        try:
            self.on_timeout()
        except Exception as e:
            print("Timer on_timeout error:", e)