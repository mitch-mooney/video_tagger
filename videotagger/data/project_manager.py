import json
import os
from videotagger.models.project import (
    Category, Clip, Period, Playlist, Project, VideoAngle,
)


class ProjectManager:
    """The persistence seam for projects.

    The only module that knows the on-disk ``.vtp`` format: serialization,
    version migration, and relative-path resolution all live behind ``save``/``load``.
    The domain model (:mod:`videotagger.models.project`) stays a plain dataclass.
    """

    @staticmethod
    def save(project: Project, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_to_dict(project), f, indent=2)

    @staticmethod
    def load(path: str) -> Project:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Project file not found: {path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupt project file ({path}): {e}")

        project = _from_dict(data)

        # Resolve relative paths against the .vtp file's directory
        vtp_dir = os.path.dirname(os.path.abspath(path))
        if not os.path.isabs(project.merged_video_path):
            project.merged_video_path = os.path.normpath(
                os.path.join(vtp_dir, project.merged_video_path)
            )
        project.source_video_paths = [
            _resolve(vtp_dir, p) for p in project.source_video_paths
        ]
        for angle in project.angles:
            angle.merged_video_path = _resolve(vtp_dir, angle.merged_video_path)
            angle.source_video_paths = [
                _resolve(vtp_dir, p) for p in angle.source_video_paths
            ]
        return project


def _resolve(base_dir: str, path: str) -> str:
    if not path or os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(base_dir, path))


# ── on-disk format ────────────────────────────────────────────────────────
# Serialization and version migration. Private to the persistence seam — callers
# go through ProjectManager.save/load, never these directly.

def _to_dict(proj: Project) -> dict:
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
        "periods": [
            {"id": p.id, "name": p.name, "primary_start": p.primary_start}
            for p in proj.periods
        ],
        "angles": [
            {"id": a.id, "name": a.name,
             "source_video_paths": a.source_video_paths,
             "merged_video_path": a.merged_video_path,
             "period_starts": a.period_starts}
            for a in proj.angles
        ],
    }


def _from_dict(d: dict) -> Project:
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
    periods = [
        Period(id=p["id"], name=p["name"], primary_start=p["primary_start"])
        for p in d.get("periods", [])
    ]
    angles = [
        VideoAngle(
            id=a["id"], name=a["name"],
            source_video_paths=a.get("source_video_paths", []),
            merged_video_path=a.get("merged_video_path", ""),
            period_starts={k: float(v) for k, v in a.get("period_starts", {}).items()},
        )
        for a in d.get("angles", [])
    ]
    return Project(
        version=3,
        source_video_paths=source_paths,
        merged_video_path=merged_path,
        categories=categories,
        clips=clips,
        playlists=playlists,
        periods=periods,
        angles=angles,
    )
