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
