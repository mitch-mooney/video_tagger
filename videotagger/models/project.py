import uuid
from dataclasses import dataclass, field
from typing import List

def _new_id() -> str:
    return str(uuid.uuid4())

@dataclass
class Category:
    name: str
    color: str
    labels: List[str] = field(default_factory=list)
    id: str = field(default_factory=_new_id)

@dataclass
class Clip:
    category_id: str
    label: str
    start: float
    end: float
    notes: str = ""
    id: str = field(default_factory=_new_id)

@dataclass
class Playlist:
    name: str
    clip_ids: List[str] = field(default_factory=list)
    id: str = field(default_factory=_new_id)

@dataclass
class Project:
    video_path: str
    categories: List[Category] = field(default_factory=list)
    clips: List[Clip] = field(default_factory=list)
    playlists: List[Playlist] = field(default_factory=list)
    version: int = 1

def project_to_dict(proj: Project) -> dict:
    return {
        "version": proj.version,
        "video_path": proj.video_path,
        "categories": [
            {"id": c.id, "name": c.name, "color": c.color, "labels": c.labels}
            for c in proj.categories
        ],
        "clips": [
            {"id": c.id, "category_id": c.category_id, "label": c.label,
             "start": c.start, "end": c.end, "notes": c.notes}
            for c in proj.clips
        ],
        "playlists": [
            {"id": p.id, "name": p.name, "clip_ids": p.clip_ids}
            for p in proj.playlists
        ],
    }

def project_from_dict(d: dict) -> Project:
    categories = [
        Category(id=c["id"], name=c["name"], color=c["color"], labels=c["labels"])
        for c in d.get("categories", [])
    ]
    clips = [
        Clip(id=c["id"], category_id=c["category_id"], label=c["label"],
             start=c["start"], end=c["end"], notes=c.get("notes", ""))
        for c in d.get("clips", [])
    ]
    playlists = [
        Playlist(id=p["id"], name=p["name"], clip_ids=p["clip_ids"])
        for p in d.get("playlists", [])
    ]
    return Project(
        version=d.get("version", 1),
        video_path=d["video_path"],
        categories=categories,
        clips=clips,
        playlists=playlists,
    )
