from dataclasses import dataclass

@dataclass
class InputHistoryEvent:
    text: str
    phrase: str
    format: str
    line_index: int = 0
    index_from_line_end: int = 0