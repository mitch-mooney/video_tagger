# Design: Multi-file Projects, QtMultimedia, and Presentation Mode UX

**Date:** 2026-04-16  
**Status:** Approved

---

## Overview

Three interconnected improvements to VideoTagger:

1. **Multi-file project support** — a single match split across multiple camera files is treated as one continuous video timeline, merged via FFmpeg at project creation
2. **VLC → QtMultimedia** — replace VLC with PyQt6's built-in media stack to fix broken drawing overlays and keyboard event handling in presentation mode
3. **Presentation UX** — Tab/Shift+Tab navigation, working drawing overlay

---

## Section 1 — Project Modes (Standalone vs Package)

### Motivation

Users share `.vtp` files when everyone on a team already has the same 5GB match file. A separate "Package" option bundles the project + video into a portable folder for archiving or sending to someone without the source footage.

### Mode 1: Standalone `.vtp` (default, unchanged workflow)

The `.vtp` JSON file stores:

```json
{
  "version": 2,
  "source_video_paths": ["C:/Matches/Q1.mp4", "C:/Matches/Q2.mp4"],
  "merged_video_path": "C:/Matches/game_merged.mp4",
  "categories": [...],
  "clips": [...],
  "playlists": [...]
}
```

- `source_video_paths` replaces `video_path` (list; single-file projects have one entry)
- `merged_video_path` is where the merged file was written at project creation
- On open: if `merged_video_path` does not exist, the app prompts the user to either:
  - Re-merge from their local copies of the source files (paths editable in the dialog)
  - Locate the merged file manually (existing "Video Not Found" flow)
- Single-file, pre-existing projects: `video_path` is read as a single-entry `source_video_paths`; `merged_video_path` equals `source_video_paths[0]` (no merge needed)

**Backward compatibility rule:** if `video_path` key is present (version 1), load it as a single-source project. Write version 2 format on first save.

### Mode 2: Package (opt-in)

- **File → Package Project...** opens a folder picker
- Creates `<chosen_folder>/` containing:
  ```
  MyGame/
    project.vtp        ← merged_video_path set to "./video.mp4"
    video.mp4          ← copy of the merged file
  ```
- The packaged `.vtp` uses a relative path `./video.mp4` so the folder is self-contained wherever it lives
- Source paths are preserved in `source_video_paths` for reference but are not required for playback

---

## Section 2 — Multi-file Merge (FFmpeg)

### New Project Dialog Changes

- Replace single file picker with a multi-file list:
  - "Add files" button (multi-select supported)
  - Orderable list (drag to reorder, e.g. Q1 before Q2)
  - Remove button per row
- "Merged video location" field: defaults to same directory as first source file, user can change
- Merged filename defaults to `<first_file_stem>_merged.mp4`

### Merge Process

Runs after the user confirms the dialog, before the project opens.

**Step 1 — attempt copy-concat (fast, lossless):**

```
ffmpeg -f concat -safe 0 -i filelist.txt -c copy video.mp4
```

- `filelist.txt` is a temp file listing source paths in order
- Fast even for 2×2GB files (pure container operation, no re-encode)
- Requires all files to share the same codec, resolution, and framerate — guaranteed for camera splits from the same device

**Step 2 — fallback re-encode (if Step 1 fails):**

```
ffmpeg -f concat -safe 0 -i filelist.txt -c:v libx264 -crf 18 -c:a aac video.mp4
```

- `-crf 18` = near-lossless quality
- Slower but handles codec mismatches

**Single-file projects:** No merge. `merged_video_path = source_video_paths[0]`. The file is referenced in-place; it is NOT copied into any container unless the user explicitly packages the project.

**Progress UI:** Modal progress dialog (non-blocking Qt thread) with:
- File name and step ("Merging — pass 1: copy")
- Cancel button (kills the FFmpeg subprocess cleanly)
- On cancel: partial output file is deleted

### Re-merge on Open

If `merged_video_path` is missing at open time, a dialog shows:
- List of `source_video_paths` with editable path fields (so user can remap to their local copies)
- "Re-merge" button → runs the same merge process
- "Locate merged file" button → manual file picker

---

## Section 3 — VLC → QtMultimedia

### Motivation

VLC's `set_hwnd` embedding bypasses Qt's rendering pipeline entirely. At the OS compositor level, VLC's video surface is painted independently of the Qt widget tree, meaning:

- `DrawingOverlay` (a Qt widget) is composited *beneath* VLC's video — invisible
- VLC intercepts native keyboard/mouse messages before Qt sees them — shortcuts unreliable

`QMediaPlayer` + `QVideoWidget` renders through Qt, so overlays are simply Qt widgets in the normal stacking order and all input events are handled by Qt.

### Changes

**`PlayerWidget` (main window):**
- Replace `vlc.Instance` / `vlc.MediaPlayer` with `QMediaPlayer` + `QVideoWidget`
- `QVideoWidget` embedded where VLC surface was
- Public API preserved: `load(path)`, `seek(t)`, `get_position()`, `get_rate()`, `set_rate(r)`, `step(s)`, `toggle_play()`
- Signals preserved: `position_changed`, `duration_changed`
- Position polling via `QMediaPlayer.positionChanged` signal (replaces manual timer)

**`PresentationWindow`:**
- Replace VLC player with `QMediaPlayer` + `QVideoWidget`
- `QVideoWidget` as the base video surface
- `DrawingOverlay` and HUD layered on top as Qt children — works correctly
- `_init_vlc`, `_attach_vlc_window` removed
- Clip boundary polling kept via `QTimer` checking `QMediaPlayer.position()`

**Dependencies:**
- Remove `vlc` from `requirements.txt`
- Remove VLC-related args from `VideoTagger.spec`
- Add `PyQt6-Qt6-MultimediaWidgets` if not already present (check `requirements.txt`)

**Codec support note:** `QMediaPlayer` on Windows uses the Windows Media Foundation backend. Handles H.264/H.265/AAC MP4 natively (standard sports camera output). The FFmpeg merge step in Section 2 outputs H.264 for the fallback path, ensuring compatibility.

---

## Section 4 — Presentation Mode UX

### Navigation

| Key | Action |
|-----|--------|
| `Tab` | Next clip |
| `Shift+Tab` | Previous clip |
| `Space` | Pause / play |
| `Left` | Step back 5s |
| `Right` | Step forward 5s |
| `Shift+Left` | (removed — was prev clip, now Tab/Shift+Tab) |
| `Shift+Right` | (removed — was next clip, now Tab/Shift+Tab) |
| `[` / `]` | Speed down / up |
| `,` / `.` | Frame back / forward |
| `D` | Toggle drawing mode |
| `C` | Clear drawing (in draw mode) |
| `K` | Cycle pen color (in draw mode) |
| `N` | Toggle pinned notes |
| `Escape` / `F11` | Exit presentation |

Auto-advance on clip end is preserved (800ms gap between clips).

### Drawing Overlay

`DrawingOverlay` is unchanged in code. With QtMultimedia, it works correctly because:
- `QVideoWidget` is a normal Qt widget
- `DrawingOverlay` is a child of `PresentationWindow` with `raise_()` called after `QVideoWidget` — sits visually above the video
- Mouse events reach `DrawingOverlay` normally; keyboard events go to `PresentationWindow` (which has `StrongFocus`)

### HUD

No structural changes. Prev/next buttons remain for mouse users. The HUD auto-hides after 3s of no mouse movement (unchanged).

---

## Data Model Changes

`Project` dataclass (`models/project.py`):

```python
# Before
video_path: str

# After
source_video_paths: List[str]   # original source files in order
merged_video_path: str          # path to merged/playback file
```

`project_to_dict` / `project_from_dict` updated accordingly. Version bumped to `2`. Version 1 files are read transparently.

---

## Files Affected

| File | Change |
|------|--------|
| `videotagger/models/project.py` | `video_path` → `source_video_paths` + `merged_video_path`; version 2 |
| `videotagger/data/project_manager.py` | v1→v2 migration on load |
| `videotagger/ui/dialogs/new_project_dialog.py` | Multi-file picker + merge location field |
| `videotagger/ui/dialogs/merge_progress_dialog.py` | New — FFmpeg progress dialog |
| `videotagger/core/video_merger.py` | New — FFmpeg concat logic (copy → fallback) |
| `videotagger/ui/player_widget.py` | VLC → QMediaPlayer + QVideoWidget |
| `videotagger/ui/presentation_window.py` | VLC → QMediaPlayer; Tab/Shift+Tab nav |
| `videotagger/ui/main_window.py` | Package Project menu item; `_load_project` updated for new model |
| `requirements.txt` | Remove `vlc`; confirm QtMultimedia present |
| `VideoTagger.spec` | Remove VLC DLL references |

---

## Out of Scope (Future)

- Multiple camera angles (different views of the same match)
- Annotations burned into exported video
- Cloud sync of packages
