from dataclasses import dataclass
from typing import List

@dataclass
class InputHistoryEvent:
    text: str
    phrase: str
    format: str
    line_index: int = 0
    index_from_line_end: int = 0

@dataclass
class InputContext:
    character_index: 0
    previous: InputHistoryEvent = None
    current: InputHistoryEvent = None
    next: InputHistoryEvent = None

@dataclass
class InputEventMatch:
    starts: int
    indices: List[int]
    score: float
    scores: List[float]
    distance: float = 0.0