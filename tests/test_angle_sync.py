# tests/test_angle_sync.py
from videotagger.core.angle_sync import (
    DRIFT_TOLERANCE_S, PeriodMark, active_period, angle_covers, build_angle,
    build_periods, map_to_angle, needs_resync, promote_to_primary, unsynced_periods,
)
from videotagger.models.project import Clip, Period, VideoAngle


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


# ── build_angle (pure inverse: table marks -> periods + angle) ────────────────

def test_build_angle_basic_periods_and_starts():
    marks = [
        PeriodMark(name="Q1", primary_start=10.0, secondary_start=5.0),
        PeriodMark(name="Q2", primary_start=1000.0, secondary_start=600.0),
    ]
    periods, angle = build_angle(
        marks, name="Broadcast", source_paths=["b.mp4"], merged_path="b.mp4",
    )
    assert [p.name for p in periods] == ["Q1", "Q2"]
    assert [p.primary_start for p in periods] == [10.0, 1000.0]
    assert angle.name == "Broadcast"
    assert angle.merged_video_path == "b.mp4"
    # period_starts is keyed by the generated period ids, in order
    assert angle.period_starts[periods[0].id] == 5.0
    assert angle.period_starts[periods[1].id] == 600.0


def test_build_angle_reuses_period_id():
    marks = [PeriodMark(name="Q1", primary_start=10.0, secondary_start=5.0, period_id="p1")]
    periods, angle = build_angle(
        marks, name="B", source_paths=["b.mp4"], merged_path="b.mp4",
    )
    assert periods[0].id == "p1"
    assert angle.period_starts == {"p1": 5.0}


def test_build_angle_generates_period_id_when_absent():
    marks = [PeriodMark(name="Q1", primary_start=10.0, secondary_start=5.0)]
    periods, _ = build_angle(
        marks, name="B", source_paths=["b.mp4"], merged_path="b.mp4",
    )
    assert periods[0].id  # a fresh uuid was assigned


def test_build_angle_omits_missing_secondary_start():
    marks = [
        PeriodMark(name="Q1", primary_start=10.0, secondary_start=5.0, period_id="p1"),
        PeriodMark(name="Q2", primary_start=1000.0, secondary_start=None, period_id="p2"),
    ]
    _, angle = build_angle(marks, name="B", source_paths=["b.mp4"], merged_path="b.mp4")
    assert angle.period_starts == {"p1": 5.0}


def test_build_angle_blank_name_falls_back_to_positional():
    marks = [PeriodMark(name="", primary_start=10.0), PeriodMark(name="  ", primary_start=20.0)]
    periods, _ = build_angle(marks, name="B", source_paths=["b.mp4"], merged_path="b.mp4")
    assert periods[0].name == "P1"
    assert periods[1].name == ""  # whitespace is truthy then stripped, matching old behavior


def test_build_angle_skips_uncaptured_period_rows():
    # an uncaptured period (no primary start) is dropped, not anchored at 0:00
    marks = [PeriodMark(name="Q1", primary_start=10.0, secondary_start=5.0),
             PeriodMark(name="Q3", primary_start=None, secondary_start=None)]
    periods, angle = build_angle(marks, name="B", source_paths=["b.mp4"], merged_path="b.mp4")
    assert [p.name for p in periods] == ["Q1"]
    assert list(angle.period_starts.values()) == [5.0]


def test_build_angle_name_and_source_fallbacks():
    _, angle = build_angle([], name="   ", source_paths=[], merged_path="merged.mp4")
    assert angle.name == "Angle 2"
    assert angle.source_video_paths == ["merged.mp4"]


def test_build_angle_reuses_existing_angle_id():
    _, angle = build_angle(
        [], name="B", source_paths=["b.mp4"], merged_path="b.mp4", existing_angle_id="a1",
    )
    assert angle.id == "a1"


# ── build_periods (canonical periods from table marks; no angle) ──────────────

def test_build_periods_basic():
    marks = [PeriodMark(name="Q1", primary_start=10.0), PeriodMark(name="Q2", primary_start=1000.0)]
    periods = build_periods(marks)
    assert [p.name for p in periods] == ["Q1", "Q2"]
    assert [p.primary_start for p in periods] == [10.0, 1000.0]


def test_build_periods_skips_uncaptured_rows():
    # a row with no captured start is dropped (no fabricated 0:00 anchor)
    periods = build_periods([PeriodMark(name="Q1", primary_start=10.0),
                             PeriodMark(name="Q3", primary_start=None)])
    assert [p.name for p in periods] == ["Q1"]


def test_build_periods_keeps_captured_zero():
    # a genuine 0:00 start (captured) is kept — only None is skipped
    periods = build_periods([PeriodMark(name="Q1", primary_start=0.0)])
    assert len(periods) == 1 and periods[0].primary_start == 0.0


def test_build_periods_reuses_id():
    periods = build_periods([PeriodMark(name="Q1", primary_start=1.0, period_id="p1")])
    assert periods[0].id == "p1"


def test_build_periods_empty():
    assert build_periods([]) == []


# ── angle_covers (is the angle available at a canonical time?) ────────────────

def test_angle_covers_true_when_active_period_synced():
    assert angle_covers(_periods(), _angle(), 1050.0) is True   # Q2, synced


def test_angle_covers_false_when_active_period_missing():
    half = VideoAngle(name="BG", merged_video_path="bg.mp4", period_starts={"p1": 5.0})
    assert angle_covers(_periods(), half, 110.0) is True        # Q1, synced
    assert angle_covers(_periods(), half, 2050.0) is False      # Q3, not synced


def test_angle_covers_true_when_no_periods():
    assert angle_covers([], _angle(), 123.0) is True            # lockstep identity


# ── promote_to_primary (swap which angle is the canonical timeline) ────────────

def _swap_fixture():
    # Old primary = first-half footage; periods anchored on it.
    periods = [Period(name="Q1", primary_start=10.0, id="p1"),
               Period(name="Q2", primary_start=100.0, id="p2")]
    # Target = whole-match footage, synced to both periods.
    angle = VideoAngle(name="Whole Match", source_video_paths=["whole.mp4"],
                       merged_video_path="whole.mp4", period_starts={"p1": 5.0, "p2": 300.0})
    clips = [Clip(category_id="c", label="Goal", start=20.0, end=30.0, id="k1"),   # in Q1
             Clip(category_id="c", label="Mark", start=110.0, end=120.0, id="k2")]  # in Q2
    return periods, clips, angle


def test_unsynced_periods_flags_missing():
    periods = [Period(name="Q1", primary_start=10.0, id="p1"),
               Period(name="Q2", primary_start=100.0, id="p2")]
    angle = VideoAngle(name="X", period_starts={"p1": 5.0})
    assert [p.id for p in unsynced_periods(periods, angle)] == ["p2"]
    assert unsynced_periods(periods, VideoAngle(name="X", period_starts={"p1": 1, "p2": 2})) == []


def test_promote_reanchors_periods_to_new_timeline():
    periods, clips, angle = _swap_fixture()
    s = promote_to_primary(periods, clips, angle,
                           primary_source_paths=["half.mp4"], primary_merged_path="half.mp4")
    assert [(p.name, p.primary_start, p.id) for p in s.periods] == [("Q1", 5.0, "p1"), ("Q2", 300.0, "p2")]


def test_promote_remaps_clips_per_period():
    periods, clips, angle = _swap_fixture()
    s = promote_to_primary(periods, clips, angle,
                           primary_source_paths=["half.mp4"], primary_merged_path="half.mp4")
    assert (s.clips[0].start, s.clips[0].end) == (15.0, 25.0)     # Q1: 5 + (t-10)
    assert (s.clips[1].start, s.clips[1].end) == (310.0, 320.0)   # Q2: 300 + (t-100)
    assert [c.id for c in s.clips] == ["k1", "k2"]                # ids preserved


def test_promote_swaps_paths_and_demotes_old_primary():
    periods, clips, angle = _swap_fixture()
    s = promote_to_primary(periods, clips, angle, primary_source_paths=["half.mp4"],
                           primary_merged_path="half.mp4", demoted_name="Original")
    assert s.merged_video_path == "whole.mp4" and s.source_video_paths == ["whole.mp4"]
    assert s.demoted_angle.name == "Original"
    assert s.demoted_angle.merged_video_path == "half.mp4"
    assert s.demoted_angle.period_starts == {"p1": 10.0, "p2": 100.0}


def test_promote_round_trips_clip_times_back_through_demoted_angle():
    periods, clips, angle = _swap_fixture()
    s = promote_to_primary(periods, clips, angle,
                           primary_source_paths=["half.mp4"], primary_merged_path="half.mp4")
    # mapping a remapped clip back through the demoted angle returns the original time
    assert map_to_angle(s.periods, s.demoted_angle, s.clips[0].start) == 20.0
    assert map_to_angle(s.periods, s.demoted_angle, s.clips[1].start) == 110.0


# ── needs_resync (the secondary-angle drift decision) ─────────────────────────

def test_needs_resync_false_within_tolerance():
    assert needs_resync(10.0, 10.05, tolerance=0.08) is False


def test_needs_resync_true_when_drift_exceeds_tolerance():
    assert needs_resync(10.0, 10.2, tolerance=0.08) is True


def test_needs_resync_boundary_is_not_a_resync():
    # exactly at tolerance is within tolerance (strict >). 0.5 is exactly
    # representable, so this exercises the boundary without float fuzz.
    assert needs_resync(0.0, 0.5, tolerance=0.5) is False
    assert needs_resync(0.0, 0.5, tolerance=0.25) is True


def test_needs_resync_is_symmetric_for_negative_drift():
    assert needs_resync(10.0, 9.8, tolerance=0.08) is True


def test_needs_resync_zero_drift_is_false():
    assert needs_resync(42.0, 42.0, tolerance=0.08) is False


def test_needs_resync_uses_default_tolerance_when_omitted():
    # default is DRIFT_TOLERANCE_S; a drift just over it triggers a resync
    assert needs_resync(0.0, DRIFT_TOLERANCE_S + 0.01) is True
    assert needs_resync(0.0, DRIFT_TOLERANCE_S - 0.01) is False
