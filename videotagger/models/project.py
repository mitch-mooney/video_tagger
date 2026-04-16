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
    source_video_paths: List[str]
    merged_video_path: str
    categories: List[Category] = field(default_factory=list)
    clips: List[Clip] = field(default_factory=list)
    playlists: List[Playlist] = field(default_factory=list)
    version: int = 2


def project_to_dict(proj: Project) -> dict:
    return {
        "version": proj.version,
        "source_video_paths": proj.source_video_paths,
        "merged_video_path": proj.merged_video_path,
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
    # v1 migration: video_path → source_video_paths + merged_video_path
    if d.get("version", 1) == 1:
        old_path = d.get("video_path", "")
        source_paths = [old_path]
        merged_path = old_path
    else:
        source_paths = d.get("source_video_paths", [])
        merged_path = d.get("merged_video_path", "")

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
        version=2,
        source_video_paths=source_paths,
        merged_video_path=merged_path,
        categories=categories,
        clips=clips,
        playlists=playlists,
    )
