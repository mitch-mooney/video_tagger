# Dual Video Angle + Per-Period Sync — Design

**Date:** 2026-06-21
**Status:** Approved (main window only; Presentation Mode + export deferred)

## Goal

Let an analyst load **two camera angles** of the same match (e.g. *behind goals* and
*broadcast vision*), align them at the **start of each period/quarter**, and **switch
between angles seamlessly during playback**. The two recordings are usually not aligned:
one may be a single continuous recording (with breaks between quarters), the other started
and stopped each quarter. The Hudl approach is mirrored: capture each period's start
timestamp in each video and use those offsets to keep the angles in sync.

## Out of scope (deferred)

- **Presentation Mode** dual angle (single-angle for now).
- **Export** angle selection / side-by-side output.
- **3+ angle UI** — the data model already supports N angles; the UI handles one secondary.

## Approach

The **primary angle** is the existing `Project.merged_video_path`. Its video time *is* the
canonical match timeline; clips remain stored against it (no migration). A **secondary
angle** is a separate working video mapped onto the canonical timeline **piecewise per
period**:

For canonical time `t` inside period `P` (`P.primary_start <= t < nextPeriod.primary_start`):

```
secondary_time = angle.period_starts[P.id] + (t - P.primary_start)
```

Re-syncing at every period boundary absorbs drift between a continuous recording and a
per-quarter one. Within a period both run at real time, so they stay aligned; a small
runtime drift-lock corrects sub-second slippage.

**Seamless switching = dual decode.** Both angles play in lockstep on two `QMediaPlayer`s,
each rendering to its own `ZoomableVideoView`; only the active one is shown (a
`QStackedWidget`). Switching just changes the visible view — instant, no reload. The
rejected alternative (one player, `setSource` + seek on switch) reuses the existing
Presentation-Mode pattern but has a visible ~0.3–0.8 s reload hiccup per switch.

## Components

### Data model — [project.py](../../../videotagger/models/project.py)

- `Period(name, primary_start, id)` — a period anchored on the canonical timeline.
- `VideoAngle(name, source_video_paths, merged_video_path, period_starts, id)` —
  `period_starts` maps `period.id -> video-time (s)` in this angle's footage.
- `Project` gains `periods: List[Period]` and `angles: List[VideoAngle]`; `version` → **3**.
- Serialization round-trips both; v1/v2 files migrate to v3 with empty `periods`/`angles`,
  so existing projects behave exactly as before.

### Sync math — [angle_sync.py](../../../videotagger/core/angle_sync.py) (new, pure)

No Qt — testable like `zoom_geometry`. `active_period(periods, t)` and
`map_to_angle(periods, angle, t)`. Identity fallback when there are no periods or the
active period has no sync point; never returns a negative time.

### `PlayerWidget` (modified) — [player_widget.py](../../../videotagger/ui/player_widget.py)

- Video surface becomes a `QStackedWidget` of per-angle `ZoomableVideoView`s.
- Primary `QMediaPlayer` still drives `position_changed`/`duration_changed`/slider/labels.
- `set_secondary_angle(path, mapper, names...)`, `clear_secondary_angle()`,
  `switch_angle()`, `angle_changed(int)` signal, and a control-bar angle toggle button.
- `toggle_play`/`set_rate` apply to both players; `seek(t)` seeks primary to `t` and
  secondary to `mapper(t)`; `zoom_*` act on the visible view.
- **Drift lock:** while playing, each primary tick re-seeks the secondary if it drifts more
  than ~80 ms (≈2 frames) from `mapper(pos)`.

### `AngleSyncDialog` (new) — [angle_sync_dialog.py](../../../videotagger/ui/dialogs/angle_sync_dialog.py)

Opened from **Video ▸ Manage Angles…**. Picks/merges the secondary angle (reusing
`VideoMerger` + `MergeProgressDialog`), shows two scrubbable previews side by side
(`QVideoWidget` + slider + frame-step), and a period table (`name | primary start |
second-angle start`, defaults Q1–Q4, add/remove/rename). "Set @ Playhead" captures the
preview's current position. On OK it writes `project.periods` and the `VideoAngle`.

### `MainWindow` (modified) — [main_window.py](../../../videotagger/ui/main_window.py)

`_apply_secondary_angle()` builds the mapper from `periods` + `angles[0]` and calls
`player.set_secondary_angle(...)` (or `clear_secondary_angle()`), and toggles the shortcut
hint. Called after `_load_project` and after the dialog is accepted. Adds the **Video** menu
and the **`V`** shortcut → `player.switch_angle()` (avoids `Tab`, used by Qt focus traversal).

## Data flow

```
periods + angles[0].period_starts
        │  map_to_angle(t)
canonical t ───────────────▶ secondary video-time
   │ (primary player)            │ (secondary player)
   ▼                             ▼
view[0] (shown) ◀── switch_angle ──▶ view[1]   (QStackedWidget; both decode)
```

Clips/tags flow unchanged — they live on the canonical (primary) timeline.

## Error handling / edge cases

- **No second angle / old project:** `angles == []` → single-angle behaviour, toggle hidden.
- **Time before first period:** clamps to the first period's offset; never negative.
- **Missing sync point for the active period:** identity map (no shift) for that span.
- **Secondary still buffering:** drift-lock converges it to the mapped position.
- **Sub-frame alignment:** WMF seeks snap toward keyframes; per-period re-sync + drift-lock
  keep it visually tight but exact frame parity isn't guaranteed.
- **Performance:** two simultaneous decodes ~double cost; acceptable for two streams.
  Documented fallback if poor: pause the hidden player and seek-on-switch (not implemented).

## Testing

- **Unit (pure):** `tests/test_angle_sync.py` — within/at-boundary/before-first periods,
  continuous-vs-per-quarter offsets, empty periods (identity), missing key (identity),
  non-negative.
- **Model/manager:** round-trip `periods`/`angles`; v2→v3 migration; relative-path
  resolution for an angle's `merged_video_path`/`source_video_paths`.
- **Manual:** open an existing single-video project (unchanged); add a second angle; mark
  Q1–Q4 in both previews; play and press `V` mid-play (same moment, instant); cross a
  quarter boundary and switch again (still aligned); save/reopen (persists).
