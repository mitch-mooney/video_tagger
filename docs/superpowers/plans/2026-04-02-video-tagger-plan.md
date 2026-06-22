# Video Tagger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows `.exe` for tagging sporting video clips, building playlists, and exporting them as cut `.mp4` files or EDL reference files.

**Architecture:** Four layers — UI (PyQt6), Core Logic (tagging engine, playlist builder), Data (project/template JSON files), Export (ffmpeg + EDL). The project file (`.vtp`) is plain JSON shared between teammates alongside the video file.

**Tech Stack:** Python 3.11+, PyQt6, python-vlc (libVLC), ffmpeg-python, PyInstaller

---

## File Structure

```
VideoAnalysis/
├── main.py                              # Entry point
├── requirements.txt
├── VideoTagger.spec                     # PyInstaller spec
├── build.py                             # Build helper script
├── videotagger/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── project.py                   # Category, Clip, Playlist, Project dataclasses + serialization
│   ├── data/
│   │   ├── __init__.py
│   │   ├── project_manager.py           # Load/save .vtp files
│   │   └── template_manager.py          # Load/save/list templates from %APPDATA%
│   ├── core/
│   │   ├── __init__.py
│   │   ├── tagging_engine.py            # I/O state machine
│   │   └── playlist_builder.py          # Playlist CRUD
│   ├── export/
│   │   ├── __init__.py
│   │   ├── ffmpeg_exporter.py           # Cut clips to .mp4
│   │   └── edl_writer.py               # Write CMX 3600 EDL files
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py              # MainWindow, layout, menus, keyboard shortcuts
│   │   ├── player_widget.py            # libVLC embedded player + controls
│   │   ├── timeline_widget.py          # Custom QPainter timeline
│   │   ├── tag_panel.py                # Left bottom: category/label tree
│   │   ├── clips_panel.py              # Right bottom: Clips + Playlists tabs
│   │   ├── presentation_window.py      # Full-screen presentation mode + HUD
│   │   └── dialogs/
│   │       ├── __init__.py
│   │       ├── new_project_dialog.py   # Select video + load template
│   │       ├── new_clip_dialog.py      # Assign category/label/times/notes
│   │       ├── tag_manager_dialog.py   # Add/edit/delete categories and labels
│   │       └── export_dialog.py        # Export playlist options
│   └── resources/
│       └── templates/
│           └── afl.json                # Built-in AFL template
└── tests/
    ├── conftest.py
    ├── test_models.py
    ├── test_project_manager.py
    ├── test_template_manager.py
    ├── test_tagging_engine.py
    ├── test_playlist_builder.py
    ├── test_edl_writer.py
    └── test_ffmpeg_exporter.py
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `main.py`
- Create: `videotagger/__init__.py`
- Create: all `__init__.py` files for subpackages

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p videotagger/models videotagger/data videotagger/core videotagger/export videotagger/ui/dialogs videotagger/resources/templates tests
touch videotagger/__init__.py videotagger/models/__init__.py videotagger/data/__init__.py videotagger/core/__init__.py videotagger/export/__init__.py videotagger/ui/__init__.py videotagger/ui/dialogs/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

```
PyQt6>=6.6.0
python-vlc>=3.0.18122
ffmpeg-python>=0.2.0
pytest>=7.4.0
pytest-qt>=4.2.0
pyinstaller>=6.0.0
```

- [ ] **Step 3: Create main.py**

```python
import sys
from PyQt6.QtWidgets import QApplication
from videotagger.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VideoTagger")
    app.setOrganizationName("VideoTagger")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 5: Commit**

```bash
git init
git add requirements.txt main.py videotagger/ tests/
git commit -m "feat: project scaffolding"
```

---

### Task 2: Data Models

**Files:**
- Create: `videotagger/models/project.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models.py
import pytest
from videotagger.models.project import Category, Clip, Playlist, Project
from videotagger.models.project import project_to_dict, project_from_dict

def test_category_has_auto_id():
    cat = Category(name="Offence", color="#e94560", labels=["Goal", "Behind"])
    assert cat.id is not None
    assert len(cat.id) == 36  # UUID format

def test_clip_has_auto_id():
    clip = Clip(category_id="cat-1", label="Goal", start=10.0, end=20.0)
    assert clip.id is not None

def test_project_round_trip():
    cat = Category(name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(category_id=cat.id, label="Goal", start=10.5, end=18.2, notes="Great goal")
    pl = Playlist(name="Best Goals", clip_ids=[clip.id])
    proj = Project(video_path="C:/video.mp4", categories=[cat], clips=[clip], playlists=[pl])
    d = project_to_dict(proj)
    proj2 = project_from_dict(d)
    assert proj2.video_path == "C:/video.mp4"
    assert proj2.categories[0].name == "Offence"
    assert proj2.clips[0].start == 10.5
    assert proj2.clips[0].notes == "Great goal"
    assert proj2.playlists[0].name == "Best Goals"
    assert proj2.playlists[0].clip_ids == [clip.id]

def test_project_from_dict_missing_notes_defaults_empty():
    d = {
        "version": 1, "video_path": "C:/v.mp4", "categories": [],
        "clips": [{"id": "c1", "category_id": "cat1", "label": "Goal", "start": 1.0, "end": 2.0}],
        "playlists": []
    }
    proj = project_from_dict(d)
    assert proj.clips[0].notes == ""
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_models.py -v
```
Expected: `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: Implement models**

```python
# videotagger/models/project.py
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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_models.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add videotagger/models/project.py tests/test_models.py
git commit -m "feat: data models with serialization"
```

---

### Task 3: Project File Manager

**Files:**
- Create: `videotagger/data/project_manager.py`
- Create: `tests/test_project_manager.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_project_manager.py
import json, os, pytest
from videotagger.models.project import Category, Clip, Project
from videotagger.data.project_manager import ProjectManager

@pytest.fixture
def sample_project(tmp_path):
    cat = Category(name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(category_id=cat.id, label="Goal", start=10.0, end=15.0)
    return Project(video_path=str(tmp_path / "video.mp4"), categories=[cat], clips=[clip])

def test_save_creates_file(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    assert path.exists()

def test_save_writes_valid_json(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    with open(path) as f:
        data = json.load(f)
    assert data["version"] == 1
    assert data["categories"][0]["name"] == "Offence"

def test_load_round_trip(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    loaded = ProjectManager.load(str(path))
    assert loaded.video_path == sample_project.video_path
    assert loaded.clips[0].start == 10.0

def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        ProjectManager.load("nonexistent.vtp")

def test_load_corrupt_file_raises(tmp_path):
    path = tmp_path / "bad.vtp"
    path.write_text("not json")
    with pytest.raises(ValueError):
        ProjectManager.load(str(path))
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_project_manager.py -v
```

- [ ] **Step 3: Implement**

```python
# videotagger/data/project_manager.py
import json
from videotagger.models.project import Project, project_to_dict, project_from_dict

class ProjectManager:
    @staticmethod
    def save(project: Project, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(project_to_dict(project), f, indent=2)

    @staticmethod
    def load(path: str) -> Project:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Project file not found: {path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupt project file ({path}): {e}")
        return project_from_dict(data)
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest tests/test_project_manager.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add videotagger/data/project_manager.py tests/test_project_manager.py
git commit -m "feat: project file manager (load/save .vtp)"
```

---

### Task 4: Template Manager + AFL Template

**Files:**
- Create: `videotagger/data/template_manager.py`
- Create: `videotagger/resources/templates/afl.json`
- Create: `tests/test_template_manager.py`

- [ ] **Step 1: Create the AFL template file**

```json
{
  "name": "AFL",
  "categories": [
    {"name": "Offence", "color": "#e94560", "labels": ["Goal", "Behind", "Handball", "Kick", "Mark", "Shot at Goal"]},
    {"name": "Defence", "color": "#4ade80", "labels": ["Tackle", "Spoil", "Intercept", "Pressure Act", "Smother"]},
    {"name": "Stoppages", "color": "#facc15", "labels": ["Ball-up", "Boundary Throw-in", "Kick-in"]},
    {"name": "General", "color": "#a78bfa", "labels": ["Error", "Highlight"]}
  ]
}
```

Save to: `videotagger/resources/templates/afl.json`

- [ ] **Step 2: Write failing tests**

```python
# tests/test_template_manager.py
import pytest
from videotagger.data.template_manager import TemplateManager
from videotagger.models.project import Category

def test_list_builtin_templates():
    templates = TemplateManager.list_builtin()
    assert "AFL" in templates

def test_load_builtin_afl():
    cats = TemplateManager.load_builtin("AFL")
    names = [c.name for c in cats]
    assert "Offence" in names
    assert "Defence" in names
    labels = next(c.labels for c in cats if c.name == "Offence")
    assert "Goal" in labels

def test_save_and_load_user_template(tmp_path, monkeypatch):
    monkeypatch.setattr("videotagger.data.template_manager.TemplateManager._user_dir",
                        staticmethod(lambda: str(tmp_path)))
    cats = [Category(name="Attack", color="#ff0000", labels=["Shot", "Pass"])]
    TemplateManager.save_user("My Template", cats)
    loaded = TemplateManager.load_user("My Template")
    assert loaded[0].name == "Attack"
    assert "Shot" in loaded[0].labels

def test_list_user_templates(tmp_path, monkeypatch):
    monkeypatch.setattr("videotagger.data.template_manager.TemplateManager._user_dir",
                        staticmethod(lambda: str(tmp_path)))
    cats = [Category(name="X", color="#000", labels=[])]
    TemplateManager.save_user("Custom", cats)
    assert "Custom" in TemplateManager.list_user()
```

- [ ] **Step 3: Run — verify fail**

```bash
pytest tests/test_template_manager.py -v
```

- [ ] **Step 4: Implement**

```python
# videotagger/data/template_manager.py
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
        return [Path(f).stem for f in os.listdir(d) if f.endswith(".json")]

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
        return [Path(f).stem for f in os.listdir(d) if f.endswith(".json")]
```

- [ ] **Step 5: Run — verify pass**

```bash
pytest tests/test_template_manager.py -v
```
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add videotagger/data/template_manager.py videotagger/resources/templates/afl.json tests/test_template_manager.py
git commit -m "feat: template manager + built-in AFL template"
```

---

### Task 5: Tagging Engine

**Files:**
- Create: `videotagger/core/tagging_engine.py`
- Create: `tests/test_tagging_engine.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_tagging_engine.py
import pytest
from videotagger.core.tagging_engine import TaggingEngine, TaggingState

def test_initial_state_is_idle():
    engine = TaggingEngine()
    assert engine.state == TaggingState.IDLE
    assert engine.mark_in is None

def test_press_in_sets_marking_state():
    engine = TaggingEngine()
    engine.press_in(10.0)
    assert engine.state == TaggingState.MARKING
    assert engine.mark_in == 10.0

def test_press_in_twice_updates_start():
    engine = TaggingEngine()
    engine.press_in(10.0)
    engine.press_in(12.0)
    assert engine.mark_in == 12.0

def test_press_out_returns_start_end():
    engine = TaggingEngine()
    engine.press_in(10.0)
    start, end = engine.press_out(20.0)
    assert start == 10.0
    assert end == 20.0

def test_press_out_resets_to_idle():
    engine = TaggingEngine()
    engine.press_in(10.0)
    engine.press_out(20.0)
    assert engine.state == TaggingState.IDLE
    assert engine.mark_in is None

def test_press_out_without_in_raises():
    engine = TaggingEngine()
    with pytest.raises(ValueError, match="start"):
        engine.press_out(20.0)

def test_press_out_before_in_raises():
    engine = TaggingEngine()
    engine.press_in(20.0)
    with pytest.raises(ValueError, match="after"):
        engine.press_out(10.0)

def test_cancel_resets_state():
    engine = TaggingEngine()
    engine.press_in(10.0)
    engine.cancel()
    assert engine.state == TaggingState.IDLE
    assert engine.mark_in is None
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_tagging_engine.py -v
```

- [ ] **Step 3: Implement**

```python
# videotagger/core/tagging_engine.py
from enum import Enum, auto
from typing import Optional, Tuple

class TaggingState(Enum):
    IDLE = auto()
    MARKING = auto()

class TaggingEngine:
    def __init__(self):
        self._state = TaggingState.IDLE
        self._mark_in: Optional[float] = None

    @property
    def state(self) -> TaggingState:
        return self._state

    @property
    def mark_in(self) -> Optional[float]:
        return self._mark_in

    def press_in(self, position: float) -> None:
        self._state = TaggingState.MARKING
        self._mark_in = position

    def press_out(self, position: float) -> Tuple[float, float]:
        if self._state != TaggingState.MARKING:
            raise ValueError("Cannot mark out: no start marked yet")
        if position <= self._mark_in:
            raise ValueError("End must be after start position")
        start = self._mark_in
        self._state = TaggingState.IDLE
        self._mark_in = None
        return start, position

    def cancel(self) -> None:
        self._state = TaggingState.IDLE
        self._mark_in = None
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest tests/test_tagging_engine.py -v
```
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add videotagger/core/tagging_engine.py tests/test_tagging_engine.py
git commit -m "feat: tagging engine state machine"
```

---

### Task 6: Playlist Builder

**Files:**
- Create: `videotagger/core/playlist_builder.py`
- Create: `tests/test_playlist_builder.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_playlist_builder.py
import pytest
from videotagger.models.project import Category, Clip, Playlist, Project
from videotagger.core.playlist_builder import PlaylistBuilder

@pytest.fixture
def project_with_clips():
    cat = Category(name="Offence", color="#e94560", labels=["Goal"])
    c1 = Clip(category_id=cat.id, label="Goal", start=10.0, end=15.0)
    c2 = Clip(category_id=cat.id, label="Goal", start=30.0, end=35.0)
    return Project(video_path="v.mp4", categories=[cat], clips=[c1, c2]), c1, c2

def test_create_playlist(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    assert pl.name == "Goals"
    assert any(p.id == pl.id for p in proj.playlists)

def test_add_clip_to_playlist(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.add_clip(pl.id, c1.id)
    assert c1.id in pl.clip_ids

def test_add_clip_no_duplicates(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.add_clip(pl.id, c1.id)
    builder.add_clip(pl.id, c1.id)
    assert pl.clip_ids.count(c1.id) == 1

def test_remove_clip(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.add_clip(pl.id, c1.id)
    builder.remove_clip(pl.id, c1.id)
    assert c1.id not in pl.clip_ids

def test_delete_playlist(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.delete_playlist(pl.id)
    assert not any(p.id == pl.id for p in proj.playlists)

def test_get_clips_returns_ordered_clips(project_with_clips):
    proj, c1, c2 = project_with_clips
    builder = PlaylistBuilder(proj)
    pl = builder.create_playlist("Goals")
    builder.add_clip(pl.id, c2.id)
    builder.add_clip(pl.id, c1.id)
    clips = builder.get_clips(pl.id)
    assert clips[0].id == c2.id
    assert clips[1].id == c1.id
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_playlist_builder.py -v
```

- [ ] **Step 3: Implement**

```python
# videotagger/core/playlist_builder.py
from typing import List
from videotagger.models.project import Clip, Playlist, Project

class PlaylistBuilder:
    def __init__(self, project: Project):
        self._project = project

    def create_playlist(self, name: str) -> Playlist:
        pl = Playlist(name=name)
        self._project.playlists.append(pl)
        return pl

    def delete_playlist(self, playlist_id: str) -> None:
        self._project.playlists = [p for p in self._project.playlists if p.id != playlist_id]

    def add_clip(self, playlist_id: str, clip_id: str) -> None:
        pl = self._get(playlist_id)
        if clip_id not in pl.clip_ids:
            pl.clip_ids.append(clip_id)

    def remove_clip(self, playlist_id: str, clip_id: str) -> None:
        pl = self._get(playlist_id)
        pl.clip_ids = [c for c in pl.clip_ids if c != clip_id]

    def reorder_clips(self, playlist_id: str, clip_ids: List[str]) -> None:
        pl = self._get(playlist_id)
        pl.clip_ids = clip_ids

    def get_clips(self, playlist_id: str) -> List[Clip]:
        pl = self._get(playlist_id)
        clip_map = {c.id: c for c in self._project.clips}
        return [clip_map[cid] for cid in pl.clip_ids if cid in clip_map]

    def _get(self, playlist_id: str) -> Playlist:
        for p in self._project.playlists:
            if p.id == playlist_id:
                return p
        raise KeyError(f"Playlist not found: {playlist_id}")
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest tests/test_playlist_builder.py -v
```
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add videotagger/core/playlist_builder.py tests/test_playlist_builder.py
git commit -m "feat: playlist builder"
```

---

### Task 7: EDL Writer

**Files:**
- Create: `videotagger/export/edl_writer.py`
- Create: `tests/test_edl_writer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_edl_writer.py
from videotagger.models.project import Category, Clip, Project
from videotagger.export.edl_writer import seconds_to_timecode, write_edl

def test_seconds_to_timecode_simple():
    assert seconds_to_timecode(0.0) == "00:00:00:00"
    assert seconds_to_timecode(1.0) == "00:00:01:00"
    assert seconds_to_timecode(61.0) == "00:01:01:00"
    assert seconds_to_timecode(3661.0) == "01:01:01:00"

def test_seconds_to_timecode_frames():
    # 25fps: 0.04s = 1 frame
    assert seconds_to_timecode(0.04) == "00:00:00:01"
    assert seconds_to_timecode(0.96) == "00:00:00:24"

def test_write_edl_creates_file(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=17.0)
    proj = Project(video_path="video.mp4", categories=[cat], clips=[clip])
    out = str(tmp_path / "out.edl")
    write_edl("Goals", [clip], proj, out)
    content = open(out).read()
    assert "TITLE: Goals" in content
    assert "00:00:10:00" in content   # src_in
    assert "00:00:17:00" in content   # src_out
    assert "Offence - Goal" in content

def test_write_edl_sequential_record_times(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    c1 = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=15.0)
    c2 = Clip(id="c2", category_id="cat1", label="Goal", start=30.0, end=38.0)
    proj = Project(video_path="video.mp4", categories=[cat], clips=[c1, c2])
    out = str(tmp_path / "out.edl")
    write_edl("Goals", [c1, c2], proj, out)
    content = open(out).read()
    # c2 record-in should be at 5 seconds (duration of c1)
    assert "00:00:05:00" in content
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_edl_writer.py -v
```

- [ ] **Step 3: Implement**

```python
# videotagger/export/edl_writer.py
from typing import List
from videotagger.models.project import Clip, Project

def seconds_to_timecode(seconds: float, fps: int = 25) -> str:
    total_frames = int(round(seconds * fps))
    frames = total_frames % fps
    secs = (total_frames // fps) % 60
    mins = (total_frames // (fps * 60)) % 60
    hours = total_frames // (fps * 3600)
    return f"{hours:02d}:{mins:02d}:{secs:02d}:{frames:02d}"

def write_edl(playlist_name: str, clips: List[Clip], project: Project,
              output_path: str, fps: int = 25) -> None:
    cat_map = {c.id: c for c in project.categories}
    lines = [f"TITLE: {playlist_name}", "FCM: NON-DROP FRAME", ""]
    rec_pos = 0.0
    for i, clip in enumerate(clips, 1):
        cat = cat_map.get(clip.category_id)
        cat_name = cat.name if cat else "Unknown"
        duration = clip.end - clip.start
        src_in = seconds_to_timecode(clip.start, fps)
        src_out = seconds_to_timecode(clip.end, fps)
        rec_in = seconds_to_timecode(rec_pos, fps)
        rec_out = seconds_to_timecode(rec_pos + duration, fps)
        rec_pos += duration
        lines.append(
            f"{i:03d}  AX       V     C        {src_in} {src_out} {rec_in} {rec_out}"
        )
        lines.append(f"* FROM CLIP NAME: {cat_name} - {clip.label}")
        if clip.notes:
            lines.append(f"* COMMENT: {clip.notes}")
        lines.append("")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest tests/test_edl_writer.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add videotagger/export/edl_writer.py tests/test_edl_writer.py
git commit -m "feat: EDL writer (CMX 3600 format)"
```

---

### Task 8: ffmpeg Exporter

**Files:**
- Create: `videotagger/export/ffmpeg_exporter.py`
- Create: `tests/test_ffmpeg_exporter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ffmpeg_exporter.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from videotagger.models.project import Category, Clip, Project
from videotagger.export.ffmpeg_exporter import (
    build_clip_filename, export_clip, export_playlist_clips
)

def test_build_clip_filename():
    assert build_clip_filename("C:/footage/afl_round5.mp4", "Offence", "Goal", 1) \
        == "afl_round5_Offence_Goal_001.mp4"
    assert build_clip_filename("C:/footage/afl_round5.mp4", "Defence", "Tackle", 12) \
        == "afl_round5_Defence_Tackle_012.mp4"

def test_export_clip_calls_ffmpeg(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=17.0)
    proj = Project(video_path="video.mp4", categories=[cat], clips=[clip])
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("videotagger.export.ffmpeg_exporter.subprocess.run", return_value=mock_result) as mock_run:
        output = export_clip(clip, "Offence", 1, "video.mp4", str(tmp_path))
    args = mock_run.call_args[0][0]
    assert "-ss" in args
    assert "10.0" in args
    assert "-t" in args
    assert "7.0" in args
    assert output.endswith("video_Offence_Goal_001.mp4")

def test_export_clip_raises_on_ffmpeg_failure(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=17.0)
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "error message"
    with patch("videotagger.export.ffmpeg_exporter.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="ffmpeg failed"):
            export_clip(clip, "Offence", 1, "video.mp4", str(tmp_path))

def test_export_playlist_clips_increments_instance(tmp_path):
    cat = Category(id="cat1", name="Offence", color="#e94560", labels=["Goal"])
    c1 = Clip(id="c1", category_id="cat1", label="Goal", start=10.0, end=15.0)
    c2 = Clip(id="c2", category_id="cat1", label="Goal", start=30.0, end=35.0)
    proj = Project(video_path="video.mp4", categories=[cat], clips=[c1, c2])
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("videotagger.export.ffmpeg_exporter.subprocess.run", return_value=mock_result):
        outputs = export_playlist_clips([c1, c2], proj, str(tmp_path))
    assert "Goal_001" in outputs[0]
    assert "Goal_002" in outputs[1]
```

- [ ] **Step 2: Run — verify fail**

```bash
pytest tests/test_ffmpeg_exporter.py -v
```

- [ ] **Step 3: Implement**

```python
# videotagger/export/ffmpeg_exporter.py
import os
import subprocess
from pathlib import Path
from typing import List
from videotagger.models.project import Clip, Project

def _ffmpeg_path() -> str:
    bundled = Path(__file__).parent.parent / "resources" / "ffmpeg.exe"
    if bundled.exists():
        return str(bundled)
    return "ffmpeg"

def build_clip_filename(video_path: str, category_name: str, label: str, instance: int) -> str:
    stem = Path(video_path).stem
    return f"{stem}_{category_name}_{label}_{instance:03d}.mp4"

def export_clip(clip: Clip, category_name: str, instance: int,
                video_path: str, output_dir: str) -> str:
    filename = build_clip_filename(video_path, category_name, clip.label, instance)
    output_path = os.path.join(output_dir, filename)
    duration = str(round(clip.end - clip.start, 6))
    cmd = [
        _ffmpeg_path(), "-y",
        "-ss", str(clip.start),
        "-i", video_path,
        "-t", duration,
        "-c", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    return output_path

def export_playlist_clips(playlist_clips: List[Clip], project: Project,
                          output_dir: str) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    cat_map = {c.id: c for c in project.categories}
    label_counts: dict = {}
    outputs = []
    for clip in playlist_clips:
        cat = cat_map.get(clip.category_id)
        cat_name = cat.name if cat else "Unknown"
        key = f"{cat_name}_{clip.label}"
        label_counts[key] = label_counts.get(key, 0) + 1
        out = export_clip(clip, cat_name, label_counts[key], project.video_path, output_dir)
        outputs.append(out)
    return outputs
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest tests/test_ffmpeg_exporter.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add videotagger/export/ffmpeg_exporter.py tests/test_ffmpeg_exporter.py
git commit -m "feat: ffmpeg exporter"
```

---

### Task 9: Main Window Skeleton

**Files:**
- Create: `videotagger/ui/main_window.py`

Note: UI tasks use `pytest-qt` for smoke testing. A `QApplication` must exist; `pytest-qt` provides the `qtbot` fixture that handles this.

- [ ] **Step 1: Implement main window layout**

```python
# videotagger/ui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QMenuBar, QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from videotagger.models.project import Project

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VideoTagger")
        self.resize(1280, 800)
        self._project: Project | None = None
        self._project_path: str | None = None
        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        from videotagger.ui.player_widget import PlayerWidget
        from videotagger.ui.timeline_widget import TimelineWidget
        from videotagger.ui.tag_panel import TagPanel
        from videotagger.ui.clips_panel import ClipsPanel

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Main vertical splitter: player+timeline (top) | bottom panels
        self._vsplit = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self._vsplit)

        # Top section: player + timeline stacked vertically
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        self.player = PlayerWidget()
        self.timeline = TimelineWidget()
        self.timeline.setFixedHeight(60)
        top_layout.addWidget(self.player, stretch=1)
        top_layout.addWidget(self.timeline)
        self._vsplit.addWidget(top_widget)

        # Bottom section: tag panel | clips panel side by side
        self._hsplit = QSplitter(Qt.Orientation.Horizontal)
        self.tag_panel = TagPanel()
        self.clips_panel = ClipsPanel()
        self._hsplit.addWidget(self.tag_panel)
        self._hsplit.addWidget(self.clips_panel)
        self._hsplit.setSizes([300, 700])
        self._vsplit.addWidget(self._hsplit)

        self._vsplit.setSizes([600, 200])
        self.setStatusBar(QStatusBar())

    def _setup_menu(self):
        menubar = self.menuBar()
        # File menu
        file_menu = menubar.addMenu("&File")
        new_act = QAction("&New Project...", self)
        new_act.setShortcut(QKeySequence.StandardKey.New)
        new_act.triggered.connect(self._new_project)
        file_menu.addAction(new_act)

        open_act = QAction("&Open Project...", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self._open_project)
        file_menu.addAction(open_act)

        self._save_act = QAction("&Save", self)
        self._save_act.setShortcut(QKeySequence.StandardKey.Save)
        self._save_act.triggered.connect(self._save_project)
        self._save_act.setEnabled(False)
        file_menu.addAction(self._save_act)

        file_menu.addSeparator()
        quit_act = QAction("&Quit", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        # Tags menu
        tags_menu = menubar.addMenu("&Tags")
        manage_act = QAction("&Manage Tags...", self)
        manage_act.triggered.connect(self._open_tag_manager)
        tags_menu.addAction(manage_act)

    def _new_project(self):
        from videotagger.ui.dialogs.new_project_dialog import NewProjectDialog
        dlg = NewProjectDialog(self)
        if dlg.exec():
            self._load_project(dlg.project(), None)

    def _open_project(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Video Tagger Project (*.vtp)"
        )
        if not path:
            return
        from videotagger.data.project_manager import ProjectManager
        try:
            proj = ProjectManager.load(path)
        except (FileNotFoundError, ValueError) as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", str(e))
            return
        self._load_project(proj, path)

    def _save_project(self):
        if not self._project:
            return
        from videotagger.data.project_manager import ProjectManager
        if not self._project_path:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Project", "", "Video Tagger Project (*.vtp)"
            )
            if not path:
                return
            if not path.endswith(".vtp"):
                path += ".vtp"
            self._project_path = path
        ProjectManager.save(self._project, self._project_path)
        self.statusBar().showMessage(f"Saved: {self._project_path}", 3000)

    def _open_tag_manager(self):
        if not self._project:
            return
        from videotagger.ui.dialogs.tag_manager_dialog import TagManagerDialog
        dlg = TagManagerDialog(self._project, self)
        dlg.exec()
        self.tag_panel.refresh(self._project)

    def _load_project(self, project: Project, path: str | None):
        self._project = project
        self._project_path = path
        self._save_act.setEnabled(True)
        self.setWindowTitle(f"VideoTagger — {project.video_path}")
        self.player.load(project.video_path)
        self.timeline.set_project(project)
        self.tag_panel.refresh(project)
        self.clips_panel.refresh(project)

    def closeEvent(self, event):
        # TODO: check unsaved changes
        event.accept()
```

- [ ] **Step 2: Smoke test**

```python
# tests/test_main_window.py (create this file)
def test_main_window_opens(qtbot):
    from videotagger.ui.main_window import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    assert win.isVisible()
```

- [ ] **Step 3: Run smoke test**

```bash
pytest tests/test_main_window.py -v
```
Expected: 1 passed. (May show stub errors until later tasks fill in player/timeline/panels — stub them as empty QWidget subclasses first, see next tasks.)

- [ ] **Step 4: Commit**

```bash
git add videotagger/ui/main_window.py tests/test_main_window.py
git commit -m "feat: main window skeleton with layout and menus"
```

---

### Task 10: Video Player Widget

**Files:**
- Create: `videotagger/ui/player_widget.py`

- [ ] **Step 1: Implement player widget**

```python
# videotagger/ui/player_widget.py
import sys
import vlc
from PyQt6.QtWidgets import QWidget, QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

class PlayerWidget(QWidget):
    position_changed = pyqtSignal(float)   # current position in seconds
    duration_changed = pyqtSignal(float)   # total duration in seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self._instance = vlc.Instance("--no-xlib")
        self._player = self._instance.media_player_new()
        self._duration = 0.0
        self._setup_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._poll_position)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Video frame
        self._frame = QFrame()
        self._frame.setStyleSheet("background: black;")
        self._frame.setMinimumHeight(200)
        layout.addWidget(self._frame, stretch=1)

        # Controls row
        ctrl = QHBoxLayout()
        ctrl.setContentsMargins(4, 2, 4, 2)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedWidth(36)
        self._play_btn.clicked.connect(self.toggle_play)
        ctrl.addWidget(self._play_btn)

        self._pos_label = QLabel("00:00:00")
        self._pos_label.setFont(QFont("Courier", 9))
        ctrl.addWidget(self._pos_label)

        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setRange(0, 10000)
        self._seek_slider.sliderMoved.connect(self._seek_to_slider)
        ctrl.addWidget(self._seek_slider, stretch=1)

        self._dur_label = QLabel("00:00:00")
        self._dur_label.setFont(QFont("Courier", 9))
        ctrl.addWidget(self._dur_label)

        self._speed_label = QLabel("1.0x")
        self._speed_label.setFixedWidth(36)
        ctrl.addWidget(self._speed_label)

        layout.addLayout(ctrl)

    def load(self, path: str) -> None:
        media = self._instance.media_new(path)
        self._player.set_media(media)
        if sys.platform == "win32":
            self._player.set_hwnd(int(self._frame.winId()))
        elif sys.platform == "darwin":
            self._player.set_nsobject(int(self._frame.winId()))
        else:
            self._player.set_xwindow(int(self._frame.winId()))
        self._player.play()
        self._timer.start()
        # Get duration after media parses (poll briefly)
        QTimer.singleShot(500, self._update_duration)

    def _update_duration(self):
        ms = self._player.get_length()
        if ms > 0:
            self._duration = ms / 1000.0
            self.duration_changed.emit(self._duration)
            self._dur_label.setText(self._fmt(self._duration))
        else:
            QTimer.singleShot(300, self._update_duration)

    def toggle_play(self):
        if self._player.is_playing():
            self._player.pause()
            self._play_btn.setText("▶")
        else:
            self._player.play()
            self._play_btn.setText("⏸")

    def get_position(self) -> float:
        return self._player.get_time() / 1000.0

    def seek(self, seconds: float) -> None:
        self._player.set_time(int(seconds * 1000))

    def step(self, seconds: float) -> None:
        self.seek(max(0.0, self.get_position() + seconds))

    def set_rate(self, rate: float) -> None:
        rate = max(0.25, min(4.0, rate))
        self._player.set_rate(rate)
        self._speed_label.setText(f"{rate:.2g}x")

    def get_rate(self) -> float:
        return self._player.get_rate()

    def _poll_position(self):
        if self._player.is_playing() or self._player.get_state() == vlc.State.Paused:
            pos = self.get_position()
            self.position_changed.emit(pos)
            self._pos_label.setText(self._fmt(pos))
            if self._duration > 0:
                self._seek_slider.setValue(int(pos / self._duration * 10000))

    def _seek_to_slider(self, value: int):
        if self._duration > 0:
            self.seek(value / 10000.0 * self._duration)

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
```

- [ ] **Step 2: Smoke test**

```python
# Add to tests/test_main_window.py
def test_player_widget_creates(qtbot):
    from videotagger.ui.player_widget import PlayerWidget
    w = PlayerWidget()
    qtbot.addWidget(w)
    w.show()
    assert w.isVisible()
```

- [ ] **Step 3: Run**

```bash
pytest tests/test_main_window.py -v
```

- [ ] **Step 4: Commit**

```bash
git add videotagger/ui/player_widget.py tests/test_main_window.py
git commit -m "feat: video player widget (libVLC)"
```

---

### Task 11: Timeline Widget

**Files:**
- Create: `videotagger/ui/timeline_widget.py`

- [ ] **Step 1: Implement**

```python
# videotagger/ui/timeline_widget.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from videotagger.models.project import Project

class TimelineWidget(QWidget):
    seek_requested = pyqtSignal(float)   # user clicked — seek to this time
    clip_clicked = pyqtSignal(str)       # clip id clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project: Project | None = None
        self._duration = 0.0
        self._position = 0.0
        self.setMinimumHeight(50)
        self.setMouseTracking(True)

    def set_project(self, project: Project) -> None:
        self._project = project
        self.update()

    def set_duration(self, seconds: float) -> None:
        self._duration = seconds
        self.update()

    def set_position(self, seconds: float) -> None:
        self._position = seconds
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor("#1a1a2e"))

        if self._duration <= 0 or not self._project:
            painter.end()
            return

        # Track bar
        track_y = h // 2 - 6
        track_h = 12
        painter.fillRect(0, track_y, w, track_h, QColor("#0f3460"))

        # Draw clips
        cat_map = {c.id: c for c in self._project.categories}
        for clip in self._project.clips:
            x1 = int(clip.start / self._duration * w)
            x2 = int(clip.end / self._duration * w)
            cat = cat_map.get(clip.category_id)
            color = QColor(cat.color if cat else "#888888")
            painter.fillRect(x1, track_y, max(2, x2 - x1), track_h, color)

        # Playhead
        px = int(self._position / self._duration * w)
        pen = QPen(QColor("white"), 2)
        painter.setPen(pen)
        painter.drawLine(px, 0, px, h)

        painter.end()

    def mousePressEvent(self, event):
        if self._duration <= 0:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            t = event.position().x() / self.width() * self._duration
            # Check if a clip was clicked
            if self._project:
                for clip in self._project.clips:
                    x1 = clip.start / self._duration * self.width()
                    x2 = clip.end / self._duration * self.width()
                    if x1 <= event.position().x() <= x2:
                        self.clip_clicked.emit(clip.id)
                        return
            self.seek_requested.emit(t)
```

- [ ] **Step 2: Smoke test**

Add to `tests/test_main_window.py`:

```python
def test_timeline_widget_creates(qtbot):
    from videotagger.ui.timeline_widget import TimelineWidget
    w = TimelineWidget()
    qtbot.addWidget(w)
    w.show()
    assert w.isVisible()
```

- [ ] **Step 3: Run**

```bash
pytest tests/test_main_window.py -v
```

- [ ] **Step 4: Commit**

```bash
git add videotagger/ui/timeline_widget.py tests/test_main_window.py
git commit -m "feat: timeline widget with clip markers and playhead"
```

---

### Task 12: Tag Panel

**Files:**
- Create: `videotagger/ui/tag_panel.py`

- [ ] **Step 1: Implement**

```python
# videotagger/ui/tag_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QBrush
from videotagger.models.project import Project

class TagPanel(QWidget):
    label_selected = pyqtSignal(str, str)  # category_id, label

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        layout.addWidget(QLabel("Tags"))
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._tree)

    def refresh(self, project: Project) -> None:
        self._tree.clear()
        for cat in project.categories:
            cat_item = QTreeWidgetItem([cat.name])
            cat_item.setForeground(0, QBrush(QColor(cat.color)))
            cat_item.setData(0, Qt.ItemDataRole.UserRole, ("category", cat.id))
            for label in cat.labels:
                label_item = QTreeWidgetItem([label])
                label_item.setData(0, Qt.ItemDataRole.UserRole, ("label", cat.id, label))
                cat_item.addChild(label_item)
            self._tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == "label":
            self.label_selected.emit(data[1], data[2])
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/tag_panel.py
git commit -m "feat: tag panel (category/label tree)"
```

---

### Task 13: Clips + Playlists Panel

**Files:**
- Create: `videotagger/ui/clips_panel.py`

- [ ] **Step 1: Implement**

```python
# videotagger/ui/clips_panel.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QListWidget, QListWidgetItem, QHeaderView, QAbstractItemView, QMenu
)
from PyQt6.QtCore import pyqtSignal, Qt
from videotagger.models.project import Project, Clip, Playlist

class ClipsPanel(QWidget):
    clip_selected = pyqtSignal(str)        # clip id
    playlist_selected = pyqtSignal(str)    # playlist id
    export_requested = pyqtSignal(str)     # playlist id
    present_requested = pyqtSignal(str)    # playlist id
    new_playlist_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project: Project | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)
        self._clips_table = self._make_clips_table()
        self._playlists_list = self._make_playlists_list()
        self._tabs.addTab(self._clips_table, "Clips")
        self._tabs.addTab(self._playlists_list, "Playlists")

    def _make_clips_table(self) -> QTableWidget:
        t = QTableWidget(0, 4)
        t.setHorizontalHeaderLabels(["Category", "Label", "Start", "End"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.cellClicked.connect(self._on_clip_clicked)
        t.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        t.customContextMenuRequested.connect(self._clips_context_menu)
        return t

    def _make_playlists_list(self) -> QListWidget:
        l = QListWidget()
        l.itemClicked.connect(self._on_playlist_clicked)
        l.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        l.customContextMenuRequested.connect(self._playlists_context_menu)
        return l

    def refresh(self, project: Project) -> None:
        self._project = project
        self._refresh_clips()
        self._refresh_playlists()

    def _refresh_clips(self):
        if not self._project:
            return
        cat_map = {c.id: c for c in self._project.categories}
        self._clips_table.setRowCount(0)
        for clip in self._project.clips:
            row = self._clips_table.rowCount()
            self._clips_table.insertRow(row)
            cat = cat_map.get(clip.category_id)
            self._clips_table.setItem(row, 0, QTableWidgetItem(cat.name if cat else ""))
            self._clips_table.setItem(row, 1, QTableWidgetItem(clip.label))
            self._clips_table.setItem(row, 2, QTableWidgetItem(self._fmt(clip.start)))
            self._clips_table.setItem(row, 3, QTableWidgetItem(self._fmt(clip.end)))
            self._clips_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, clip.id)

    def _refresh_playlists(self):
        if not self._project:
            return
        self._playlists_list.clear()
        for pl in self._project.playlists:
            item = QListWidgetItem(f"{pl.name} ({len(pl.clip_ids)} clips)")
            item.setData(Qt.ItemDataRole.UserRole, pl.id)
            self._playlists_list.addItem(item)

    def _on_clip_clicked(self, row, col):
        item = self._clips_table.item(row, 0)
        if item:
            self.clip_selected.emit(item.data(Qt.ItemDataRole.UserRole))

    def _on_playlist_clicked(self, item: QListWidgetItem):
        self.playlist_selected.emit(item.data(Qt.ItemDataRole.UserRole))

    def _clips_context_menu(self, pos):
        if not self._project:
            return
        item = self._clips_table.itemAt(pos)
        if not item:
            return
        clip_id = self._clips_table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        for pl in self._project.playlists:
            act = menu.addAction(f"Add to: {pl.name}")
            act.setData(pl.id)
        if self._project.playlists:
            menu.addSeparator()
        menu.addAction("New playlist...").setData("__new__")
        chosen = menu.exec(self._clips_table.mapToGlobal(pos))
        if chosen:
            if chosen.data() == "__new__":
                self.new_playlist_requested.emit()
            else:
                from videotagger.core.playlist_builder import PlaylistBuilder
                PlaylistBuilder(self._project).add_clip(chosen.data(), clip_id)
                self._refresh_playlists()

    def _playlists_context_menu(self, pos):
        item = self._playlists_list.itemAt(pos)
        if not item:
            return
        pl_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.addAction("Present Playlist").setData(("present", pl_id))
        menu.addAction("Export Playlist...").setData(("export", pl_id))
        menu.addSeparator()
        menu.addAction("Delete Playlist").setData(("delete", pl_id))
        chosen = menu.exec(self._playlists_list.mapToGlobal(pos))
        if chosen:
            action, pid = chosen.data()
            if action == "present":
                self.present_requested.emit(pid)
            elif action == "export":
                self.export_requested.emit(pid)
            elif action == "delete":
                from videotagger.core.playlist_builder import PlaylistBuilder
                PlaylistBuilder(self._project).delete_playlist(pid)
                self._refresh_playlists()

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        ms = int((seconds - s) * 10)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}.{ms}"
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/clips_panel.py
git commit -m "feat: clips and playlists panel"
```

---

### Task 14: New Clip Dialog

**Files:**
- Create: `videotagger/ui/dialogs/new_clip_dialog.py`

- [ ] **Step 1: Implement**

```python
# videotagger/ui/dialogs/new_clip_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QComboBox, QLineEdit, QDoubleSpinBox,
    QDialogButtonBox, QTextEdit, QLabel
)
from PyQt6.QtCore import Qt
from videotagger.models.project import Category, Clip, Project

class NewClipDialog(QDialog):
    def __init__(self, project: Project, start: float, end: float,
                 preset_category_id: str = None, preset_label: str = None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Clip")
        self._project = project
        self._clip: Clip | None = None
        layout = QFormLayout(self)

        self._cat_combo = QComboBox()
        for cat in project.categories:
            self._cat_combo.addItem(cat.name, cat.id)
        if preset_category_id:
            idx = self._cat_combo.findData(preset_category_id)
            if idx >= 0:
                self._cat_combo.setCurrentIndex(idx)
        self._cat_combo.currentIndexChanged.connect(self._update_labels)
        layout.addRow("Category:", self._cat_combo)

        self._label_combo = QComboBox()
        self._update_labels()
        if preset_label:
            idx = self._label_combo.findText(preset_label)
            if idx >= 0:
                self._label_combo.setCurrentIndex(idx)
        layout.addRow("Label:", self._label_combo)

        self._start_spin = QDoubleSpinBox()
        self._start_spin.setRange(0, 86400)
        self._start_spin.setDecimals(2)
        self._start_spin.setValue(start)
        layout.addRow("Start (s):", self._start_spin)

        self._end_spin = QDoubleSpinBox()
        self._end_spin.setRange(0, 86400)
        self._end_spin.setDecimals(2)
        self._end_spin.setValue(end)
        layout.addRow("End (s):", self._end_spin)

        self._notes = QLineEdit()
        self._notes.setPlaceholderText("Optional note...")
        layout.addRow("Notes:", self._notes)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _update_labels(self):
        self._label_combo.clear()
        cat_id = self._cat_combo.currentData()
        cat = next((c for c in self._project.categories if c.id == cat_id), None)
        if cat:
            for label in cat.labels:
                self._label_combo.addItem(label)

    def _accept(self):
        cat_id = self._cat_combo.currentData()
        label = self._label_combo.currentText()
        start = self._start_spin.value()
        end = self._end_spin.value()
        if end <= start:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid", "End time must be after start time.")
            return
        self._clip = Clip(
            category_id=cat_id, label=label,
            start=start, end=end,
            notes=self._notes.text()
        )
        self.accept()

    def clip(self) -> Clip | None:
        return self._clip
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/dialogs/new_clip_dialog.py
git commit -m "feat: new clip dialog"
```

---

### Task 15: Tag Manager Dialog

**Files:**
- Create: `videotagger/ui/dialogs/tag_manager_dialog.py`

- [ ] **Step 1: Implement**

```python
# videotagger/ui/dialogs/tag_manager_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QInputDialog, QColorDialog, QMessageBox, QLabel,
    QDialogButtonBox, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from videotagger.models.project import Category, Project
from videotagger.data.template_manager import TemplateManager

class TagManagerDialog(QDialog):
    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Tags")
        self.resize(600, 400)
        self._project = project
        self._selected_cat: Category | None = None
        self._setup_ui()
        self._refresh_categories()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # Left: categories
        left = QVBoxLayout()
        left.addWidget(QLabel("Categories"))
        self._cat_list = QListWidget()
        self._cat_list.currentItemChanged.connect(self._on_cat_selected)
        left.addWidget(self._cat_list)
        cat_btns = QHBoxLayout()
        add_cat = QPushButton("+ Add")
        add_cat.clicked.connect(self._add_category)
        rename_cat = QPushButton("Rename")
        rename_cat.clicked.connect(self._rename_category)
        del_cat = QPushButton("Delete")
        del_cat.clicked.connect(self._delete_category)
        color_cat = QPushButton("Color")
        color_cat.clicked.connect(self._change_color)
        for b in [add_cat, rename_cat, del_cat, color_cat]:
            cat_btns.addWidget(b)
        left.addLayout(cat_btns)
        layout.addLayout(left)

        # Right: labels
        right = QVBoxLayout()
        right.addWidget(QLabel("Labels"))
        self._label_list = QListWidget()
        right.addWidget(self._label_list)
        label_btns = QHBoxLayout()
        add_lbl = QPushButton("+ Add")
        add_lbl.clicked.connect(self._add_label)
        rename_lbl = QPushButton("Rename")
        rename_lbl.clicked.connect(self._rename_label)
        del_lbl = QPushButton("Delete")
        del_lbl.clicked.connect(self._delete_label)
        for b in [add_lbl, rename_lbl, del_lbl]:
            label_btns.addWidget(b)
        right.addLayout(label_btns)
        layout.addLayout(right)

        # Bottom buttons
        outer = QVBoxLayout()
        outer.addLayout(layout)
        btm = QHBoxLayout()
        save_tmpl = QPushButton("Save as Template...")
        save_tmpl.clicked.connect(self._save_template)
        load_tmpl = QPushButton("Load Template...")
        load_tmpl.clicked.connect(self._load_template)
        close_btn = QPushButton("Done")
        close_btn.clicked.connect(self.accept)
        btm.addWidget(save_tmpl)
        btm.addWidget(load_tmpl)
        btm.addStretch()
        btm.addWidget(close_btn)
        outer.addLayout(btm)
        self.setLayout(outer)

    def _refresh_categories(self):
        self._cat_list.clear()
        for cat in self._project.categories:
            item = QListWidgetItem(cat.name)
            item.setData(Qt.ItemDataRole.UserRole, cat.id)
            item.setForeground(QColor(cat.color))
            self._cat_list.addItem(item)

    def _refresh_labels(self):
        self._label_list.clear()
        if not self._selected_cat:
            return
        for label in self._selected_cat.labels:
            self._label_list.addItem(label)

    def _on_cat_selected(self, current, previous):
        if not current:
            self._selected_cat = None
            return
        cat_id = current.data(Qt.ItemDataRole.UserRole)
        self._selected_cat = next((c for c in self._project.categories if c.id == cat_id), None)
        self._refresh_labels()

    def _add_category(self):
        name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        if not ok or not name.strip():
            return
        color = QColorDialog.getColor(QColor("#888888"), self, "Choose color")
        if not color.isValid():
            return
        cat = Category(name=name.strip(), color=color.name())
        self._project.categories.append(cat)
        self._refresh_categories()

    def _rename_category(self):
        if not self._selected_cat:
            return
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=self._selected_cat.name)
        if ok and name.strip():
            self._selected_cat.name = name.strip()
            self._refresh_categories()

    def _delete_category(self):
        if not self._selected_cat:
            return
        if QMessageBox.question(self, "Delete", f"Delete '{self._selected_cat.name}' and all its labels?") \
                == QMessageBox.StandardButton.Yes:
            self._project.categories = [c for c in self._project.categories if c.id != self._selected_cat.id]
            self._selected_cat = None
            self._refresh_categories()
            self._refresh_labels()

    def _change_color(self):
        if not self._selected_cat:
            return
        color = QColorDialog.getColor(QColor(self._selected_cat.color), self)
        if color.isValid():
            self._selected_cat.color = color.name()
            self._refresh_categories()

    def _add_label(self):
        if not self._selected_cat:
            return
        name, ok = QInputDialog.getText(self, "Add Label", "Label name:")
        if ok and name.strip():
            self._selected_cat.labels.append(name.strip())
            self._refresh_labels()

    def _rename_label(self):
        item = self._label_list.currentItem()
        if not item or not self._selected_cat:
            return
        old = item.text()
        name, ok = QInputDialog.getText(self, "Rename Label", "New name:", text=old)
        if ok and name.strip():
            idx = self._selected_cat.labels.index(old)
            self._selected_cat.labels[idx] = name.strip()
            self._refresh_labels()

    def _delete_label(self):
        item = self._label_list.currentItem()
        if not item or not self._selected_cat:
            return
        self._selected_cat.labels.remove(item.text())
        self._refresh_labels()

    def _save_template(self):
        name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        if ok and name.strip():
            TemplateManager.save_user(name.strip(), self._project.categories)
            QMessageBox.information(self, "Saved", f"Template '{name}' saved.")

    def _load_template(self):
        builtin = TemplateManager.list_builtin()
        user = TemplateManager.list_user()
        all_templates = [f"[Built-in] {n}" for n in builtin] + [f"[Custom] {n}" for n in user]
        if not all_templates:
            QMessageBox.information(self, "No Templates", "No templates found.")
            return
        choice, ok = QInputDialog.getItem(self, "Load Template", "Choose template:", all_templates, editable=False)
        if not ok:
            return
        if self._project.clips:
            reply = QMessageBox.question(
                self, "Load Template",
                "Loading a template will replace current categories. Existing clips will keep their category IDs. Continue?"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        if choice.startswith("[Built-in]"):
            cats = TemplateManager.load_builtin(choice.replace("[Built-in] ", ""))
        else:
            cats = TemplateManager.load_user(choice.replace("[Custom] ", ""))
        self._project.categories = cats
        self._selected_cat = None
        self._refresh_categories()
        self._refresh_labels()
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/dialogs/tag_manager_dialog.py
git commit -m "feat: tag manager dialog"
```

---

### Task 16: New Project Dialog

**Files:**
- Create: `videotagger/ui/dialogs/new_project_dialog.py`

- [ ] **Step 1: Implement**

```python
# videotagger/ui/dialogs/new_project_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDialogButtonBox, QFileDialog
)
from videotagger.models.project import Project
from videotagger.data.template_manager import TemplateManager

class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(480)
        self._project: Project | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select video file:"))
        file_row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Path to .mp4 / .mov ...")
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse)
        file_row.addWidget(self._path_edit, stretch=1)
        file_row.addWidget(browse)
        layout.addLayout(file_row)

        layout.addWidget(QLabel("Start from template (optional):"))
        self._tmpl_combo = QComboBox()
        self._tmpl_combo.addItem("— None (blank) —", None)
        for name in TemplateManager.list_builtin():
            self._tmpl_combo.addItem(f"[Built-in] {name}", ("builtin", name))
        for name in TemplateManager.list_user():
            self._tmpl_combo.addItem(f"[Custom] {name}", ("user", name))
        layout.addWidget(self._tmpl_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.m4v);;All Files (*)"
        )
        if path:
            self._path_edit.setText(path)

    def _accept(self):
        path = self._path_edit.text().strip()
        if not path:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Required", "Please select a video file.")
            return
        tmpl_data = self._tmpl_combo.currentData()
        categories = []
        if tmpl_data:
            kind, name = tmpl_data
            if kind == "builtin":
                categories = TemplateManager.load_builtin(name)
            else:
                categories = TemplateManager.load_user(name)
        self._project = Project(video_path=path, categories=categories)
        self.accept()

    def project(self) -> Project | None:
        return self._project
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/dialogs/new_project_dialog.py
git commit -m "feat: new project dialog"
```

---

### Task 17: Export Dialog

**Files:**
- Create: `videotagger/ui/dialogs/export_dialog.py`

- [ ] **Step 1: Implement**

```python
# videotagger/ui/dialogs/export_dialog.py
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QDialogButtonBox, QFileDialog, QProgressDialog
)
from PyQt6.QtCore import Qt
from videotagger.models.project import Project
from videotagger.core.playlist_builder import PlaylistBuilder

class ExportDialog(QDialog):
    def __init__(self, project: Project, playlist_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Playlist")
        self.setMinimumWidth(480)
        self._project = project
        self._playlist_id = playlist_id
        pl = next(p for p in project.playlists if p.id == playlist_id)
        self._clips = PlaylistBuilder(project).get_clips(playlist_id)
        self._setup_ui(pl.name)

    def _setup_ui(self, playlist_name: str):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Exporting playlist: <b>{playlist_name}</b> ({len(self._clips)} clips)"))

        layout.addWidget(QLabel("Output folder:"))
        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit()
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse_folder)
        folder_row.addWidget(self._folder_edit, stretch=1)
        folder_row.addWidget(browse)
        layout.addLayout(folder_row)

        layout.addWidget(QLabel("Export formats:"))
        self._mp4_check = QCheckBox("Cut video files (.mp4)")
        self._mp4_check.setChecked(True)
        self._edl_check = QCheckBox("EDL reference file (.edl)")
        layout.addWidget(self._mp4_check)
        layout.addWidget(self._edl_check)

        # Naming preview
        layout.addWidget(QLabel("File naming preview:"))
        from pathlib import Path
        stem = Path(self._project.video_path).stem
        from videotagger.models.project import Category
        cat_map = {c.id: c for c in self._project.categories}
        if self._clips:
            clip = self._clips[0]
            cat = cat_map.get(clip.category_id)
            cat_name = cat.name if cat else "Unknown"
            preview = f"{stem}_{cat_name}_{clip.label}_001.mp4"
        else:
            preview = f"{stem}_Category_Label_001.mp4"
        lbl = QLabel(f"<code>{preview}</code>")
        layout.addWidget(lbl)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Export")
        buttons.accepted.connect(self._export)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self._folder_edit.setText(folder)

    def _export(self):
        folder = self._folder_edit.text().strip()
        if not folder:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Required", "Please select an output folder.")
            return
        do_mp4 = self._mp4_check.isChecked()
        do_edl = self._edl_check.isChecked()
        if not do_mp4 and not do_edl:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Required", "Select at least one export format.")
            return

        progress = QProgressDialog("Exporting...", "Cancel", 0, len(self._clips), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        errors = []

        if do_mp4:
            from videotagger.export.ffmpeg_exporter import export_playlist_clips
            try:
                export_playlist_clips(self._clips, self._project, folder)
            except RuntimeError as e:
                errors.append(str(e))

        if do_edl:
            from videotagger.export.edl_writer import write_edl
            pl = next(p for p in self._project.playlists if p.id == self._playlist_id)
            edl_path = os.path.join(folder, f"{pl.name}.edl")
            write_edl(pl.name, self._clips, self._project, edl_path)

        progress.close()
        if errors:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Export errors", "\n".join(errors))
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Done", f"Exported to:\n{folder}")
            self.accept()
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/dialogs/export_dialog.py
git commit -m "feat: export dialog"
```

---

### Task 18: Wire Up Main Window (Signals + Keyboard Shortcuts)

**Files:**
- Modify: `videotagger/ui/main_window.py`

- [ ] **Step 1: Connect all signals in `_load_project`**

Add to `main_window.py` — update `_load_project` and add `_setup_shortcuts`:

```python
def _load_project(self, project: Project, path: str | None):
    self._project = project
    self._project_path = path
    self._tagging_engine = TaggingEngine()
    self._save_act.setEnabled(True)
    self.setWindowTitle(f"VideoTagger — {project.video_path}")

    # Wire signals
    self.player.position_changed.connect(self.timeline.set_position)
    self.player.duration_changed.connect(self.timeline.set_duration)
    self.timeline.seek_requested.connect(self.player.seek)
    self.timeline.clip_clicked.connect(self._on_clip_clicked_in_timeline)
    self.tag_panel.label_selected.connect(self._on_label_preselected)
    self.clips_panel.clip_selected.connect(self._on_clip_selected)
    self.clips_panel.export_requested.connect(self._on_export_requested)
    self.clips_panel.present_requested.connect(self._on_present_requested)
    self.clips_panel.new_playlist_requested.connect(self._new_playlist)

    self.player.load(project.video_path)
    self.timeline.set_project(project)
    self.tag_panel.refresh(project)
    self.clips_panel.refresh(project)
    self._setup_shortcuts()

def _setup_shortcuts(self):
    from PyQt6.QtGui import QShortcut
    QShortcut("Space", self).activated.connect(self.player.toggle_play)
    QShortcut("I", self).activated.connect(self._mark_in)
    QShortcut("O", self).activated.connect(self._mark_out)
    QShortcut("Left", self).activated.connect(lambda: self.player.step(-5))
    QShortcut("Right", self).activated.connect(lambda: self.player.step(5))
    QShortcut("Shift+Left", self).activated.connect(lambda: self.player.step(-0.04))
    QShortcut("Shift+Right", self).activated.connect(lambda: self.player.step(0.04))
    QShortcut("[", self).activated.connect(lambda: self.player.set_rate(max(0.25, self.player.get_rate() - 0.25)))
    QShortcut("]", self).activated.connect(lambda: self.player.set_rate(min(4.0, self.player.get_rate() + 0.25)))
    QShortcut("Escape", self).activated.connect(self._cancel_mark)
    QShortcut("Ctrl+Z", self).activated.connect(self._undo_last_clip)
    QShortcut("F11", self).activated.connect(self._toggle_presentation)

def _mark_in(self):
    if self._project and hasattr(self, '_tagging_engine'):
        self._tagging_engine.press_in(self.player.get_position())
        self.statusBar().showMessage(f"Mark IN set at {self.player.get_position():.2f}s — press O to mark end")

def _mark_out(self):
    if not self._project or not hasattr(self, '_tagging_engine'):
        return
    from videotagger.core.tagging_engine import TaggingState
    if self._tagging_engine.state != TaggingState.MARKING:
        return
    try:
        start, end = self._tagging_engine.press_out(self.player.get_position())
    except ValueError as e:
        self.statusBar().showMessage(str(e), 3000)
        return
    preset_cat = getattr(self, '_preset_category_id', None)
    preset_lbl = getattr(self, '_preset_label', None)
    from videotagger.ui.dialogs.new_clip_dialog import NewClipDialog
    dlg = NewClipDialog(self._project, start, end, preset_cat, preset_lbl, self)
    if dlg.exec():
        clip = dlg.clip()
        self._project.clips.append(clip)
        self.timeline.set_project(self._project)
        self.clips_panel.refresh(self._project)
        self.statusBar().showMessage(f"Clip added: {clip.label} ({start:.1f}s – {end:.1f}s)", 3000)

def _cancel_mark(self):
    if hasattr(self, '_tagging_engine'):
        self._tagging_engine.cancel()
        self.statusBar().showMessage("Clip mark cancelled", 2000)

def _undo_last_clip(self):
    if self._project and self._project.clips:
        removed = self._project.clips.pop()
        self.timeline.set_project(self._project)
        self.clips_panel.refresh(self._project)
        self.statusBar().showMessage(f"Undo: removed clip '{removed.label}'", 3000)

def _on_label_preselected(self, category_id: str, label: str):
    self._preset_category_id = category_id
    self._preset_label = label
    self.statusBar().showMessage(f"Pre-selected: {label} — press I to start marking", 3000)

def _on_clip_clicked_in_timeline(self, clip_id: str):
    clip = next((c for c in self._project.clips if c.id == clip_id), None)
    if clip:
        self.player.seek(clip.start)

def _on_clip_selected(self, clip_id: str):
    clip = next((c for c in self._project.clips if c.id == clip_id), None)
    if clip:
        self.player.seek(clip.start)

def _new_playlist(self):
    from PyQt6.QtWidgets import QInputDialog
    from videotagger.core.playlist_builder import PlaylistBuilder
    name, ok = QInputDialog.getText(self, "New Playlist", "Playlist name:")
    if ok and name.strip():
        PlaylistBuilder(self._project).create_playlist(name.strip())
        self.clips_panel.refresh(self._project)

def _on_export_requested(self, playlist_id: str):
    from videotagger.ui.dialogs.export_dialog import ExportDialog
    dlg = ExportDialog(self._project, playlist_id, self)
    dlg.exec()

def _on_present_requested(self, playlist_id: str):
    from videotagger.ui.presentation_window import PresentationWindow
    from videotagger.core.playlist_builder import PlaylistBuilder
    clips = PlaylistBuilder(self._project).get_clips(playlist_id)
    pl = next(p for p in self._project.playlists if p.id == playlist_id)
    self._presentation = PresentationWindow(
        self._project.video_path, clips, pl.name, self
    )
    self._presentation.showFullScreen()

def _toggle_presentation(self):
    # If a playlist is selected, open it; otherwise do nothing
    pass

def closeEvent(self, event):
    from PyQt6.QtWidgets import QMessageBox
    if self._project and not self._project_path:
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Save before closing?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Save:
            self._save_project()
        elif reply == QMessageBox.StandardButton.Cancel:
            event.ignore()
            return
    event.accept()
```

Add import at top of `main_window.py`:
```python
from videotagger.core.tagging_engine import TaggingEngine
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/main_window.py
git commit -m "feat: wire up signals and keyboard shortcuts in main window"
```

---

### Task 19: Presentation Mode

**Files:**
- Create: `videotagger/ui/presentation_window.py`

- [ ] **Step 1: Implement**

```python
# videotagger/ui/presentation_window.py
import sys
import vlc
from typing import List
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QFont, QColor
from videotagger.models.project import Clip

class PresentationWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self, video_path: str, clips: List[Clip], playlist_name: str, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Presentation Mode")
        self.setStyleSheet("background: black;")
        self._video_path = video_path
        self._clips = clips
        self._playlist_name = playlist_name
        self._current_index = 0
        self._instance = vlc.Instance("--no-xlib")
        self._player = self._instance.media_player_new()
        self._hud_visible = True
        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        self.setLayout(None)  # absolute positioning for HUD overlay

        # VLC renders directly to this widget's window handle
        if sys.platform == "win32":
            self._player.set_hwnd(int(self.winId()))
        elif sys.platform == "darwin":
            self._player.set_nsobject(int(self.winId()))
        else:
            self._player.set_xwindow(int(self.winId()))

        # HUD overlay widget
        self._hud = QWidget(self)
        self._hud.setStyleSheet("background: transparent;")

        # Top-left: playlist name
        self._name_label = QLabel(self._playlist_name, self._hud)
        self._name_label.setStyleSheet("color: white; background: rgba(0,0,0,160); padding: 4px 8px;")
        self._name_label.setFont(QFont("Arial", 12))
        self._name_label.move(12, 12)
        self._name_label.adjustSize()

        # Bottom-left: clip label
        self._clip_label = QLabel("", self._hud)
        self._clip_label.setStyleSheet("color: white; background: rgba(0,0,0,160); padding: 4px 8px;")
        self._clip_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))

        # Bottom-right: counter
        self._counter_label = QLabel("", self._hud)
        self._counter_label.setStyleSheet("color: white; background: rgba(0,0,0,160); padding: 4px 8px;")
        self._counter_label.setFont(QFont("Arial", 12))

        # Centre-bottom: controls
        self._prev_btn = QPushButton("⏮", self._hud)
        self._play_btn = QPushButton("⏸", self._hud)
        self._next_btn = QPushButton("⏭", self._hud)
        for btn in [self._prev_btn, self._play_btn, self._next_btn]:
            btn.setStyleSheet("color: white; background: rgba(0,0,0,160); border: none; font-size: 20px; padding: 6px 12px;")
            btn.setFixedSize(50, 40)
        self._prev_btn.clicked.connect(self._prev_clip)
        self._play_btn.clicked.connect(self._toggle_play)
        self._next_btn.clicked.connect(self._next_clip)

        self.setMouseTracking(True)

    def _setup_timer(self):
        # Poll for clip end
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(200)
        self._poll_timer.timeout.connect(self._check_clip_end)

        # HUD fade timer
        self._hud_timer = QTimer(self)
        self._hud_timer.setSingleShot(True)
        self._hud_timer.setInterval(3000)
        self._hud_timer.timeout.connect(self._hide_hud)

    def showFullScreen(self):
        super().showFullScreen()
        self._play_clip(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.resize(self.size())
        self._reposition_hud()

    def _reposition_hud(self):
        w, h = self.width(), self.height()
        self._clip_label.move(12, h - 50)
        self._clip_label.adjustSize()
        self._counter_label.adjustSize()
        self._counter_label.move(w - self._counter_label.width() - 12, h - 50)
        cx = (w - 160) // 2
        self._prev_btn.move(cx, h - 52)
        self._play_btn.move(cx + 55, h - 52)
        self._next_btn.move(cx + 110, h - 52)

    def _play_clip(self, index: int):
        if index < 0 or index >= len(self._clips):
            return
        self._current_index = index
        clip = self._clips[index]
        media = self._instance.media_new(self._video_path)
        self._player.set_media(media)
        self._player.play()
        self._player.set_time(int(clip.start * 1000))
        self._poll_timer.start()
        self._update_hud_labels()

    def _check_clip_end(self):
        if not self._clips:
            return
        clip = self._clips[self._current_index]
        if self._player.get_time() / 1000.0 >= clip.end:
            self._poll_timer.stop()
            if self._current_index + 1 < len(self._clips):
                QTimer.singleShot(1000, lambda: self._play_clip(self._current_index + 1))
            else:
                self._player.pause()
                self._play_btn.setText("▶")

    def _update_hud_labels(self):
        clip = self._clips[self._current_index]
        self._clip_label.setText(clip.label)
        self._clip_label.adjustSize()
        self._counter_label.setText(f"{self._current_index + 1} / {len(self._clips)}")
        self._counter_label.adjustSize()
        self._reposition_hud()

    def _toggle_play(self):
        if self._player.is_playing():
            self._player.pause()
            self._play_btn.setText("▶")
        else:
            self._player.play()
            self._play_btn.setText("⏸")

    def _prev_clip(self):
        self._poll_timer.stop()
        self._play_clip(max(0, self._current_index - 1))

    def _next_clip(self):
        self._poll_timer.stop()
        self._play_clip(min(len(self._clips) - 1, self._current_index + 1))

    def _hide_hud(self):
        self._hud.setVisible(False)
        self._hud_visible = False

    def _show_hud(self):
        self._hud.setVisible(True)
        self._hud_visible = True
        self._hud_timer.start()

    def mouseMoveEvent(self, event):
        self._show_hud()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
            self._poll_timer.stop()
            self._player.stop()
            self.close()
            self.closed.emit()
        elif key == Qt.Key.Key_Space:
            self._toggle_play()
        elif key == Qt.Key.Key_Left:
            self._prev_clip()
        elif key == Qt.Key.Key_Right:
            self._next_clip()
        else:
            super().keyPressEvent(event)
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/presentation_window.py
git commit -m "feat: presentation mode (full-screen playlist playback)"
```

---

### Task 20: Settings Persistence

**Files:**
- Create: `videotagger/data/settings_manager.py`
- Modify: `videotagger/ui/main_window.py`

- [ ] **Step 1: Implement settings manager**

```python
# videotagger/data/settings_manager.py
import json, os
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
```

- [ ] **Step 2: Add save/restore to MainWindow**

Add to `__init__` in `MainWindow` (after `_setup_ui`):

```python
self._restore_settings()
```

Add methods to `MainWindow`:

```python
def _restore_settings(self):
    from videotagger.data.settings_manager import SettingsManager
    s = SettingsManager.load()
    if "geometry" in s:
        from PyQt6.QtCore import QByteArray
        import base64
        self.restoreGeometry(QByteArray(base64.b64decode(s["geometry"])))
    self._recent_files = s.get("recent_files", [])

def _save_settings(self):
    from videotagger.data.settings_manager import SettingsManager
    import base64
    SettingsManager.save({
        "geometry": base64.b64encode(bytes(self.saveGeometry())).decode(),
        "recent_files": getattr(self, "_recent_files", []),
    })

def closeEvent(self, event):
    self._save_settings()
    from PyQt6.QtWidgets import QMessageBox
    if self._project and not self._project_path:
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Save before closing?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Save:
            self._save_project()
        elif reply == QMessageBox.StandardButton.Cancel:
            event.ignore()
            return
    event.accept()
```

- [ ] **Step 3: Commit**

```bash
git add videotagger/data/settings_manager.py videotagger/ui/main_window.py
git commit -m "feat: settings persistence (window geometry, recent files)"
```

---

### Task 21: Error Handling — Missing Video

**Files:**
- Modify: `videotagger/ui/main_window.py`

- [ ] **Step 1: Add missing-video recovery to `_load_project`**

Update the `_load_project` method — before calling `self.player.load(project.video_path)`, add:

```python
import os
from PyQt6.QtWidgets import QMessageBox, QFileDialog

if not os.path.exists(project.video_path):
    reply = QMessageBox.warning(
        self, "Video Not Found",
        f"Video file not found:\n{project.video_path}\n\nLocate it?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if reply == QMessageBox.StandardButton.Yes:
        new_path, _ = QFileDialog.getOpenFileName(
            self, "Locate Video", "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.m4v);;All Files (*)"
        )
        if new_path:
            project.video_path = new_path
        else:
            return  # User cancelled — don't load
    else:
        return
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/main_window.py
git commit -m "feat: handle missing video file on project open"
```

---

### Task 22: PyInstaller Packaging

**Files:**
- Create: `VideoTagger.spec`
- Create: `build.py`

- [ ] **Step 1: Create the spec file**

```python
# VideoTagger.spec
import os
from pathlib import Path
import vlc

vlc_dir = Path(vlc.__file__).parent

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[
        (str(vlc_dir / 'libvlc.dll'), '.'),
        (str(vlc_dir / 'libvlccore.dll'), '.'),
    ],
    datas=[
        ('videotagger/resources', 'videotagger/resources'),
        (str(vlc_dir / 'plugins'), 'plugins'),
    ],
    hiddenimports=['vlc'],
    hookspath=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoTagger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)
```

- [ ] **Step 2: Create build helper**

```python
# build.py
import subprocess, sys

def main():
    print("Building VideoTagger.exe...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "VideoTagger.spec"],
        check=True
    )
    print("Build complete. Output in dist/VideoTagger.exe")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Download ffmpeg binary**

Download the Windows ffmpeg static build from https://github.com/BtbN/FFmpeg-Builds/releases and place `ffmpeg.exe` at:

```
videotagger/resources/ffmpeg.exe
```

(This file is large — add it to `.gitignore` and document the download step for teammates.)

Add to `.gitignore`:
```
videotagger/resources/ffmpeg.exe
dist/
build/
*.spec.bak
__pycache__/
*.pyc
.venv/
```

- [ ] **Step 4: Test the build**

```bash
python build.py
```

Expected: `dist/VideoTagger.exe` is created. Double-click to launch — verify the main window opens.

- [ ] **Step 5: Commit**

```bash
git add VideoTagger.spec build.py .gitignore
git commit -m "feat: PyInstaller packaging spec and build script"
```

---

## Running All Tests

```bash
pytest tests/ -v --ignore=tests/test_main_window.py
```

UI tests require a display:
```bash
pytest tests/test_main_window.py -v
```

Full suite:
```bash
pytest tests/ -v
```

Expected: all tests pass.
