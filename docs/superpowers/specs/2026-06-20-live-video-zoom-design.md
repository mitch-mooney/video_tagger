# Live Video Zoom — Design

**Date:** 2026-06-20
**Status:** Approved (Section A only; zoomed export deferred)

## Goal

Let the user zoom into and pan around a region of the video while it plays —
both while reviewing/coding a game in the main player, and while highlighting
an area for an audience in Presentation Mode. The motivating case: a 4K source
where the user wants to look closely at one part of the frame (e.g. a ~720p
square) without the whole frame being scaled to fit.

This is a **live viewing aid**. It does not alter clips, projects, or exported
files. Zoom state is transient and not saved.

## Out of scope (deferred)

- **Zoomed export** (baking a crop region into exported `.mp4` files). Tracked
  separately for a later round.
- Keyframed / action-tracking pan.
- Saving zoom regions per clip.

## Approach

The current video surface is `QVideoWidget`, a native window that always shows
the whole frame scaled-to-fit and cannot zoom into a region. Replace it with
`QGraphicsView` + `QGraphicsScene` + `QGraphicsVideoItem`, where:

- **Zoom** = a scale transform on the view.
- **Pan** = a translation (scrolling the view over the larger scaled item).

`QMediaPlayer.setVideoOutput()` accepts a `QGraphicsVideoItem` the same way it
accepts a `QVideoWidget`, so the existing playback wiring is unchanged.

Rejected alternatives:
- Scaling/translating the native `QVideoWidget` itself — unreliable for native
  windows (the codebase already forces `winId()` HWND creation).
- Manually painting frames from a `QVideoSink` to a `QGraphicsScene` —
  reimplements playback rendering for no benefit and risks performance on 4K.

## Components

### `ZoomableVideoView` (new shared widget)

A small reusable widget that owns the zoom/pan rendering and logic. One place to
maintain so behavior stays identical in both consumers.

**Responsibilities**
- Hold a `QGraphicsView`, `QGraphicsScene`, and `QGraphicsVideoItem`.
- Expose the video item so the owner can call
  `player.setVideoOutput(view.video_item)`.
- Keep the video item sized to the source video's native frame size (via
  `QGraphicsVideoItem.nativeSize`, available once the media loads) so zoom math
  is in real pixel terms.
- Implement zoom and pan with clamping.

**Public interface (what it does / how you use it / what it depends on)**
- `video_item` — the `QGraphicsVideoItem` to pass to the player. *(what it does:
  the render target.)*
- `zoom_in(step)` / `zoom_out(step)` — change zoom by a factor step.
- `set_zoom(factor)` — set absolute zoom.
- `reset_zoom()` — return to fit-to-view (factor that makes the whole frame
  visible).
- `is_zoomed` — whether currently above fit.
- Depends only on PyQt6 (`QtWidgets`, `QtMultimediaWidgets`, `QtCore`,
  `QtGui`). No project model dependencies — it is purely a view component.

**Behavior**
- **Fit baseline:** the minimum zoom is "fit" — the whole frame visible,
  letterboxed in the view. You cannot zoom below fit.
- **Zoom centered on cursor** for wheel zoom; centered on view center for
  `+`/`-` keys.
- **Pan clamping:** when zoomed, panning is clamped so the view never shows
  past the frame edges (no black margins from over-panning).
- **Drag to pan:** left-button press-drag translates the view when zoomed; when
  at fit, drag is a no-op (nothing to pan).

**Controls**

| Input              | Action                              |
|--------------------|-------------------------------------|
| Mouse scroll wheel | Zoom in / out, centered on cursor   |
| `+` / `-`          | Zoom in / out a step                |
| Click + drag       | Pan the zoomed view                 |
| `0`                | Reset to fit (full frame)           |

These do not collide with any existing shortcuts in either consumer (see below).

### `PlayerWidget` (modified)

[videotagger/ui/player_widget.py](../../../videotagger/ui/player_widget.py)

- Replace the `QVideoWidget` in `_setup_ui` with a `ZoomableVideoView`; wire
  `self._player.setVideoOutput(self._zoom_view.video_item)`.
- The control bar (play / position / seek / duration / speed) is unchanged and
  still sits below the video area.
- **Zoom persists** across play and scrubbing. It changes only when the user
  adjusts it or presses `0`. Nothing auto-resets it.
- Wheel and drag are handled inside `ZoomableVideoView`. The `+` / `-` / `0`
  keys are routed from the existing key handling so they work while the player
  has focus.

**Existing main-window shortcuts that must stay intact:** `Space`, `I`, `O`,
`Esc`, `Ctrl+Z`, `Left`/`Right` (±5 s), `Shift+Left`/`Shift+Right` (±1 frame),
`[` / `]` (speed), `Ctrl+N/O/S`. None use `+`, `-`, `0`, the wheel, or drag.

### `PresentationWindow` (modified)

[videotagger/ui/presentation_window.py](../../../videotagger/ui/presentation_window.py)

- Replace the full-screen `QVideoWidget` with a `ZoomableVideoView` sized to the
  window in `resizeEvent`; wire the player's video output to its video item.
- HUD overlays (`_hud`, `_pinned_notes`, labels, buttons) are absolutely
  positioned children of the window, **not** of the video widget, so they
  continue to render on top of the zoomed video with no change.
- **Zoom auto-resets to fit when advancing to a new clip** (`_play_clip`), so
  every clip starts full-frame. The user re-zooms per clip as needed.

**Existing presentation shortcuts that must stay intact:** `Esc`/`F11`,
`Space`, `Tab`/`Shift+Tab`, `Left`/`Right` (±5 s), `,` / `.` (frame step),
`[` / `]` (speed), `N` (pin notes). None use `+`, `-`, `0`, the wheel, or drag.

## Data flow

```
QMediaPlayer ──setVideoOutput──> ZoomableVideoView.video_item (QGraphicsVideoItem)
                                          │
                          QGraphicsScene ─┘ (item sized to native frame)
                                          │
                          QGraphicsView ──┘ (scale = zoom, scroll = pan, clamped)
```

No data flows into the project model. Zoom state lives only in the view.

## Error handling / edge cases

- **Native size not yet known:** `QGraphicsVideoItem.nativeSize` is invalid
  until the media is loaded and the first frame is decoded. Handle the
  `nativeSizeChanged` signal to (re)apply the fit transform once the real frame
  size arrives; before then, treat the item size as the view size.
- **Window/view resize:** recompute the fit baseline on resize so "fit" always
  means the current viewport; preserve the user's current zoom factor and
  re-clamp the pan offset to the new bounds.
- **Zoom clamping:** minimum = fit; define a sensible maximum (e.g. 8×) to avoid
  extreme pixelation and runaway state.
- **Pan clamping:** never expose area outside the frame.
- **Aspect ratio:** keep the frame's aspect ratio (letterbox at fit); zoom
  scales uniformly so no distortion.

## Testing

- **Unit-testable logic** (extract pure functions so they need no live video):
  - Fit-scale computation given frame size and viewport size.
  - Zoom clamping (min = fit, max cap).
  - Pan-offset clamping given zoom factor, frame size, viewport size.
- **Manual verification:**
  - Main player: zoom while playing and while scrubbing; confirm zoom persists;
    confirm `0` resets; confirm drag pans and clamps at edges.
  - Presentation: zoom on a clip, advance to next clip, confirm reset to fit;
    confirm HUD/notes still render on top while zoomed.
  - Confirm no regression in existing shortcuts in both windows.
```
