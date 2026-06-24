"""Pure math for mapping a canonical (primary) timeline position onto a secondary
camera angle, using per-period sync points. No Qt dependencies — see test_angle_sync.py.

The primary/canonical timeline IS the primary angle's video time. Each period is anchored
on that timeline (``Period.primary_start``). A secondary angle stores, per period, the
video-time where that same period begins in its own footage (``VideoAngle.period_starts``).

For a canonical time ``t`` inside period ``P``::

    angle_time = period_starts[P.id] + (t - P.primary_start)

Re-syncing every period absorbs drift between a continuous recording and a per-quarter one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from videotagger.models.project import Clip, Period, VideoAngle

# Re-seek the secondary angle when it drifts more than this (seconds) from the
# mapped target. ≈ 2 frames at 25fps.
DRIFT_TOLERANCE_S = 0.08


def needs_resync(expected: float, actual: float, tolerance: float = DRIFT_TOLERANCE_S) -> bool:
    """Whether a secondary angle at ``actual`` (s) has drifted far enough from its
    mapped ``expected`` (s) to warrant a re-seek. Symmetric; the boundary is within
    tolerance (strict ``>``)."""
    return abs(actual - expected) > tolerance


def active_period(periods: List[Period], t: float) -> Optional[Period]:
    """Return the period containing canonical time ``t``.

    The period with the largest ``primary_start`` that is ``<= t``. Times before the first
    period clamp to the first period. Returns ``None`` if there are no periods.
    """
    if not periods:
        return None
    ordered = sorted(periods, key=lambda p: p.primary_start)
    current = ordered[0]
    for p in ordered:
        if p.primary_start <= t:
            current = p
        else:
            break
    return current


def map_to_angle(periods: List[Period], angle: VideoAngle, t: float) -> float:
    """Map canonical time ``t`` (seconds) to ``angle``'s video time (seconds).

    Falls back to identity (``t``) when there are no periods or the active period has no
    sync point for this angle. Never returns a negative time.
    """
    period = active_period(periods, t)
    if period is None or period.id not in angle.period_starts:
        return max(0.0, t)
    angle_time = angle.period_starts[period.id] + (t - period.primary_start)
    return max(0.0, angle_time)


@dataclass
class PeriodMark:
    """One row of the angle-sync table as plain data (no Qt).

    ``secondary_start`` is the start of this period in the secondary footage, or
    ``None`` if it hasn't been captured yet. ``period_id`` reuses an existing
    period's id when editing, or is ``None`` for a fresh period.
    """
    name: str
    primary_start: Optional[float] = None
    secondary_start: Optional[float] = None
    period_id: Optional[str] = None


def build_periods(marks: List[PeriodMark]) -> List[Period]:
    """Build canonical :class:`Period` objects from table marks. Pure — no Qt.

    A row whose ``primary_start`` was never captured (``None``) is **skipped** — a period
    must be anchored on the primary, and fabricating a ``0:00`` start would corrupt the
    timeline. A captured ``0.0`` is kept (a period genuinely starting at video time 0).
    Blank names fall back to ``P{n}`` (1-based); ``period_id`` is reused when editing.
    """
    periods: List[Period] = []
    for i, mark in enumerate(marks):
        if mark.primary_start is None:
            continue
        period = Period(
            name=(mark.name or f"P{i + 1}").strip(),
            primary_start=mark.primary_start,
        )
        if mark.period_id:
            period.id = mark.period_id
        periods.append(period)
    return periods


def angle_covers(periods: List[Period], angle: VideoAngle, t: float) -> bool:
    """Whether ``angle`` has footage at canonical time ``t`` — i.e. the active period
    has a sync point in this angle. With no periods, the angle plays lockstep (covered).
    Uncovered periods are where the angle should be treated as unavailable (no seek)."""
    period = active_period(periods, t)
    if period is None:
        return True
    return period.id in angle.period_starts


def build_angle(
    marks: List[PeriodMark],
    *,
    name: str,
    source_paths: List[str],
    merged_path: str,
    existing_angle_id: Optional[str] = None,
) -> Tuple[List[Period], VideoAngle]:
    """Build the canonical periods and a secondary :class:`VideoAngle` from table marks.

    The inverse of what :func:`map_to_angle` consumes: each mark becomes a canonical
    :class:`Period`, and the angle's ``period_starts`` maps each period id to its start
    time in the secondary footage. Pure — no Qt. Marks without a ``secondary_start`` are
    left out of ``period_starts``; a blank angle name falls back to ``"Angle 2"`` and empty
    ``source_paths`` falls back to ``[merged_path]``. (Period naming/id rules: see
    :func:`build_periods`.)
    """
    valid = [m for m in marks if m.primary_start is not None]
    periods = build_periods(valid)
    period_starts: dict = {}
    for mark, period in zip(valid, periods):
        if mark.secondary_start is not None:
            period_starts[period.id] = mark.secondary_start

    angle = VideoAngle(
        name=name.strip() or "Angle 2",
        source_video_paths=source_paths or [merged_path],
        merged_video_path=merged_path,
        period_starts=period_starts,
    )
    if existing_angle_id:
        angle.id = existing_angle_id
    return periods, angle


@dataclass
class PrimarySwap:
    """Result of promoting a secondary angle to primary: the re-anchored periods,
    remapped clips, the new primary's paths, and the old primary as a demoted angle."""
    periods: List[Period]
    clips: List[Clip]
    source_video_paths: List[str]
    merged_video_path: str
    demoted_angle: VideoAngle


def unsynced_periods(periods: List[Period], angle: VideoAngle) -> List[Period]:
    """Periods with no sync point in ``angle`` — they can't be re-anchored onto it.
    A promote is only valid when this is empty (then every clip is remappable too)."""
    return [p for p in periods if p.id not in angle.period_starts]


def promote_to_primary(
    periods: List[Period],
    clips: List[Clip],
    angle: VideoAngle,
    *,
    primary_source_paths: List[str],
    primary_merged_path: str,
    demoted_name: str = "Original",
) -> PrimarySwap:
    """Swap the canonical timeline from the current primary onto ``angle``.

    Pure. Pre-condition: ``unsynced_periods(periods, angle)`` is empty (the caller
    validates and reports otherwise). Periods are re-anchored to the angle's start
    times, clip times are remapped per-period (via :func:`map_to_angle`), and the old
    primary (``primary_*`` paths) becomes a secondary :class:`VideoAngle` whose
    ``period_starts`` are the periods' old primary times — so it stays perfectly in
    sync and the remap is exactly reversible.
    """
    new_periods = [
        Period(name=p.name, primary_start=angle.period_starts[p.id], id=p.id)
        for p in periods
    ]
    new_clips = [
        Clip(category_id=c.category_id, label=c.label,
             start=map_to_angle(periods, angle, c.start),
             end=map_to_angle(periods, angle, c.end),
             notes=c.notes, id=c.id)
        for c in clips
    ]
    demoted = VideoAngle(
        name=demoted_name,
        source_video_paths=list(primary_source_paths),
        merged_video_path=primary_merged_path,
        period_starts={p.id: p.primary_start for p in periods},
    )
    return PrimarySwap(
        periods=new_periods,
        clips=new_clips,
        source_video_paths=list(angle.source_video_paths),
        merged_video_path=angle.merged_video_path,
        demoted_angle=demoted,
    )
