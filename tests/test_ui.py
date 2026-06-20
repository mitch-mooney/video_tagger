# tests/test_ui.py
# Smoke tests for UI components — Tasks 9-17
import pytest


def test_main_window_opens(qtbot):
    from videotagger.ui.main_window import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    assert win.isVisible()


def test_player_widget_creates(qtbot):
    from videotagger.ui.player_widget import PlayerWidget
    w = PlayerWidget()
    qtbot.addWidget(w)
    w.show()
    assert w.isVisible()
    assert hasattr(w, 'position_changed')
    assert hasattr(w, 'duration_changed')


def test_timeline_widget_creates(qtbot):
    from videotagger.ui.timeline_widget import TimelineWidget
    w = TimelineWidget()
    qtbot.addWidget(w)
    w.show()
    assert w.isVisible()


def test_tag_panel_creates(qtbot):
    from videotagger.ui.tag_panel import TagPanel
    w = TagPanel()
    qtbot.addWidget(w)
    w.show()
    assert w.isVisible()


def test_clips_panel_creates(qtbot):
    from videotagger.ui.clips_panel import ClipsPanel
    w = ClipsPanel()
    qtbot.addWidget(w)
    w.show()
    assert w.isVisible()
    assert w._tabs.count() == 2


def test_presentation_window_creates(qtbot):
    from videotagger.ui.presentation_window import PresentationWindow
    w = PresentationWindow("video.mp4", [], "Test Playlist")
    qtbot.addWidget(w)
    w.show()
    assert w.isVisible()


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


def test_main_window_zoom_shortcuts(qtbot):
    from PyQt6.QtGui import QShortcut
    from videotagger.ui.main_window import MainWindow
    win = MainWindow()
    qtbot.addWidget(win)
    keys = {sc.key().toString() for sc in win.findChildren(QShortcut)}
    assert "0" in keys
    assert "-" in keys
    assert ("+" in keys) or ("=" in keys)
