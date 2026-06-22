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

from videotagger.models.project import Period, VideoAngle

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

    Blank names fall back to ``P{n}`` (1-based); a missing ``primary_start`` is ``0.0``;
    a mark's ``period_id`` is reused when editing, otherwise a fresh id is assigned.
    """
    periods: List[Period] = []
    for i, mark in enumerate(marks):
        period = Period(
            name=(mark.name or f"P{i + 1}").strip(),
            primary_start=mark.primary_start or 0.0,
        )
        if mark.period_id:
            period.id = mark.period_id
        periods.append(period)
    return periods


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
    periods = build_periods(marks)
    period_starts: dict = {}
    for mark, period in zip(marks, periods):
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
