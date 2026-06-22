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

from typing import List, Optional

from videotagger.models.project import Period, VideoAngle


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
