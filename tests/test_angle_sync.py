# tests/test_angle_sync.py
from videotagger.core.angle_sync import active_period, map_to_angle
from videotagger.models.project import Period, VideoAngle


def _periods():
    # Primary (canonical) timeline: continuous recording with breaks between quarters.
    return [
        Period(name="Q1", primary_start=10.0, id="p1"),
        Period(name="Q2", primary_start=1000.0, id="p2"),
        Period(name="Q3", primary_start=2000.0, id="p3"),
        Period(name="Q4", primary_start=3000.0, id="p4"),
    ]


def _angle():
    # Secondary angle: started/stopped each quarter, so quarters sit back-to-back.
    return VideoAngle(
        name="Broadcast",
        merged_video_path="b.mp4",
        period_starts={"p1": 5.0, "p2": 600.0, "p3": 1200.0, "p4": 1800.0},
    )


# ── active_period ───────────────────────────────────────────────────────────

def test_active_period_within_first_period():
    assert active_period(_periods(), 500.0).id == "p1"


def test_active_period_at_boundary_is_next_period():
    # exactly at Q2's primary_start belongs to Q2
    assert active_period(_periods(), 1000.0).id == "p2"


def test_active_period_before_first_clamps_to_first():
    assert active_period(_periods(), 0.0).id == "p1"


def test_active_period_after_last_is_last():
    assert active_period(_periods(), 9999.0).id == "p4"


def test_active_period_empty_returns_none():
    assert active_period([], 100.0) is None


# ── map_to_angle ────────────────────────────────────────────────────────────

def test_map_within_period_applies_offset():
    # 100s into Q1 on primary (t=110) -> 100s into Q1 on angle (5 + 100)
    assert map_to_angle(_periods(), _angle(), 110.0) == 105.0


def test_map_resyncs_each_period():
    # 50s into Q2 on primary (t=1050) -> angle Q2 start (600) + 50
    assert map_to_angle(_periods(), _angle(), 1050.0) == 650.0


def test_map_before_first_period_uses_first_offset():
    # t=0 is 10s before Q1 primary_start -> angle 5 + (0 - 10) = -5 clamps to 0
    assert map_to_angle(_periods(), _angle(), 0.0) == 0.0


def test_map_empty_periods_is_identity():
    assert map_to_angle([], _angle(), 123.0) == 123.0


def test_map_missing_period_start_is_identity():
    angle = VideoAngle(name="X", merged_video_path="x.mp4", period_starts={})
    assert map_to_angle(_periods(), angle, 1050.0) == 1050.0


def test_map_never_returns_negative():
    angle = VideoAngle(name="X", merged_video_path="x.mp4", period_starts={"p1": 0.0})
    assert map_to_angle([Period(name="Q1", primary_start=100.0, id="p1")], angle, 0.0) == 0.0
