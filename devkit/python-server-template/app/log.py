from __future__ import annotations

import os
from datetime import datetime
from threading import RLock
from typing import Iterable, List, Optional


class Logger:
    """
    Logger par clé, stocké dans un fichier texte.
    Format :
    [YYYY-MM-DD HH:MM:SS] : [key] => message
    """

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self._lock = RLock()
        self._ensure_file_exists()

    # --- Écrire un log ---
    def log(self, key: str, message: str) -> None:
        key = self._validate_key(key)
        message = self._validate_message(message)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] : [{key}] => {message}\n"

        with self._lock:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(line)

    # --- Récupérer les logs ---
    def get_logs(
        self,
        key: Optional[str] = None,
        limit: Optional[int] = None,
        desc: bool = False,
    ) -> List[str]:
        """
        - key   : filtre par clé (None = toutes)
        - limit : nombre max de logs (None = tous)
        - desc  : True = ordre inverse (dernier en premier)
        """

        if key is not None:
            key = self._validate_key(key)

        if desc:
            return self._get_logs_desc(key, limit)

        logs: List[str] = []
        for line in self._iter_logs_asc():
            if key and f"] : [{key}] =>" not in line:
                continue

            logs.append(line)
            if limit is not None and len(logs) >= limit:
                break

        return logs

    # --- Lecture ascendante (streaming) ---
    def _iter_logs_asc(self) -> Iterable[str]:
        with self._lock:
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line:
                        yield line

    # --- Lecture descendante (RAM maîtrisée) ---
    def _get_logs_desc(
        self,
        key: Optional[str],
        limit: Optional[int],
    ) -> List[str]:
        """
        Lecture depuis la fin du fichier.
        Ne charge pas tout le fichier en mémoire.
        """
        results: List[str] = []

        with self._lock:
            with open(self.filepath, "rb") as f:
                f.seek(0, os.SEEK_END)
                buffer = b""
                pos = f.tell()

                while pos > 0:
                    read_size = min(4096, pos)
                    pos -= read_size
                    f.seek(pos)
                    chunk = f.read(read_size)
                    buffer = chunk + buffer

                    lines = buffer.split(b"\n")
                    buffer = lines[0]

                    for raw in reversed(lines[1:]):
                        try:
                            line = raw.decode("utf-8")
                        except UnicodeDecodeError:
                            continue

                        if not line:
                            continue
                        if key and f"] : [{key}] =>" not in line:
                            continue

                        results.append(line)
                        if limit is not None and len(results) >= limit:
                            return results

                # première ligne du fichier
                if buffer:
                    try:
                        line = buffer.decode("utf-8")
                        if not key or f"] : [{key}] =>" in line:
                            results.append(line)
                    except UnicodeDecodeError:
                        pass

        return results

    # --- Internes ---
    def _ensure_file_exists(self) -> None:
        folder = os.path.dirname(os.path.abspath(self.filepath))
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8"):
                pass

    @staticmethod
    def _validate_key(key: str) -> str:
        if not isinstance(key, str):
            raise TypeError("key doit être une chaîne.")
        key = key.strip()
        if not key:
            raise ValueError("key ne peut pas être vide.")
        return key

    @staticmethod
    def _validate_message(message: str) -> str:
        if not isinstance(message, str):
            raise TypeError("message doit être une chaîne.")

        # Retire tous les retours à la ligne (et évite les doubles espaces)
        message = message.replace("\r\n", "\n").replace("\r", "\n")
        message = " ".join(message.splitlines())  # join avec espace
        message = " ".join(message.split())       # compacte les espaces / tabs
        message = message.strip()

        if not message:
            raise ValueError("message ne peut pas être vide.")
        return message