# Live Video Zoom Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user zoom into and pan around a region of the playing video, both in the main player (while coding a game) and in Presentation Mode (to highlight an area live).

**Architecture:** Replace the non-zoomable `QVideoWidget` video surface with a reusable `ZoomableVideoView` built on `QGraphicsView` + `QGraphicsVideoItem`. Zoom = a `fitInView` over a computed visible sub-rectangle of the frame; pan = moving that rectangle's center. The geometry math (zoom clamp, visible-rect/pan clamp, cursor-centered recenter) lives in pure functions so it is unit-testable without live video.

**Tech Stack:** Python, PyQt6 (`QtWidgets`, `QtMultimedia`, `QtMultimediaWidgets`), pytest + pytest-qt.

**Reference spec:** `docs/superpowers/specs/2026-06-20-live-video-zoom-design.md`

---

## File Structure

- **Create** `videotagger/ui/zoom_geometry.py` — pure geometry helpers (no Qt UI deps; uses only plain floats/tuples). One responsibility: zoom/pan math.
- **Create** `videotagger/ui/zoomable_video_view.py` — `ZoomableVideoView(QGraphicsView)` widget. One responsibility: render the video item and apply zoom/pan.
- **Modify** `videotagger/ui/player_widget.py` — use `ZoomableVideoView` instead of `QVideoWidget`; expose `zoom_in`/`zoom_out`/`reset_zoom`.
- **Modify** `videotagger/ui/main_window.py` — add `+` / `=` / `-` / `0` shortcuts wired to the player's zoom methods.
- **Modify** `videotagger/ui/presentation_window.py` — use `ZoomableVideoView`; reset zoom on each clip; handle `+` / `=` / `-` / `0` keys.
- **Create** `tests/test_zoom_geometry.py` — unit tests for the pure helpers.
- **Modify** `tests/test_ui.py` — smoke/behavior tests for the new widget and integrations.

**Note on pan clamping:** `visible_rect()` clamps the center so the visible rectangle never leaves the frame. All pan paths (drag, cursor-zoom) funnel through it, so testing `visible_rect` covers pan clamping. This is the one deliberate refinement from the spec's "separate pan-clamp function" wording — same guarantee, single source of truth.

---

## Task 1: Pure geometry helpers

**Files:**
- Create: `videotagger/ui/zoom_geometry.py`
- Test: `tests/test_zoom_geometry.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_zoom_geometry.py
import pytest
from videotagger.ui.zoom_geometry import clamp_zoom, visible_rect, recenter_on_point


def test_clamp_zoom_floors_at_one():
    assert clamp_zoom(0.5) == 1.0
    assert clamp_zoom(1.0) == 1.0


def test_clamp_zoom_caps_at_max():
    assert clamp_zoom(100.0) == 8.0
    assert clamp_zoom(8.0) == 8.0


def test_clamp_zoom_passes_through_in_range():
    assert clamp_zoom(2.5) == 2.5


def test_visible_rect_at_zoom_one_is_full_frame():
    assert visible_rect(0.0, 0.0, 1920.0, 1080.0, 1.0) == (0.0, 0.0, 1920.0, 1080.0)


def test_visible_rect_zoom_two_centered():
    # zoom 2 -> half size (960x540); centered at frame middle -> offset (480,270)
    assert visible_rect(960.0, 540.0, 1920.0, 1080.0, 2.0) == (480.0, 270.0, 960.0, 540.0)


def test_visible_rect_clamps_center_to_left_edge():
    # center way off to the left -> x clamps to 0
    x, y, w, h = visible_rect(0.0, 540.0, 1920.0, 1080.0, 2.0)
    assert (x, w) == (0.0, 960.0)


def test_visible_rect_clamps_center_to_bottom_right_edge():
    x, y, w, h = visible_rect(99999.0, 99999.0, 1920.0, 1080.0, 2.0)
    assert (x, y) == (960.0, 540.0)  # rect pinned to bottom-right


def test_recenter_on_point_keeps_point_under_cursor_center():
    # cursor at viewport center (0.5,0.5): center == the scene point itself
    cx, cy = recenter_on_point(700.0, 400.0, 0.5, 0.5, 1920.0, 1080.0, 2.0)
    assert (cx, cy) == (700.0, 400.0)


def test_recenter_on_point_offsets_for_corner_cursor():
    # cursor at top-left (0,0): center shifts by +half the visible size
    # visible width at zoom 2 = 960 -> +480 ; height 540 -> +270
    cx, cy = recenter_on_point(700.0, 400.0, 0.0, 0.0, 1920.0, 1080.0, 2.0)
    assert (cx, cy) == (700.0 + 480.0, 400.0 + 270.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_zoom_geometry.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'videotagger.ui.zoom_geometry'`

- [ ] **Step 3: Write the implementation**

```python
# videotagger/ui/zoom_geometry.py
"""Pure geometry helpers for zoom/pan. No Qt dependencies — easy to unit test.

Coordinate system: the video frame is `frame_w` x `frame_h` pixels with origin
(0, 0) at top-left. A "zoom factor" of 1.0 means the whole frame is visible
(fit); 2.0 means a half-width/half-height window, etc. "center" is the point in
frame pixels that the visible window is centered on.
"""
from __future__ import annotations

MIN_ZOOM = 1.0
MAX_ZOOM = 8.0


def clamp_zoom(zoom: float, min_zoom: float = MIN_ZOOM, max_zoom: float = MAX_ZOOM) -> float:
    """Clamp a requested zoom factor to [min_zoom, max_zoom]."""
    return max(min_zoom, min(max_zoom, zoom))


def visible_rect(center_x: float, center_y: float,
                 frame_w: float, frame_h: float, zoom: float) -> tuple:
    """Return the visible (x, y, w, h) sub-rectangle of the frame for a given
    center and zoom, with the center clamped so the rectangle stays fully
    inside the frame. This is also the single source of pan clamping."""
    zoom = max(MIN_ZOOM, zoom)
    w = frame_w / zoom
    h = frame_h / zoom
    # Clamp the top-left so the window stays within [0, frame] on both axes.
    x = min(max(center_x - w / 2.0, 0.0), frame_w - w)
    y = min(max(center_y - h / 2.0, 0.0), frame_h - h)
    return (x, y, w, h)


def recenter_on_point(point_x: float, point_y: float,
                      norm_x: float, norm_y: float,
                      frame_w: float, frame_h: float, zoom: float) -> tuple:
    """Compute the new center so that the frame point (point_x, point_y) stays
    at normalized viewport position (norm_x, norm_y) in [0,1] after zooming.
    Used for cursor-centered wheel zoom. Returned center is unclamped — pass it
    through visible_rect to clamp."""
    w = frame_w / zoom
    h = frame_h / zoom
    center_x = point_x + w * (0.5 - norm_x)
    center_y = point_y + h * (0.5 - norm_y)
    return (center_x, center_y)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_zoom_geometry.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
git add videotagger/ui/zoom_geometry.py tests/test_zoom_geometry.py
git commit -m "feat: pure zoom/pan geometry helpers"
```

---

## Task 2: ZoomableVideoView widget

**Files:**
- Create: `videotagger/ui/zoomable_video_view.py`
- Test: `tests/test_ui.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ui.py`:

```python
def test_zoomable_video_view_creates(qtbot):
    from videotagger.ui.zoomable_video_view import ZoomableVideoView
    from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
    v = ZoomableVideoView()
    qtbot.addWidget(v)
    v.show()
    assert v.isVisible()
    assert isinstance(v.video_item, QGraphicsVideoItem)


def test_zoomable_video_view_zoom_state(qtbot):
    from videotagger.ui.zoomable_video_view import ZoomableVideoView
    v = ZoomableVideoView()
    qtbot.addWidget(v)
    # starts at fit
    v.reset_zoom()
    assert v._zoom == 1.0
    assert v.is_zoomed is False
    # zoom in raises the factor
    v.zoom_in()
    assert v._zoom > 1.0
    assert v.is_zoomed is True
    # zoom out cannot go below fit
    v.reset_zoom()
    v.zoom_out()
    assert v._zoom == 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ui.py::test_zoomable_video_view_creates tests/test_ui.py::test_zoomable_video_view_zoom_state -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'videotagger.ui.zoomable_video_view'`

- [ ] **Step 3: Write the implementation**

```python
# videotagger/ui/zoomable_video_view.py
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, QSizeF, Qt
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtWidgets import QFrame, QGraphicsScene, QGraphicsView

from videotagger.ui.zoom_geometry import clamp_zoom, recenter_on_point, visible_rect

_ZOOM_STEP = 1.25


class ZoomableVideoView(QGraphicsView):
    """A video surface that supports zoom (wheel / +/- / API) and pan (drag).

    Pass `view.video_item` to `QMediaPlayer.setVideoOutput()`. Zoom factor 1.0
    means the whole frame is visible (fit); higher means zoomed in.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._video_item = QGraphicsVideoItem()
        self._scene.addItem(self._video_item)

        self._zoom = 1.0
        self._center = QPointF(0.0, 0.0)
        self._pan_last = None

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("background: black; border: none;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._video_item.nativeSizeChanged.connect(self._on_native_size)

    # ── Public API ──────────────────────────────────────────────────────

    @property
    def video_item(self) -> QGraphicsVideoItem:
        return self._video_item

    @property
    def is_zoomed(self) -> bool:
        return self._zoom > 1.0 + 1e-6

    def zoom_in(self, factor: float = _ZOOM_STEP) -> None:
        self._set_zoom(self._zoom * factor)

    def zoom_out(self, factor: float = _ZOOM_STEP) -> None:
        self._set_zoom(self._zoom / factor)

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        self._center = self._frame_center()
        self._update_view()

    # ── Internal ────────────────────────────────────────────────────────

    def _frame_size(self) -> QSizeF:
        return self._video_item.size()

    def _frame_center(self) -> QPointF:
        s = self._frame_size()
        return QPointF(s.width() / 2.0, s.height() / 2.0)

    def _set_zoom(self, zoom: float) -> None:
        self._zoom = clamp_zoom(zoom)
        self._update_view()

    def _on_native_size(self, size: QSizeF) -> None:
        if size.isEmpty():
            return
        self._video_item.setSize(size)
        self._scene.setSceneRect(self._video_item.boundingRect())
        self._center = self._frame_center()
        self._update_view()

    def _update_view(self) -> None:
        s = self._frame_size()
        if s.width() <= 0 or s.height() <= 0:
            return
        x, y, w, h = visible_rect(
            self._center.x(), self._center.y(), s.width(), s.height(), self._zoom
        )
        self._center = QPointF(x + w / 2.0, y + h / 2.0)
        self.fitInView(QRectF(x, y, w, h), Qt.AspectRatioMode.KeepAspectRatio)

    # ── Events ──────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_view()

    def wheelEvent(self, event):
        s = self._frame_size()
        if s.width() <= 0:
            return
        vp = self.viewport()
        scene_pt = self.mapToScene(event.position().toPoint())
        norm_x = event.position().x() / max(1, vp.width())
        norm_y = event.position().y() / max(1, vp.height())
        old = self._zoom
        factor = _ZOOM_STEP if event.angleDelta().y() > 0 else 1.0 / _ZOOM_STEP
        self._zoom = clamp_zoom(old * factor)
        if self._zoom != old:
            cx, cy = recenter_on_point(
                scene_pt.x(), scene_pt.y(), norm_x, norm_y,
                s.width(), s.height(), self._zoom,
            )
            self._center = QPointF(cx, cy)
        self._update_view()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_zoomed:
            self._pan_last = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_last is not None:
            s = self._frame_size()
            vw = max(1, self.viewport().width())
            scene_per_px = (s.width() / self._zoom) / vw
            d = event.position() - self._pan_last
            self._center = QPointF(
                self._center.x() - d.x() * scene_per_px,
                self._center.y() - d.y() * scene_per_px,
            )
            self._pan_last = event.position()
            self._update_view()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._pan_last is not None:
            self._pan_last = None
            self.unsetCursor()
        super().mouseReleaseEvent(event)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ui.py::test_zoomable_video_view_creates tests/test_ui.py::test_zoomable_video_view_zoom_state -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add videotagger/ui/zoomable_video_view.py tests/test_ui.py
git commit -m "feat: ZoomableVideoView widget"
```

---

## Task 3: Use ZoomableVideoView in PlayerWidget

**Files:**
- Modify: `videotagger/ui/player_widget.py`
- Test: `tests/test_ui.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ui.py`:

```python
def test_player_widget_has_zoom(qtbot):
    from videotagger.ui.player_widget import PlayerWidget
    from videotagger.ui.zoomable_video_view import ZoomableVideoView
    w = PlayerWidget()
    qtbot.addWidget(w)
    assert isinstance(w._zoom_view, ZoomableVideoView)
    w.reset_zoom()
    w.zoom_in()
    assert w._zoom_view._zoom > 1.0
    w.reset_zoom()
    assert w._zoom_view._zoom == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui.py::test_player_widget_has_zoom -v`
Expected: FAIL — `AttributeError: 'PlayerWidget' object has no attribute '_zoom_view'`

- [ ] **Step 3: Edit the implementation**

In `videotagger/ui/player_widget.py`, change the import line:

```python
from PyQt6.QtMultimediaWidgets import QVideoWidget
```

to:

```python
from videotagger.ui.zoomable_video_view import ZoomableVideoView
```

Replace the video-widget block in `_setup_ui` (the lines creating `self._video_widget`):

```python
        self._video_widget = QVideoWidget()
        self._video_widget.setMinimumHeight(200)
        self._player.setVideoOutput(self._video_widget)
        # Force native HWND creation so the video renderer has a valid surface.
        self._video_widget.winId()
        layout.addWidget(self._video_widget, stretch=1)
```

with:

```python
        self._zoom_view = ZoomableVideoView()
        self._zoom_view.setMinimumHeight(200)
        self._player.setVideoOutput(self._zoom_view.video_item)
        layout.addWidget(self._zoom_view, stretch=1)
```

Add these public methods to `PlayerWidget` (place them in the "Public API" section, e.g. after `get_rate`):

```python
    def zoom_in(self) -> None:
        self._zoom_view.zoom_in()

    def zoom_out(self) -> None:
        self._zoom_view.zoom_out()

    def reset_zoom(self) -> None:
        self._zoom_view.reset_zoom()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ui.py::test_player_widget_creates tests/test_ui.py::test_player_widget_has_zoom -v`
Expected: PASS (2 passed) — the existing creation test still passes after the swap.

- [ ] **Step 5: Commit**

```bash
git add videotagger/ui/player_widget.py tests/test_ui.py
git commit -m "feat: zoomable video surface in PlayerWidget"
```

---

## Task 4: Wire zoom keyboard shortcuts in MainWindow

**Files:**
- Modify: `videotagger/ui/main_window.py`
- Test: `tests/test_ui.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ui.py`:

```python
def test_main_window_zoom_shortcuts(qtbot):
    from PyQt6.QtGui import QShortcut
    from videotagger.ui.main_window import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    keys = {sc.key().toString() for sc in win.findChildren(QShortcut)}
    assert "0" in keys
    assert "-" in keys
    assert ("+" in keys) or ("=" in keys)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui.py::test_main_window_zoom_shortcuts -v`
Expected: FAIL — assertion error, `"0"` not in shortcut keys.

- [ ] **Step 3: Edit the implementation**

In `videotagger/ui/main_window.py`, inside `_setup_shortcuts`, add after the existing `QShortcut("]", ...)` block (before the `Escape` shortcut):

```python
        QShortcut("+", self).activated.connect(self.player.zoom_in)
        QShortcut("=", self).activated.connect(self.player.zoom_in)
        QShortcut("-", self).activated.connect(self.player.zoom_out)
        QShortcut("0", self).activated.connect(self.player.reset_zoom)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ui.py::test_main_window_zoom_shortcuts tests/test_ui.py::test_main_window_opens -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add videotagger/ui/main_window.py tests/test_ui.py
git commit -m "feat: +/-/0 zoom shortcuts in main window"
```

---

## Task 5: Use ZoomableVideoView in PresentationWindow (with per-clip reset)

**Files:**
- Modify: `videotagger/ui/presentation_window.py`
- Test: `tests/test_ui.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_ui.py`:

```python
def test_presentation_window_zoom_resets_on_clip(qtbot):
    from videotagger.ui.presentation_window import PresentationWindow
    from videotagger.ui.zoomable_video_view import ZoomableVideoView
    from videotagger.models.project import Clip
    clip = Clip(category_id="c1", label="Goal", start=1.0, end=2.0)
    w = PresentationWindow("video.mp4", [clip], "Test Playlist")
    qtbot.addWidget(w)
    assert isinstance(w._zoom_view, ZoomableVideoView)
    # Simulate a user-applied zoom, then advancing to a clip resets it.
    w._zoom_view._zoom = 2.0
    w._play_clip(0)
    assert w._zoom_view._zoom == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui.py::test_presentation_window_zoom_resets_on_clip -v`
Expected: FAIL — `AttributeError: 'PresentationWindow' object has no attribute '_zoom_view'`

- [ ] **Step 3: Edit the implementation**

In `videotagger/ui/presentation_window.py`:

Change the import:

```python
from PyQt6.QtMultimediaWidgets import QVideoWidget
```

to:

```python
from videotagger.ui.zoomable_video_view import ZoomableVideoView
```

In `_setup_ui`, replace the video-widget block:

```python
        self._video_widget = QVideoWidget(self)
        self._video_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._player.setVideoOutput(self._video_widget)
        self._video_widget.winId()
```

with:

```python
        self._zoom_view = ZoomableVideoView(self)
        self._zoom_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._player.setVideoOutput(self._zoom_view.video_item)
```

In `resizeEvent`, replace:

```python
        self._video_widget.resize(self.size())
```

with:

```python
        self._zoom_view.resize(self.size())
```

In `_play_clip`, add a zoom reset right after `self._current_index = index` line so each clip starts at fit:

```python
        self._current_index = index
        self._zoom_view.reset_zoom()
```

In `keyPressEvent`, add zoom key handling. Insert these branches before the final `else:` clause:

```python
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self._zoom_view.zoom_in()

        elif key == Qt.Key.Key_Minus:
            self._zoom_view.zoom_out()

        elif key == Qt.Key.Key_0:
            self._zoom_view.reset_zoom()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ui.py::test_presentation_window_creates tests/test_ui.py::test_presentation_window_zoom_resets_on_clip -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add videotagger/ui/presentation_window.py tests/test_ui.py
git commit -m "feat: zoomable video surface in Presentation Mode with per-clip reset"
```

---

## Task 6: Full regression run + manual verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest tests/ -v`
Expected: all tests PASS (existing + new). No errors from the `QVideoWidget` → `ZoomableVideoView` swap.

- [ ] **Step 2: Manual verification — main player**

Run: `python main.py`, open a video, and confirm:
- Scroll wheel over the video zooms in/out, centered on the cursor.
- `+` / `-` zoom in/out; `0` resets to full frame.
- Click-drag pans while zoomed; you cannot pan past the frame edges.
- Zoom persists while playing and while scrubbing the seek bar.
- Existing shortcuts still work: `Space`, `I`/`O`, `Left`/`Right`, `[`/`]`, `Ctrl+Z`.

- [ ] **Step 3: Manual verification — Presentation Mode**

Build a playlist with ≥2 clips, right-click → Present, and confirm:
- Zoom (wheel / `+` / `-`) and drag-pan work during playback.
- The HUD, clip label, and pinned notes (`N`) still render on top of the zoomed video.
- Advancing to the next clip (`Tab`) resets zoom to full frame.
- Existing presentation shortcuts still work: `Space`, `Tab`/`Shift+Tab`, `Left`/`Right`, `,`/`.`, `[`/`]`, `Esc`.

- [ ] **Step 4: Update CHANGELOG**

Add an entry to `CHANGELOG.md` under a new unreleased/next-version heading:

```markdown
### Added
- Live zoom & pan in the main player and Presentation Mode: scroll wheel or
  `+`/`-` to zoom, click-drag to pan, `0` to reset. Useful for inspecting a
  region of high-resolution (e.g. 4K) footage.
```

- [ ] **Step 5: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: changelog entry for live video zoom"
```
```
