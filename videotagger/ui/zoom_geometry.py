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
