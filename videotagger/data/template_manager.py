import json, os
from pathlib import Path
from typing import List
from videotagger.models.project import Category, _new_id

class TemplateManager:
    @staticmethod
    def _builtin_dir() -> str:
        return str(Path(__file__).parent.parent / "resources" / "templates")

    @staticmethod
    def _user_dir() -> str:
        base = os.environ.get("APPDATA", str(Path.home()))
        d = os.path.join(base, "VideoTagger", "templates")
        os.makedirs(d, exist_ok=True)
        return d

    @staticmethod
    def _cats_from_list(raw: list) -> List[Category]:
        return [
            Category(id=_new_id(), name=c["name"], color=c["color"], labels=c["labels"])
            for c in raw
        ]

    @staticmethod
    def _cats_to_list(cats: List[Category]) -> list:
        return [{"name": c.name, "color": c.color, "labels": c.labels} for c in cats]

    @classmethod
    def list_builtin(cls) -> List[str]:
        d = cls._builtin_dir()
        return sorted(Path(f).stem for f in os.listdir(d) if f.endswith(".json"))

    @classmethod
    def load_builtin(cls, name: str) -> List[Category]:
        path = os.path.join(cls._builtin_dir(), f"{name}.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls._cats_from_list(data["categories"])

    @classmethod
    def save_user(cls, name: str, categories: List[Category]) -> None:
        path = os.path.join(cls._user_dir(), f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": name, "categories": cls._cats_to_list(categories)}, f, indent=2)

    @classmethod
    def load_user(cls, name: str) -> List[Category]:
        path = os.path.join(cls._user_dir(), f"{name}.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls._cats_from_list(data["categories"])

    @classmethod
    def list_user(cls) -> List[str]:
        d = cls._user_dir()
        return sorted(Path(f).stem for f in os.listdir(d) if f.endswith(".json"))
