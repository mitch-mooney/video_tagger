# videotagger/data/settings_manager.py
import json
import os
from pathlib import Path

class SettingsManager:
    @staticmethod
    def _path() -> str:
        base = os.environ.get("APPDATA", str(Path.home()))
        d = os.path.join(base, "VideoTagger")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "settings.json")

    @classmethod
    def load(cls) -> dict:
        path = cls._path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def save(cls, data: dict) -> None:
        with open(cls._path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
