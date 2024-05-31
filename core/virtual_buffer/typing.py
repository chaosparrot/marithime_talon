from dataclasses import dataclass
from typing import List

@dataclass
class VirtualBufferToken:
    text: str
    phrase: str
    format: str
    line_index: int = 0
    index_from_line_end: int = 0

@dataclass
class VirtualBufferTokenMatch:
    starts: int
    indices: List[int]
    comparisons: List[List[str]]
    score: float
    scores: List[float]
    syllable_score: float
    syllable_scores: List[float]
    distance: float = 0.0

class VirtualBufferMatchCalculation:
    words: List[str]
    weights: List[float]
    potentials: List[float]
    match_threshold: float
    max_score: float
    length: float

    def __init__(self, words: List[str], weights: List[str], match_threshold = 0, max_score_per_word = 3):
        self.words = words
        self.length = len(words)
        self.weights = weights
        self.match_threshold = match_threshold
        self.max_score = max_score_per_word
        self.potentials = [weight * max_score_per_word for weight in weights]

    # Calculate the list of possible search branches that can lead to a match, sorted by most likely
    def get_possible_branches(self) -> List[List[int]]:
        # TODO IMPROVE IMPOSSIBLE BRANCH DETECTION
        impossible_potential = 0
        for potential in self.potentials:
            if self.max_score - potential < self.match_threshold:
                impossible_potential = max(potential, impossible_potential)
        
        # Add two-word combinations as well
        combined_potentials = []
        for index, potential in enumerate(self.potentials):
            if index + 1 < len(self.potentials) and self.potentials[index] + self.potentials[index + 1] >= impossible_potential:
                combined_potentials.append({"index": [index, index + 1], "potential": self.potentials[index] + self.potentials[index + 1]})

        sorted_potentials = [{"index": [index], "potential": potential} for index, potential in enumerate(self.potentials) if potential >= impossible_potential]
        sorted_potentials.extend(combined_potentials)
        sorted_potentials.sort(key=lambda x: x["potential"], reverse=True)

        return [potential["index"] for potential in sorted_potentials]

@dataclass
class VirtualBufferMatchMatrix:
    index: int
    tokens: List[VirtualBufferToken]
    end_index: int

    def __init__(self, index: int, tokens: List[VirtualBufferToken]):
        self.index = index
        self.end_index = index + len(tokens) - 1
        self.tokens = tokens

    def get_submatrix(self, starting_index: int, ending_index: int):
        max_index = self.index + len(self.tokens)
        submatrix_tokens = []
        if starting_index <= ending_index and starting_index >= self.index and ending_index <= max_index:
            submatrix_tokens = self.tokens[starting_index:ending_index]
        return VirtualBufferMatchMatrix(starting_index, submatrix_tokens)

    def to_global_index(self, index):
        return self.index + index

@dataclass
class VirtualBufferMatch:
    query_indices: List[List[int]]
    replace_indices: List[List[int]]
    query: List[str]
    buffer: List[str]
    scores: List[float]
    current_score: float
    distance: float = 0.0

    def can_expand_backward(self, submatrix: VirtualBufferMatchMatrix) -> bool:
        next_query_index = self.query_indices[0][0] - 1 if len(self.query_indices) > 0 else -1
        return next_query_index >= 0

    def can_expand_forward(self, calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix) -> bool:
        matrix_length = len(submatrix.tokens)
        next_query_index = self.query_indices[-1][-1] + 1 if len(self.query_indices) > 0 else matrix_length
        return next_query_index < matrix_length and next_query_index < calculation.length


@dataclass
class VirtualBufferTokenContext:
    character_index: 0
    previous: VirtualBufferToken = None
    current: VirtualBufferToken = None
    next: VirtualBufferToken = None

@dataclass
class InputMutation:
    time: float
    insertion: str
    deletion: str
    previous: str = ""
    next: str = ""

@dataclass
class InputFix:
    key: str
    from_text: str
    to_text: str
    amount: int = 0
    previous: str = ""
    next: str = ""