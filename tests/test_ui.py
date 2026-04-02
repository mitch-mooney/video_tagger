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
