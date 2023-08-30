from dataclasses import dataclass

@dataclass
class InputHistoryEvent:
    phrase: str
    text: str
    format: str
    start_index: int
    end_index: int