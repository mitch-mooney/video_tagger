import uuid
from dataclasses import dataclass, field
from typing import Dict, List


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
class Period:
    """A match period (quarter/half) anchored on the primary/canonical timeline."""
    name: str            # "Q1", "Half 1", ...
    primary_start: float # video-time (s) where this period begins in the PRIMARY video
    id: str = field(default_factory=_new_id)


@dataclass
class VideoAngle:
    """An additional camera angle synced onto the canonical timeline per period."""
    name: str                          # "Behind Goals"
    source_video_paths: List[str] = field(default_factory=list)
    merged_video_path: str = ""        # this angle's working video (via VideoMerger)
    period_starts: Dict[str, float] = field(default_factory=dict)  # period.id -> video-time (s)
    id: str = field(default_factory=_new_id)


@dataclass
class Project:
    source_video_paths: List[str]
    merged_video_path: str
    categories: List[Category] = field(default_factory=list)
    clips: List[Clip] = field(default_factory=list)
    playlists: List[Playlist] = field(default_factory=list)
    periods: List[Period] = field(default_factory=list)   # canonical, primary-relative
    angles: List[VideoAngle] = field(default_factory=list)  # ADDITIONAL angles beyond primary
    version: int = 3
