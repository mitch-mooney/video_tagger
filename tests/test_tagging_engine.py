import pytest
from videotagger.core.tagging_engine import TaggingEngine, TaggingState

def test_initial_state_is_idle():
    engine = TaggingEngine()
    assert engine.state == TaggingState.IDLE
    assert engine.mark_in is None

def test_press_in_sets_marking_state():
    engine = TaggingEngine()
    engine.press_in(10.0)
    assert engine.state == TaggingState.MARKING
    assert engine.mark_in == 10.0

def test_press_in_twice_updates_start():
    engine = TaggingEngine()
    engine.press_in(10.0)
    engine.press_in(12.0)
    assert engine.mark_in == 12.0

def test_press_out_returns_start_end():
    engine = TaggingEngine()
    engine.press_in(10.0)
    start, end = engine.press_out(20.0)
    assert start == 10.0
    assert end == 20.0

def test_press_out_resets_to_idle():
    engine = TaggingEngine()
    engine.press_in(10.0)
    engine.press_out(20.0)
    assert engine.state == TaggingState.IDLE
    assert engine.mark_in is None

def test_press_out_without_in_raises():
    engine = TaggingEngine()
    with pytest.raises(ValueError, match="start"):
        engine.press_out(20.0)

def test_press_out_before_in_raises():
    engine = TaggingEngine()
    engine.press_in(20.0)
    with pytest.raises(ValueError, match="after"):
        engine.press_out(10.0)

def test_cancel_resets_state():
    engine = TaggingEngine()
    engine.press_in(10.0)
    engine.cancel()
    assert engine.state == TaggingState.IDLE
    assert engine.mark_in is None
