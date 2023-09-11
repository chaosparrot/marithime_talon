from dataclasses import dataclass

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