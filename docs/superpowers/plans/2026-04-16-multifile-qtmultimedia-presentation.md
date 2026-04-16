# Multi-file Projects, QtMultimedia, and Presentation UX — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace VLC with PyQt6 QtMultimedia, support multi-file projects merged via FFmpeg, add Tab/Shift+Tab presentation navigation, and add a Package Project export.

**Architecture:** The data model gains `source_video_paths + merged_video_path` (v1 files migrate transparently). A new `VideoMerger` uses FFmpeg concat to stitch files at project creation. `PlayerWidget` and `PresentationWindow` are rewritten using `QMediaPlayer + QVideoWidget`, which lets the existing `DrawingOverlay` render correctly.

**Tech Stack:** PyQt6 ≥ 6.6.0, `PyQt6.QtMultimedia` (QMediaPlayer, QAudioOutput), `PyQt6.QtMultimediaWidgets` (QVideoWidget), FFmpeg (bundled `ffmpeg.exe`), pytest, pytest-qt.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `videotagger/models/project.py` | v2 data model, dict serialisation |
| Modify | `videotagger/data/project_manager.py` | v1→v2 migration, relative path resolution |
| Create | `videotagger/core/video_merger.py` | FFmpeg concat logic (copy → H.264 fallback) |
| Create | `videotagger/ui/dialogs/merge_progress_dialog.py` | Threaded merge UI |
| Modify | `videotagger/ui/dialogs/new_project_dialog.py` | Multi-file picker, merge location |
| Modify | `videotagger/ui/player_widget.py` | VLC → QMediaPlayer + QVideoWidget |
| Modify | `videotagger/ui/presentation_window.py` | VLC → QMediaPlayer; Tab/Shift+Tab nav |
| Modify | `videotagger/ui/main_window.py` | Package Project menu; updated _load_project |
| Modify | `videotagger/export/ffmpeg_exporter.py` | video_path → merged_video_path |
| Modify | `tests/test_models.py` | v2 model tests + v1 migration test |
| Modify | `tests/test_project_manager.py` | v2 save/load + migration tests |
| Create | `tests/test_video_merger.py` | VideoMerger unit tests (subprocess mocked) |
| Modify | `tests/test_ui.py` | Update smoke tests for new widget API |
| Modify | `requirements.txt` | Remove python-vlc |
| Modify | `VideoTagger.spec` | Remove VLC binaries/datas |

---

## Task 1: Update Project Data Model (v1 → v2)

**Files:**
- Modify: `videotagger/models/project.py`
- Modify: `videotagger/export/ffmpeg_exporter.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for the v2 model**

Replace the contents of `tests/test_models.py`:

```python
import pytest
from videotagger.models.project import Category, Clip, Playlist, Project
from videotagger.models.project import project_to_dict, project_from_dict


def test_category_has_auto_id():
    cat = Category(name="Offence", color="#e94560", labels=["Goal", "Behind"])
    assert cat.id is not None
    assert len(cat.id) == 36


def test_clip_has_auto_id():
    clip = Clip(category_id="cat-1", label="Goal", start=10.0, end=20.0)
    assert clip.id is not None


def test_project_v2_round_trip():
    cat = Category(name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(category_id=cat.id, label="Goal", start=10.5, end=18.2, notes="Great goal")
    pl = Playlist(name="Best Goals", clip_ids=[clip.id])
    proj = Project(
        source_video_paths=["C:/Q1.mp4", "C:/Q2.mp4"],
        merged_video_path="C:/game_merged.mp4",
        categories=[cat], clips=[clip], playlists=[pl],
    )
    d = project_to_dict(proj)
    proj2 = project_from_dict(d)
    assert proj2.source_video_paths == ["C:/Q1.mp4", "C:/Q2.mp4"]
    assert proj2.merged_video_path == "C:/game_merged.mp4"
    assert proj2.categories[0].name == "Offence"
    assert proj2.clips[0].start == 10.5
    assert proj2.clips[0].notes == "Great goal"
    assert proj2.playlists[0].name == "Best Goals"
    assert proj2.version == 2


def test_project_from_v1_dict_migrates():
    """v1 .vtp files (video_path key) are transparently upgraded to v2."""
    d = {
        "version": 1,
        "video_path": "C:/old_game.mp4",
        "categories": [],
        "clips": [],
        "playlists": [],
    }
    proj = project_from_dict(d)
    assert proj.source_video_paths == ["C:/old_game.mp4"]
    assert proj.merged_video_path == "C:/old_game.mp4"
    assert proj.version == 2


def test_project_from_dict_missing_notes_defaults_empty():
    d = {
        "version": 2,
        "source_video_paths": ["C:/v.mp4"],
        "merged_video_path": "C:/v.mp4",
        "categories": [],
        "clips": [{"id": "c1", "category_id": "cat1", "label": "Goal",
                   "start": 1.0, "end": 2.0}],
        "playlists": [],
    }
    proj = project_from_dict(d)
    assert proj.clips[0].notes == ""
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_models.py -v
```
Expected: FAIL — `Project` has no `source_video_paths`.

- [ ] **Step 3: Rewrite the Project model**

Replace `videotagger/models/project.py` entirely:

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_models.py -v
```
Expected: all PASS.

- [ ] **Step 5: Update ffmpeg_exporter to use merged_video_path**

In `videotagger/export/ffmpeg_exporter.py`, change line 58:

```python
# Before
out = export_clip(clip, cat_name, label_counts[key], project.video_path, output_dir)

# After
out = export_clip(clip, cat_name, label_counts[key], project.merged_video_path, output_dir)
```

- [ ] **Step 6: Commit**

```bash
git add videotagger/models/project.py videotagger/export/ffmpeg_exporter.py tests/test_models.py
git commit -m "feat: upgrade Project model to v2 with source_video_paths + merged_video_path"
```

---

## Task 2: Migrate ProjectManager to v2

**Files:**
- Modify: `videotagger/data/project_manager.py`
- Test: `tests/test_project_manager.py`

- [ ] **Step 1: Write failing tests**

Replace `tests/test_project_manager.py`:

```python
import json, os, pytest
from videotagger.models.project import Category, Clip, Project
from videotagger.data.project_manager import ProjectManager


@pytest.fixture
def sample_project(tmp_path):
    cat = Category(name="Offence", color="#e94560", labels=["Goal"])
    clip = Clip(category_id=cat.id, label="Goal", start=10.0, end=15.0)
    return Project(
        source_video_paths=[str(tmp_path / "video.mp4")],
        merged_video_path=str(tmp_path / "video.mp4"),
        categories=[cat],
        clips=[clip],
    )


def test_save_creates_file(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    assert path.exists()


def test_save_writes_version_2(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    with open(path) as f:
        data = json.load(f)
    assert data["version"] == 2
    assert "source_video_paths" in data
    assert "merged_video_path" in data


def test_load_round_trip(tmp_path, sample_project):
    path = tmp_path / "test.vtp"
    ProjectManager.save(sample_project, str(path))
    loaded = ProjectManager.load(str(path))
    assert loaded.source_video_paths == sample_project.source_video_paths
    assert loaded.merged_video_path == sample_project.merged_video_path
    assert loaded.clips[0].start == 10.0


def test_load_v1_file_migrates(tmp_path):
    """A v1 .vtp file (video_path key) loads without error and is migrated."""
    v1_data = {
        "version": 1,
        "video_path": str(tmp_path / "old.mp4"),
        "categories": [],
        "clips": [],
        "playlists": [],
    }
    path = tmp_path / "old.vtp"
    path.write_text(json.dumps(v1_data))
    proj = ProjectManager.load(str(path))
    assert proj.merged_video_path == str(tmp_path / "old.mp4")
    assert proj.source_video_paths == [str(tmp_path / "old.mp4")]


def test_load_packaged_relative_path(tmp_path):
    """A packaged .vtp with merged_video_path='./video.mp4' is resolved relative to the .vtp."""
    pkg_dir = tmp_path / "MyGame"
    pkg_dir.mkdir()
    vtp_data = {
        "version": 2,
        "source_video_paths": ["./video.mp4"],
        "merged_video_path": "./video.mp4",
        "categories": [], "clips": [], "playlists": [],
    }
    vtp_path = pkg_dir / "project.vtp"
    vtp_path.write_text(json.dumps(vtp_data))
    proj = ProjectManager.load(str(vtp_path))
    assert os.path.isabs(proj.merged_video_path)
    assert proj.merged_video_path == str(pkg_dir / "video.mp4")


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        ProjectManager.load("nonexistent.vtp")


def test_load_corrupt_file_raises(tmp_path):
    path = tmp_path / "bad.vtp"
    path.write_text("not json")
    with pytest.raises(ValueError):
        ProjectManager.load(str(path))
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_project_manager.py -v
```
Expected: FAIL on `test_save_writes_version_2`, `test_load_packaged_relative_path`, `test_load_v1_file_migrates`.

- [ ] **Step 3: Rewrite ProjectManager**

Replace `videotagger/data/project_manager.py`:

```python
import json
import os
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

        project = project_from_dict(data)

        # Resolve relative paths against the .vtp file's directory
        vtp_dir = os.path.dirname(os.path.abspath(path))
        if not os.path.isabs(project.merged_video_path):
            project.merged_video_path = os.path.normpath(
                os.path.join(vtp_dir, project.merged_video_path)
            )
        project.source_video_paths = [
            os.path.normpath(os.path.join(vtp_dir, p)) if not os.path.isabs(p) else p
            for p in project.source_video_paths
        ]
        return project
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_project_manager.py -v
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add videotagger/data/project_manager.py tests/test_project_manager.py
git commit -m "feat: ProjectManager handles v1 migration and relative paths for packaged projects"
```

---

## Task 3: VideoMerger — FFmpeg Concat Logic

**Files:**
- Create: `videotagger/core/video_merger.py`
- Create: `tests/test_video_merger.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_video_merger.py`:

```python
import pytest
import shutil
from unittest.mock import patch, MagicMock
from videotagger.core.video_merger import VideoMerger, MergeError


@pytest.fixture
def merger():
    return VideoMerger(ffmpeg_path="ffmpeg")


def test_single_file_copies_in_place(tmp_path, merger):
    src = tmp_path / "src.mp4"
    src.write_bytes(b"fake video data")
    dst = tmp_path / "out.mp4"
    merger.merge([str(src)], str(dst))
    assert dst.exists()
    assert dst.read_bytes() == b"fake video data"


def _make_mock_proc(returncode: int):
    proc = MagicMock()
    proc.stderr = iter([])
    proc.returncode = returncode
    proc.poll.return_value = returncode
    return proc


def test_multiple_files_tries_copy_first(tmp_path, merger):
    src1 = tmp_path / "a.mp4"
    src2 = tmp_path / "b.mp4"
    src1.write_bytes(b"a")
    src2.write_bytes(b"b")
    dst = tmp_path / "out.mp4"

    with patch("subprocess.Popen", return_value=_make_mock_proc(0)) as mock_popen:
        merger.merge([str(src1), str(src2)], str(dst))

    cmd = mock_popen.call_args[0][0]
    assert "-c" in cmd
    assert "copy" in cmd


def test_falls_back_to_h264_when_copy_fails(tmp_path, merger):
    src1 = tmp_path / "a.mp4"
    src2 = tmp_path / "b.mp4"
    src1.write_bytes(b"a")
    src2.write_bytes(b"b")
    dst = tmp_path / "out.mp4"

    call_count = 0

    def side_effect(cmd, **kwargs):
        nonlocal call_count
        call_count += 1
        return _make_mock_proc(1 if call_count == 1 else 0)

    with patch("subprocess.Popen", side_effect=side_effect):
        merger.merge([str(src1), str(src2)], str(dst))

    assert call_count == 2


def test_raises_merge_error_when_both_passes_fail(tmp_path, merger):
    src1 = tmp_path / "a.mp4"
    src2 = tmp_path / "b.mp4"
    src1.write_bytes(b"a")
    src2.write_bytes(b"b")
    dst = tmp_path / "out.mp4"

    with patch("subprocess.Popen", return_value=_make_mock_proc(1)):
        with pytest.raises(MergeError):
            merger.merge([str(src1), str(src2)], str(dst))


def test_progress_callback_called(tmp_path, merger):
    src1 = tmp_path / "a.mp4"
    src2 = tmp_path / "b.mp4"
    src1.write_bytes(b"a")
    src2.write_bytes(b"b")
    dst = tmp_path / "out.mp4"
    messages = []

    with patch("subprocess.Popen", return_value=_make_mock_proc(0)):
        merger.merge([str(src1), str(src2)], str(dst), on_progress=messages.append)

    assert any("pass 1" in m.lower() or "copy" in m.lower() for m in messages)
```

- [ ] **Step 2: Run to confirm failure**

```
pytest tests/test_video_merger.py -v
```
Expected: FAIL — module not found.

- [ ] **Step 3: Implement VideoMerger**

Create `videotagger/core/video_merger.py`:

```python
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Callable, List


class MergeError(Exception):
    pass


class VideoMerger:
    """Merges multiple video files into one using FFmpeg concat demuxer.

    Tries -c copy (lossless, fast) first. Falls back to H.264/AAC transcode
    if sources have mismatched codecs.
    """

    def __init__(self, ffmpeg_path: str):
        self._ffmpeg = ffmpeg_path
        self._proc: subprocess.Popen | None = None

    def merge(
        self,
        sources: List[str],
        output: str,
        on_progress: Callable[[str], None] | None = None,
    ) -> None:
        """Merge sources into output.

        Single source: copied directly (no FFmpeg needed).
        Multiple sources: concat demuxer with copy, then H.264 fallback.
        Raises MergeError if FFmpeg fails on both passes.
        """
        if len(sources) == 1:
            shutil.copy2(sources[0], output)
            return

        fd, filelist_path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for src in sources:
                    escaped = src.replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            base_cmd = [
                self._ffmpeg, "-y", "-f", "concat", "-safe", "0",
                "-i", filelist_path,
            ]

            if on_progress:
                on_progress("Merging — pass 1: copy (fast)…")
            if self._run(base_cmd + ["-c", "copy", output], on_progress):
                return

            if on_progress:
                on_progress("Copy pass failed — re-encoding to H.264…")
            if self._run(
                base_cmd + ["-c:v", "libx264", "-crf", "18", "-c:a", "aac", output],
                on_progress,
            ):
                return

            raise MergeError(
                "FFmpeg failed to merge the video files on both passes. "
                "Check that all source files are valid and not corrupted."
            )
        finally:
            if os.path.exists(filelist_path):
                os.unlink(filelist_path)

    def cancel(self) -> None:
        """Terminate a running FFmpeg process."""
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()

    def _run(
        self,
        cmd: List[str],
        on_progress: Callable[[str], None] | None,
    ) -> bool:
        self._proc = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in self._proc.stderr:
            if on_progress and "time=" in line:
                for part in line.split():
                    if part.startswith("time="):
                        on_progress(f"Processed: {part[5:]}")
                        break
        self._proc.wait()
        return self._proc.returncode == 0
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_video_merger.py -v
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add videotagger/core/video_merger.py tests/test_video_merger.py
git commit -m "feat: add VideoMerger with FFmpeg concat copy→H.264 fallback"
```

---

## Task 4: MergeProgressDialog

**Files:**
- Create: `videotagger/ui/dialogs/merge_progress_dialog.py`

No isolated unit test — tested as part of Task 5 manual flow.

- [ ] **Step 1: Create MergeProgressDialog**

Create `videotagger/ui/dialogs/merge_progress_dialog.py`:

```python
from __future__ import annotations

from typing import List

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox,
    QProgressBar, QPushButton, QVBoxLayout,
)

from videotagger.core.video_merger import VideoMerger


class _MergeThread(QThread):
    progress = pyqtSignal(str)
    succeeded = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, merger: VideoMerger, sources: List[str], output: str):
        super().__init__()
        self._merger = merger
        self._sources = sources
        self._output = output

    def run(self) -> None:
        try:
            self._merger.merge(self._sources, self._output,
                               on_progress=self.progress.emit)
            self.succeeded.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class MergeProgressDialog(QDialog):
    """Modal dialog that runs VideoMerger in a background thread."""

    def __init__(
        self,
        merger: VideoMerger,
        sources: List[str],
        output: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Merging Video Files")
        self.setModal(True)
        self.setMinimumWidth(420)
        self._merger = merger
        self._success = False

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._status_label = QLabel("Starting…")
        layout.addWidget(self._status_label)

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)  # indeterminate
        layout.addWidget(self._bar)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)
        layout.addLayout(btn_row)

        self._thread = _MergeThread(merger, sources, output)
        self._thread.progress.connect(self._status_label.setText)
        self._thread.succeeded.connect(self._on_success)
        self._thread.failed.connect(self._on_failure)
        self._thread.start()

    def was_successful(self) -> bool:
        return self._success

    def _on_cancel(self) -> None:
        self._merger.cancel()
        self._thread.wait(2000)
        self.reject()

    def _on_success(self) -> None:
        self._success = True
        self.accept()

    def _on_failure(self, message: str) -> None:
        QMessageBox.critical(self, "Merge Failed", message)
        self.reject()
```

- [ ] **Step 2: Commit**

```bash
git add videotagger/ui/dialogs/merge_progress_dialog.py
git commit -m "feat: add MergeProgressDialog for threaded FFmpeg merge"
```

---

## Task 5: NewProjectDialog — Multi-file Support

**Files:**
- Modify: `videotagger/ui/dialogs/new_project_dialog.py`

- [ ] **Step 1: Rewrite NewProjectDialog**

Replace `videotagger/ui/dialogs/new_project_dialog.py`:

```python
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDialogButtonBox, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QWidget,
)

from videotagger.models.project import Project
from videotagger.data.template_manager import TemplateManager


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(520)
        self._project: Project | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── Source files ────────────────────────────────────────────────
        layout.addWidget(QLabel("Video file(s) — add multiple for a split-file match:"))

        self._file_list = QListWidget()
        self._file_list.setMaximumHeight(120)
        layout.addWidget(self._file_list)

        file_btn_row = QHBoxLayout()
        add_btn = QPushButton("Add File(s)…")
        add_btn.clicked.connect(self._add_files)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        up_btn = QPushButton("↑")
        up_btn.setFixedWidth(32)
        up_btn.clicked.connect(self._move_up)
        down_btn = QPushButton("↓")
        down_btn.setFixedWidth(32)
        down_btn.clicked.connect(self._move_down)
        file_btn_row.addWidget(add_btn)
        file_btn_row.addWidget(remove_btn)
        file_btn_row.addStretch()
        file_btn_row.addWidget(up_btn)
        file_btn_row.addWidget(down_btn)
        layout.addLayout(file_btn_row)

        # ── Merged output location (shown only when >1 file) ────────────
        self._merge_section = QWidget()
        merge_layout = QVBoxLayout(self._merge_section)
        merge_layout.setContentsMargins(0, 0, 0, 0)
        merge_layout.addWidget(QLabel("Save merged video to:"))
        merge_row = QHBoxLayout()
        self._merge_path_edit = QLineEdit()
        self._merge_path_edit.setPlaceholderText("Path for merged output file…")
        merge_browse = QPushButton("Browse…")
        merge_browse.clicked.connect(self._browse_merge_output)
        merge_row.addWidget(self._merge_path_edit, stretch=1)
        merge_row.addWidget(merge_browse)
        merge_layout.addLayout(merge_row)
        layout.addWidget(self._merge_section)
        self._merge_section.hide()

        self._file_list.model().rowsInserted.connect(self._update_merge_section)
        self._file_list.model().rowsRemoved.connect(self._update_merge_section)

        # ── Template ────────────────────────────────────────────────────
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

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Video File(s)", "",
            "Video Files (*.mp4 *.mov *.avi *.mkv *.m4v);;All Files (*)",
        )
        for path in paths:
            self._file_list.addItem(QListWidgetItem(path))
        self._update_merge_default()

    def _remove_selected(self):
        for item in self._file_list.selectedItems():
            self._file_list.takeItem(self._file_list.row(item))

    def _move_up(self):
        row = self._file_list.currentRow()
        if row > 0:
            item = self._file_list.takeItem(row)
            self._file_list.insertItem(row - 1, item)
            self._file_list.setCurrentRow(row - 1)

    def _move_down(self):
        row = self._file_list.currentRow()
        if row < self._file_list.count() - 1:
            item = self._file_list.takeItem(row)
            self._file_list.insertItem(row + 1, item)
            self._file_list.setCurrentRow(row + 1)

    def _update_merge_section(self):
        self._merge_section.setVisible(self._file_list.count() > 1)

    def _update_merge_default(self):
        if self._file_list.count() > 1 and not self._merge_path_edit.text().strip():
            first = self._file_list.item(0).text()
            stem = Path(first).stem
            default = str(Path(first).parent / f"{stem}_merged.mp4")
            self._merge_path_edit.setText(default)

    def _browse_merge_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged Video As", self._merge_path_edit.text(),
            "MP4 Video (*.mp4)",
        )
        if path:
            if not path.endswith(".mp4"):
                path += ".mp4"
            self._merge_path_edit.setText(path)

    def _source_paths(self) -> List[str]:
        return [
            self._file_list.item(i).text()
            for i in range(self._file_list.count())
        ]

    def _accept(self):
        sources = self._source_paths()
        if not sources:
            QMessageBox.warning(self, "Required", "Please add at least one video file.")
            return

        for src in sources:
            if not os.path.exists(src):
                QMessageBox.warning(self, "File Not Found", f"File not found:\n{src}")
                return

        if len(sources) == 1:
            merged_path = sources[0]
        else:
            merged_path = self._merge_path_edit.text().strip()
            if not merged_path:
                QMessageBox.warning(self, "Required",
                                    "Please specify where to save the merged video.")
                return
            # Run merge
            from videotagger.core.video_merger import VideoMerger
            from videotagger.ui.dialogs.merge_progress_dialog import MergeProgressDialog
            from videotagger.export.ffmpeg_exporter import _ffmpeg_path
            merger = VideoMerger(_ffmpeg_path())
            dlg = MergeProgressDialog(merger, sources, merged_path, self)
            if not dlg.exec() or not dlg.was_successful():
                return
            if not os.path.exists(merged_path):
                QMessageBox.critical(self, "Merge Failed",
                                     "Merged file was not created.")
                return

        tmpl_data = self._tmpl_combo.currentData()
        categories = []
        if tmpl_data:
            kind, name = tmpl_data
            categories = (TemplateManager.load_builtin(name) if kind == "builtin"
                          else TemplateManager.load_user(name))

        self._project = Project(
            source_video_paths=sources,
            merged_video_path=merged_path,
            categories=categories,
        )
        self.accept()

    def project(self) -> Project | None:
        return self._project
```

- [ ] **Step 2: Run existing UI smoke test to verify widget still instantiates**

```
pytest tests/test_ui.py::test_main_window_opens -v
```
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add videotagger/ui/dialogs/new_project_dialog.py
git commit -m "feat: NewProjectDialog supports multi-file selection with FFmpeg merge"
```

---

## Task 6: PlayerWidget — VLC → QtMultimedia

**Files:**
- Modify: `videotagger/ui/player_widget.py`
- Test: `tests/test_ui.py`

- [ ] **Step 1: Update the player_widget smoke test**

In `tests/test_ui.py`, replace `test_player_widget_creates`:

```python
def test_player_widget_creates(qtbot):
    from videotagger.ui.player_widget import PlayerWidget
    w = PlayerWidget()
    qtbot.addWidget(w)
    w.show()
    assert w.isVisible()
    assert hasattr(w, "position_changed")
    assert hasattr(w, "duration_changed")
    # Public API surface
    assert callable(w.load)
    assert callable(w.seek)
    assert callable(w.step)
    assert callable(w.toggle_play)
    assert callable(w.get_position)
    assert callable(w.get_rate)
    assert callable(w.set_rate)
```

Run to confirm current state passes:
```
pytest tests/test_ui.py::test_player_widget_creates -v
```

- [ ] **Step 2: Rewrite PlayerWidget using QtMultimedia**

Replace `videotagger/ui/player_widget.py`:

```python
from __future__ import annotations

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)


class PlayerWidget(QWidget):
    position_changed = pyqtSignal(float)  # seconds
    duration_changed = pyqtSignal(float)  # seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0.0
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self._setup_ui()
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._video_widget = QVideoWidget()
        self._video_widget.setStyleSheet("background: black;")
        self._video_widget.setMinimumHeight(200)
        self._player.setVideoOutput(self._video_widget)
        layout.addWidget(self._video_widget, stretch=1)

        ctrl_widget = QWidget()
        ctrl_widget.setStyleSheet("background: #090d12; border-top: 1px solid #1e2a38;")
        ctrl_widget.setFixedHeight(36)
        ctrl = QHBoxLayout(ctrl_widget)
        ctrl.setContentsMargins(8, 0, 8, 0)
        ctrl.setSpacing(8)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(32, 26)
        self._play_btn.setStyleSheet(
            "QPushButton { background: #00b09b; color: #000; border: none;"
            " border-radius: 4px; font-size: 11pt; font-weight: bold; }"
            "QPushButton:hover { background: #00d4b8; }"
            "QPushButton:pressed { background: #008f7e; }"
        )
        self._play_btn.clicked.connect(self.toggle_play)
        ctrl.addWidget(self._play_btn)

        mono = QFont("Consolas", 9)
        self._pos_label = QLabel("00:00:00")
        self._pos_label.setFont(mono)
        self._pos_label.setStyleSheet(
            "color: #00b09b; background: transparent; min-width: 58px;"
        )
        ctrl.addWidget(self._pos_label)

        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setRange(0, 10000)
        self._seek_slider.sliderMoved.connect(self._seek_to_slider)
        ctrl.addWidget(self._seek_slider, stretch=1)

        self._dur_label = QLabel("00:00:00")
        self._dur_label.setFont(mono)
        self._dur_label.setStyleSheet(
            "color: #7d8fa3; background: transparent; min-width: 58px;"
        )
        ctrl.addWidget(self._dur_label)

        self._speed_label = QLabel("1.0×")
        self._speed_label.setFixedWidth(44)
        self._speed_label.setStyleSheet(
            "color: #7d8fa3; background: #13191f; border: 1px solid #1e2a38;"
            " border-radius: 3px; padding: 1px 4px; font-size: 8pt;"
        )
        ctrl.addWidget(self._speed_label)

        layout.addWidget(ctrl_widget)

    # ── Public API ──────────────────────────────────────────────────────

    def load(self, path: str) -> None:
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        self._play_btn.setText("⏸")

    def toggle_play(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._play_btn.setText("▶")
        else:
            self._player.play()
            self._play_btn.setText("⏸")

    def get_position(self) -> float:
        return self._player.position() / 1000.0

    def seek(self, seconds: float) -> None:
        self._player.setPosition(int(max(0.0, seconds) * 1000))

    def step(self, seconds: float) -> None:
        self.seek(max(0.0, self.get_position() + seconds))

    def set_rate(self, rate: float) -> None:
        rate = max(0.25, min(4.0, rate))
        self._player.setPlaybackRate(rate)
        self._speed_label.setText(f"{rate:.2g}×")

    def get_rate(self) -> float:
        return self._player.playbackRate()

    # ── Private slots ───────────────────────────────────────────────────

    def _on_position_changed(self, ms: int) -> None:
        pos = ms / 1000.0
        self.position_changed.emit(pos)
        self._pos_label.setText(self._fmt(pos))
        if self._duration > 0:
            self._seek_slider.setValue(int(pos / self._duration * 10000))

    def _on_duration_changed(self, ms: int) -> None:
        self._duration = ms / 1000.0
        self.duration_changed.emit(self._duration)
        self._dur_label.setText(self._fmt(self._duration))

    def _seek_to_slider(self, value: int) -> None:
        if self._duration > 0:
            self.seek(value / 10000.0 * self._duration)

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
```

- [ ] **Step 3: Run smoke test**

```
pytest tests/test_ui.py::test_player_widget_creates -v
```
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add videotagger/ui/player_widget.py tests/test_ui.py
git commit -m "feat: replace VLC with QMediaPlayer+QVideoWidget in PlayerWidget"
```

---

## Task 7: PresentationWindow — QtMultimedia + Tab Navigation

**Files:**
- Modify: `videotagger/ui/presentation_window.py`
- Test: `tests/test_ui.py`

- [ ] **Step 1: Update the presentation smoke test**

In `tests/test_ui.py`, replace `test_presentation_window_creates`:

```python
def test_presentation_window_creates(qtbot):
    from videotagger.ui.presentation_window import PresentationWindow
    w = PresentationWindow("video.mp4", [], "Test Playlist")
    qtbot.addWidget(w)
    w.show()
    assert w.isVisible()
```

Run to confirm current (VLC) state still passes before rewrite:
```
pytest tests/test_ui.py::test_presentation_window_creates -v
```

- [ ] **Step 2: Rewrite PresentationWindow**

Replace `videotagger/ui/presentation_window.py`:

```python
from __future__ import annotations

from typing import List

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPen, QPixmap
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QLabel, QPushButton, QWidget

from videotagger.models.project import Clip

_PEN_COLORS = ["#ff4444", "#ffcc00", "#44aaff", "#44ff88", "#ffffff"]


class DrawingOverlay(QWidget):
    """Transparent freehand pen overlay. Never steals keyboard focus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._canvas: QPixmap | None = None
        self._last_pos = None
        self._color_index = 0
        self._pen_color = QColor(_PEN_COLORS[0])
        self._pen_width = 4

    def cycle_color(self):
        self._color_index = (self._color_index + 1) % len(_PEN_COLORS)
        self._pen_color = QColor(_PEN_COLORS[self._color_index])
        return self._pen_color

    def thicker(self):
        self._pen_width = min(20, self._pen_width + 2)

    def thinner(self):
        self._pen_width = max(2, self._pen_width - 2)

    def clear(self):
        if self._canvas:
            self._canvas.fill(Qt.GlobalColor.transparent)
        self.update()

    def resizeEvent(self, event):
        new_canvas = QPixmap(self.size())
        new_canvas.fill(Qt.GlobalColor.transparent)
        if self._canvas:
            p = QPainter(new_canvas)
            p.drawPixmap(0, 0, self._canvas)
            p.end()
        self._canvas = new_canvas
        super().resizeEvent(event)

    def paintEvent(self, event):
        if self._canvas:
            p = QPainter(self)
            p.drawPixmap(0, 0, self._canvas)
            p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_pos = event.position().toPoint()
        if self.parent():
            self.parent().setFocus()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self._last_pos is None:
            return
        if self._canvas is None:
            self._canvas = QPixmap(self.size())
            self._canvas.fill(Qt.GlobalColor.transparent)
        p = QPainter(self._canvas)
        pen = QPen(self._pen_color, self._pen_width,
                   Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                   Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawLine(self._last_pos, event.position().toPoint())
        p.end()
        self._last_pos = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event):
        self._last_pos = None


class PresentationWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self, video_path: str, clips: List[Clip], playlist_name: str,
                 category_map: dict | None = None, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Presentation Mode")
        self.setStyleSheet("background: black;")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._video_path = video_path
        self._clips = clips
        self._playlist_name = playlist_name
        self._category_map: dict = category_map or {}
        self._current_index = 0
        self._drawing_mode = False
        self._notes_pinned = False
        self._player = QMediaPlayer()
        self._audio = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self._setup_ui()
        self._setup_timers()
        self._player.positionChanged.connect(self._on_position_changed)

    # ── UI setup ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        self._video_widget = QVideoWidget(self)
        self._video_widget.setStyleSheet("background: black;")
        self._video_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._player.setVideoOutput(self._video_widget)

        self._drawing = DrawingOverlay(self)
        self._drawing.hide()

        self._pinned_notes = QLabel("", self)
        self._pinned_notes.setStyleSheet(
            "color:#ffe066; background:rgba(0,0,0,185);"
            "padding:8px 14px; border-radius:5px; border:1px solid rgba(255,220,80,130);"
        )
        self._pinned_notes.setFont(QFont("Arial", 13))
        self._pinned_notes.setWordWrap(True)
        self._pinned_notes.setMaximumWidth(700)
        self._pinned_notes.hide()

        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self._hud.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        hud_s = "color:white; background:rgba(0,0,0,160); padding:4px 8px; border-radius:3px;"
        draw_s = (
            "color:white; background:rgba(0,0,0,160); border:none;"
            "font-size:13px; padding:4px 10px; border-radius:3px;"
            "border:1px solid rgba(255,255,255,60);"
        )

        self._name_label = QLabel(self._playlist_name, self._hud)
        self._name_label.setStyleSheet(hud_s)
        self._name_label.setFont(QFont("Arial", 12))
        self._name_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._clip_label = QLabel("", self._hud)
        self._clip_label.setStyleSheet(hud_s)
        self._clip_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self._clip_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._notes_label = QLabel("", self._hud)
        self._notes_label.setStyleSheet(
            "color:#cccccc; background:rgba(0,0,0,140); padding:3px 8px; border-radius:3px;"
        )
        self._notes_label.setFont(QFont("Arial", 11))
        self._notes_label.setWordWrap(True)
        self._notes_label.setMaximumWidth(600)
        self._notes_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._counter_label = QLabel("", self._hud)
        self._counter_label.setStyleSheet(hud_s)
        self._counter_label.setFont(QFont("Arial", 12))
        self._counter_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._color_btn = QPushButton("● Color", self._hud)
        self._color_btn.setStyleSheet(f"color:{_PEN_COLORS[0]}; {draw_s}")
        self._color_btn.setFixedSize(80, 30)
        self._color_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._color_btn.clicked.connect(self._cycle_color)
        self._color_btn.hide()

        self._thin_btn = QPushButton("− Thin", self._hud)
        self._thin_btn.setStyleSheet(draw_s)
        self._thin_btn.setFixedSize(64, 30)
        self._thin_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._thin_btn.clicked.connect(self._drawing.thinner)
        self._thin_btn.hide()

        self._thick_btn = QPushButton("+ Thick", self._hud)
        self._thick_btn.setStyleSheet(draw_s)
        self._thick_btn.setFixedSize(72, 30)
        self._thick_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._thick_btn.clicked.connect(self._drawing.thicker)
        self._thick_btn.hide()

        self._clear_btn = QPushButton("✕ Clear", self._hud)
        self._clear_btn.setStyleSheet(f"color:#ff8888; {draw_s}")
        self._clear_btn.setFixedSize(72, 30)
        self._clear_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._clear_btn.clicked.connect(self._drawing.clear)
        self._clear_btn.hide()

        self._draw_hint = QLabel("", self._hud)
        self._draw_hint.setStyleSheet(
            "color:rgba(255,255,255,140); background:transparent; font-size:8pt;"
        )
        self._draw_hint.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._draw_hint.hide()

        btn_s = (
            "color:white; background:rgba(0,0,0,160); border:none;"
            "font-size:20px; padding:6px 12px; border-radius:3px;"
        )
        self._prev_btn = QPushButton("\u23ee", self._hud)
        self._play_btn = QPushButton("\u23f8", self._hud)
        self._next_btn = QPushButton("\u23ed", self._hud)
        for btn in (self._prev_btn, self._play_btn, self._next_btn):
            btn.setStyleSheet(btn_s)
            btn.setFixedSize(50, 40)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._prev_btn.clicked.connect(self._prev_clip)
        self._play_btn.clicked.connect(self._toggle_play)
        self._next_btn.clicked.connect(self._next_clip)

        self.setMouseTracking(True)

    def _setup_timers(self):
        self._hud_timer = QTimer(self)
        self._hud_timer.setSingleShot(True)
        self._hud_timer.setInterval(3000)
        self._hud_timer.timeout.connect(self._hide_hud)

    # ── Qt lifecycle ──────────────────────────────────────────────────────

    def showFullScreen(self):
        super().showFullScreen()
        QTimer.singleShot(0, lambda: self._play_clip(0))
        self._show_hud()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._video_widget.resize(self.size())
        self._drawing.resize(self.size())
        self._hud.resize(self.size())
        self._reposition_hud()

    # ── Layout ────────────────────────────────────────────────────────────

    def _reposition_hud(self):
        w, h = self.width(), self.height()

        self._name_label.adjustSize()
        self._name_label.move(12, 12)

        self._clip_label.adjustSize()
        self._clip_label.move(12, h - 72)

        notes_visible = bool(self._notes_label.text()) and not self._notes_pinned
        self._notes_label.setVisible(notes_visible)
        self._notes_label.adjustSize()
        self._notes_label.move(12, h - 50)

        self._counter_label.adjustSize()
        self._counter_label.move(w - self._counter_label.width() - 12, h - 72)

        cx = (w - 160) // 2
        self._prev_btn.move(cx, h - 52)
        self._play_btn.move(cx + 55, h - 52)
        self._next_btn.move(cx + 110, h - 52)

        sx = (w - (80 + 64 + 72 + 72 + 36)) // 2
        sy = 10
        self._color_btn.move(sx, sy)
        self._thin_btn.move(sx + 88, sy)
        self._thick_btn.move(sx + 160, sy)
        self._clear_btn.move(sx + 240, sy)
        self._draw_hint.adjustSize()
        self._draw_hint.move((w - self._draw_hint.width()) // 2, sy + 36)

        self._pinned_notes.setMaximumWidth(min(700, w - 24))
        self._pinned_notes.adjustSize()
        self._pinned_notes.move(12, h - 100 - self._pinned_notes.height())

    # ── Playback ──────────────────────────────────────────────────────────

    def _play_clip(self, index: int):
        if not self._clips or index < 0 or index >= len(self._clips):
            return
        self._current_index = index
        clip = self._clips[index]
        self._player.setSource(QUrl.fromLocalFile(self._video_path))
        self._player.play()
        QTimer.singleShot(300, lambda: self._seek_to(clip.start))
        self._play_btn.setText("\u23f8")
        self._update_hud_labels()
        QTimer.singleShot(400, self.setFocus)

    def _seek_to(self, t: float):
        self._player.setPosition(int(t * 1000))

    def _on_position_changed(self, ms: int):
        if not self._clips:
            return
        clip = self._clips[self._current_index]
        if ms / 1000.0 >= clip.end:
            self._player.pause()
            if self._current_index + 1 < len(self._clips):
                QTimer.singleShot(800, lambda: self._play_clip(self._current_index + 1))
            else:
                self._play_btn.setText("\u25b6")

    def _update_hud_labels(self):
        if not self._clips:
            return
        clip = self._clips[self._current_index]
        cat_name = self._category_map.get(clip.category_id, "")
        label_text = f"{cat_name} — {clip.label}" if cat_name else clip.label
        self._clip_label.setText(label_text)
        notes_text = clip.notes.strip() if clip.notes else ""
        self._notes_label.setText(notes_text)
        self._pinned_notes.setText(notes_text)
        self._pinned_notes.setVisible(self._notes_pinned and bool(notes_text))
        self._counter_label.setText(f"{self._current_index + 1} / {len(self._clips)}")
        self._reposition_hud()

    def _toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._play_btn.setText("\u25b6")
        else:
            self._player.play()
            self._play_btn.setText("\u23f8")
        self.setFocus()

    def _prev_clip(self):
        self._play_clip(max(0, self._current_index - 1))

    def _next_clip(self):
        self._play_clip(min(len(self._clips) - 1, self._current_index + 1))

    def _step(self, seconds: float):
        if not self._clips:
            return
        clip = self._clips[self._current_index]
        current = self._player.position() / 1000.0
        target = max(clip.start, min(clip.end - 0.1, current + seconds))
        self._seek_to(target)

    def _frame_step(self, direction: int):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._play_btn.setText("\u25b6")
        if direction > 0:
            pos = self._player.position()
            self._player.setPosition(pos + 40)  # ~1 frame at 25fps
        else:
            self._step(-0.04)

    def _set_rate(self, delta: float):
        rate = max(0.25, min(4.0, self._player.playbackRate() + delta))
        self._player.setPlaybackRate(rate)

    # ── HUD ───────────────────────────────────────────────────────────────

    def _hide_hud(self):
        self._hud.setVisible(False)

    def _show_hud(self):
        self._hud.setVisible(True)
        if not self._drawing_mode:
            self._hud_timer.start()

    # ── Drawing ───────────────────────────────────────────────────────────

    def _toggle_drawing(self):
        self._drawing_mode = not self._drawing_mode
        self._drawing.setVisible(self._drawing_mode)
        for w in (self._color_btn, self._thin_btn, self._thick_btn,
                  self._clear_btn, self._draw_hint):
            w.setVisible(self._drawing_mode)
        if self._drawing_mode:
            self._hud_timer.stop()
            self._drawing.raise_()
            self._hud.raise_()
            self._pinned_notes.raise_()
            self._draw_hint.setText(
                "Draw with mouse  ·  [K] cycle color  ·  [C] clear  ·  [D] exit draw mode"
            )
            self._show_hud()
        else:
            self._hud_timer.start()
        self._reposition_hud()
        self.setFocus()

    def _cycle_color(self):
        color = self._drawing.cycle_color()
        self._color_btn.setStyleSheet(
            f"color:{color.name()}; background:rgba(0,0,0,160); border:none;"
            "font-size:13px; padding:4px 10px; border-radius:3px;"
            "border:1px solid rgba(255,255,255,60);"
        )
        self.setFocus()

    # ── Notes pin ─────────────────────────────────────────────────────────

    def _toggle_notes_pin(self):
        self._notes_pinned = not self._notes_pinned
        notes_text = self._notes_label.text()
        self._pinned_notes.setVisible(self._notes_pinned and bool(notes_text))
        if self._notes_pinned:
            self._pinned_notes.raise_()
        self._reposition_hud()
        self._show_hud()

    # ── Mouse / keyboard ──────────────────────────────────────────────────

    def mousePressEvent(self, event):
        self.setFocus()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self._show_hud()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

        if key in (Qt.Key.Key_Escape, Qt.Key.Key_F11):
            self._hud_timer.stop()
            self._player.stop()
            self.closed.emit()
            self.close()

        elif key == Qt.Key.Key_Space:
            self._toggle_play()

        elif key == Qt.Key.Key_Tab:
            if shift:
                self._prev_clip()
            else:
                self._next_clip()

        elif key == Qt.Key.Key_Left and not self._drawing_mode:
            self._step(-5)

        elif key == Qt.Key.Key_Right and not self._drawing_mode:
            self._step(5)

        elif key in (Qt.Key.Key_Comma, Qt.Key.Key_Less):
            self._frame_step(-1)

        elif key in (Qt.Key.Key_Period, Qt.Key.Key_Greater):
            self._frame_step(1)

        elif key == Qt.Key.Key_BracketLeft:
            self._set_rate(-0.25)

        elif key == Qt.Key.Key_BracketRight:
            self._set_rate(0.25)

        elif key == Qt.Key.Key_D:
            self._toggle_drawing()

        elif key == Qt.Key.Key_C and self._drawing_mode:
            self._drawing.clear()

        elif key == Qt.Key.Key_K and self._drawing_mode:
            self._cycle_color()

        elif key == Qt.Key.Key_N:
            self._toggle_notes_pin()

        else:
            super().keyPressEvent(event)
```

- [ ] **Step 3: Run smoke test**

```
pytest tests/test_ui.py::test_presentation_window_creates -v
```
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add videotagger/ui/presentation_window.py tests/test_ui.py
git commit -m "feat: replace VLC with QMediaPlayer in PresentationWindow; Tab/Shift+Tab navigation"
```

---

## Task 8: MainWindow — Package Project + Updated Load

**Files:**
- Modify: `videotagger/ui/main_window.py`

- [ ] **Step 1: Update `_load_project` to use the new model fields**

In `videotagger/ui/main_window.py`, replace the `_load_project` method:

```python
def _load_project(self, project: Project, path):
    import os
    # Check the merged (playback) file exists
    if not os.path.exists(project.merged_video_path):
        from PyQt6.QtWidgets import QMessageBox, QFileDialog
        msg = (
            f"Merged video not found:\n{project.merged_video_path}\n\n"
            "Would you like to locate the merged file, or re-merge from sources?"
        )
        reply = QMessageBox.warning(
            self, "Video Not Found", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Locate merged file manually
            new_path, _ = QFileDialog.getOpenFileName(
                self, "Locate Merged Video", "",
                "Video Files (*.mp4 *.mov *.avi *.mkv *.m4v);;All Files (*)",
            )
            if not new_path:
                return
            project.merged_video_path = new_path
        elif reply == QMessageBox.StandardButton.No:
            # Re-merge from sources
            from videotagger.core.video_merger import VideoMerger
            from videotagger.ui.dialogs.merge_progress_dialog import MergeProgressDialog
            from videotagger.export.ffmpeg_exporter import _ffmpeg_path
            merger = VideoMerger(_ffmpeg_path())
            dlg = MergeProgressDialog(
                merger, project.source_video_paths,
                project.merged_video_path, self,
            )
            if not dlg.exec() or not dlg.was_successful():
                return
        else:
            return

    from videotagger.core.tagging_engine import TaggingEngine
    self._project = project
    self._project_path = path
    self._tagging_engine = TaggingEngine()
    self._save_act.setEnabled(True)
    self._import_act.setEnabled(True)
    self._package_act.setEnabled(True)
    self.setWindowTitle("VideoTagger")
    import os
    self._file_label.setText(os.path.basename(project.merged_video_path))
    self.player.load(project.merged_video_path)
    self.timeline.set_project(project)
    self.tag_panel.refresh(project)
    self.clips_panel.refresh(project)
    self._wire_signals()
```

- [ ] **Step 2: Add `_package_act` and `_package_project` to the menu and method**

In `_setup_menu`, add after `self._import_act`:

```python
self._package_act = QAction("&Package Project…", self)
self._package_act.triggered.connect(self._package_project)
self._package_act.setEnabled(False)
file_menu.addAction(self._package_act)
```

Add the new method to `MainWindow`:

```python
def _package_project(self):
    if not self._project:
        return
    from PyQt6.QtWidgets import QFileDialog, QMessageBox
    import copy, os, shutil
    from videotagger.data.project_manager import ProjectManager

    folder = QFileDialog.getExistingDirectory(self, "Choose Package Destination")
    if not folder:
        return

    # Name the package folder after the .vtp file (or "VideoTaggerProject")
    if self._project_path:
        import os
        proj_stem = os.path.splitext(os.path.basename(self._project_path))[0]
    else:
        proj_stem = "VideoTaggerProject"

    pkg_dir = os.path.join(folder, proj_stem)
    try:
        os.makedirs(pkg_dir, exist_ok=True)
        # Copy merged video
        shutil.copy2(self._project.merged_video_path, os.path.join(pkg_dir, "video.mp4"))
        # Save .vtp with relative path
        pkg_project = copy.copy(self._project)
        pkg_project.merged_video_path = "./video.mp4"
        pkg_project.source_video_paths = ["./video.mp4"]
        ProjectManager.save(pkg_project, os.path.join(pkg_dir, "project.vtp"))
    except Exception as exc:
        QMessageBox.critical(self, "Package Failed", str(exc))
        return

    QMessageBox.information(
        self, "Packaged",
        f"Project packaged successfully:\n{pkg_dir}",
    )
```

- [ ] **Step 3: Add `_package_act` initialisation in `__init__` before `_setup_menu` is called**

In `__init__`, before `self._setup_menu()`, add:

```python
self._package_act = None  # initialised in _setup_menu
```

Actually, `_setup_menu` creates it — no change to `__init__` needed. But `_load_project` references `self._package_act` — ensure `_setup_menu` is always called before `_load_project`. This is already the case (both called from `__init__`). No change needed.

- [ ] **Step 4: Update `_on_present_requested` to pass `merged_video_path`**

In `_on_present_requested`, the line:
```python
self._presentation = PresentationWindow(
    self._project.video_path, clips, pl.name, category_map, self
)
```
is now:
```python
self._presentation = PresentationWindow(
    self._project.merged_video_path, clips, pl.name, category_map, self
)
```

- [ ] **Step 5: Run main window smoke test**

```
pytest tests/test_ui.py::test_main_window_opens -v
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add videotagger/ui/main_window.py
git commit -m "feat: MainWindow Package Project menu + updated _load_project for v2 model"
```

---

## Task 9: Requirements and Build Spec Cleanup

**Files:**
- Modify: `requirements.txt`
- Modify: `VideoTagger.spec`

- [ ] **Step 1: Update requirements.txt**

Replace `requirements.txt`:

```
PyQt6>=6.6.0
ffmpeg-python>=0.2.0
pytest>=7.4.0
pytest-qt>=4.2.0
pyinstaller>=6.0.0
```

(`python-vlc` removed.)

- [ ] **Step 2: Rewrite VideoTagger.spec**

Replace `VideoTagger.spec`:

```python
# VideoTagger.spec  — cross-platform (Windows + macOS)
import sys
from pathlib import Path

if sys.platform == 'win32':
    ffmpeg_datas = [('ffmpeg.exe', '.')] if Path('ffmpeg.exe').exists() else []
elif sys.platform == 'darwin':
    ffmpeg_datas = [('ffmpeg', '.')] if Path('ffmpeg').exists() else []
else:
    ffmpeg_datas = []

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('videotagger/resources', 'videotagger/resources'),
    ] + ffmpeg_datas,
    hiddenimports=[
        'pkgutil',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
    ],
    hookspath=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

if sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='VideoTagger',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=None,
    )

elif sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='VideoTagger',
        debug=False,
        strip=False,
        upx=False,
        console=False,
        icon='videotagger/resources/logo.png',
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name='VideoTagger',
    )
    app = BUNDLE(
        coll,
        name='VideoTagger.app',
        icon='videotagger/resources/logo.png',
        bundle_identifier='com.cheapstats.videotagger',
        info_plist={
            'CFBundleName': 'VideoTagger',
            'CFBundleDisplayName': 'VideoTagger',
            'CFBundleVersion': '2.0.0',
            'CFBundleShortVersionString': '2.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        },
    )
```

- [ ] **Step 3: Run full test suite**

```
pytest tests/ -v
```
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt VideoTagger.spec
git commit -m "chore: remove VLC dependency; add QtMultimedia hiddenimports to build spec"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] §1 Standalone .vtp: v1→v2 migration in Tasks 1+2
- [x] §1 Packaged project: `_package_project` in Task 8
- [x] §1 Relative path resolution for packaged .vtp: Task 2
- [x] §2 Multi-file picker: Task 5
- [x] §2 FFmpeg copy→H.264 fallback: Task 3
- [x] §2 Progress dialog: Task 4
- [x] §2 Single file no-copy: `len(sources)==1` branch in Tasks 3+5
- [x] §2 Re-merge on open if merged file missing: Task 8 `_load_project`
- [x] §3 PlayerWidget VLC→QtMultimedia: Task 6
- [x] §3 PresentationWindow VLC→QtMultimedia: Task 7
- [x] §3 Drawing overlay works (now naturally via Qt widget stack): Task 7
- [x] §4 Tab/Shift+Tab navigation: Task 7
- [x] §4 Auto-advance on clip end: `_on_position_changed` in Task 7
- [x] Requirements + build spec: Task 9
- [x] `ffmpeg_exporter` video_path → merged_video_path: Task 1 Step 5

**No placeholders found.**

**Type consistency:** `VideoMerger.merge()` signature used consistently in Tasks 3, 4, 5, 8. `Project.merged_video_path` / `source_video_paths` used consistently in Tasks 1–8.
