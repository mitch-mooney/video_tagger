# Dual Video Angle + Per-Period Sync — Implementation Plan

**Goal:** Load two camera angles of one match, align them at each period start, and switch
between them seamlessly during playback (dual decode). Main tagging window only.

**Architecture:** The existing `merged_video_path` is the canonical (primary) timeline;
clips are unchanged. A secondary `VideoAngle` maps onto it piecewise per `Period` via pure
`map_to_angle` math. `PlayerWidget` drives two `QMediaPlayer`s in a `QStackedWidget` so
switching is instant; a drift-lock keeps the hidden angle aligned. Sync points are captured
visually in a new `AngleSyncDialog`.

**Tech Stack:** Python, PyQt6 (`QtWidgets`, `QtMultimedia`, `QtMultimediaWidgets`), pytest.

**Reference spec:** `docs/superpowers/specs/2026-06-21-dual-angle-sync-design.md`

---

## Tasks

- [x] **Data model** ([project.py](../../../videotagger/models/project.py)) — add `Period`
  and `VideoAngle`; add `Project.periods` / `Project.angles`; bump `version` to 3; serialize
  + migrate (v1/v2 → empty lists).
- [x] **Path resolution** ([project_manager.py](../../../videotagger/data/project_manager.py))
  — resolve each angle's `merged_video_path` / `source_video_paths` relative to the `.vtp`.
- [x] **Sync math** (`videotagger/core/angle_sync.py`) — pure `active_period`,
  `map_to_angle`; identity fallbacks; non-negative.
- [x] **Dual-decode player** ([player_widget.py](../../../videotagger/ui/player_widget.py))
  — `QStackedWidget` of views; `set_secondary_angle`/`clear_secondary_angle`/`switch_angle`;
  controls propagate to both players; 80 ms drift-lock; angle toggle button.
- [x] **Sync dialog** (`videotagger/ui/dialogs/angle_sync_dialog.py`) — file pick + merge,
  two scrubbable previews, period table with "Set @ Playhead", writes periods + angle.
- [x] **Main window** ([main_window.py](../../../videotagger/ui/main_window.py)) —
  `_apply_secondary_angle`, `_manage_angles`, **Video** menu, **`V`** shortcut.
- [x] **Shortcut hint** ([shortcut_bar.py](../../../videotagger/ui/shortcut_bar.py)) —
  conditional `V Angle` hint when a second angle is loaded.
- [x] **Tests** — `tests/test_angle_sync.py` (new); extend `tests/test_models.py` and
  `tests/test_project_manager.py` (incl. v3 version bump assertions).

## Verification

1. `pytest` — all logic tests pass (`test_angle_sync`, `test_models`, `test_project_manager`).
   Widget tests follow the existing `tests/test_ui.py` pytest-qt style.
2. Manual end-to-end: open an existing project (unchanged) → Video ▸ Manage Angles → add a
   second angle, mark Q1–Q4 in both previews → play, press `V` mid-play (same moment,
   instant) → cross a quarter boundary, switch again (still aligned) → save/reopen (persists).
