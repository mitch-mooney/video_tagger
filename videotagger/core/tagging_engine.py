from enum import Enum, auto
from typing import Optional, Tuple

class TaggingState(Enum):
    IDLE = auto()
    MARKING = auto()

class TaggingEngine:
    def __init__(self):
        self._state = TaggingState.IDLE
        self._mark_in: Optional[float] = None

    @property
    def state(self) -> TaggingState:
        return self._state

    @property
    def mark_in(self) -> Optional[float]:
        return self._mark_in

    def press_in(self, position: float) -> None:
        self._state = TaggingState.MARKING
        self._mark_in = position

    def press_out(self, position: float) -> Tuple[float, float]:
        if self._state != TaggingState.MARKING:
            raise ValueError("Cannot mark out: no start marked yet")
        if position <= self._mark_in:
            raise ValueError("End must be after start position")
        start = self._mark_in
        self._state = TaggingState.IDLE
        self._mark_in = None
        return start, position

    def cancel(self) -> None:
        self._state = TaggingState.IDLE
        self._mark_in = None
