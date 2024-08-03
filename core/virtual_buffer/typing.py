from dataclasses import dataclass
from typing import List, Self

# These values have been calculated with some deduction
# And testing using expectations with a set of up to 5 word matches
SELECTION_THRESHOLD = 0.655 # 0.66 with a slight grace threshold
CORRECTION_THRESHOLD = 0.495 # 0.5 with a slgiht grace threshold

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

@dataclass
class VirtualBufferInitialBranch:
    query_indices: List[int]
    buffer_indices: List[int]
    score: float = 0.0
    score_potential: float = 0.0

    def __hash__(self):
        return hash("_".join(map(str, self.query_indices)) + "-" + "_".join(map(str, self.buffer_indices)))

class VirtualBufferMatchCalculation:
    words: List[str]
    weights: List[float]
    potentials: List[float]
    match_threshold: float
    syllables: List[int]
    max_score: float
    length: float
    allowed_skips: int
    purpose: str
    starting_branches: List[VirtualBufferInitialBranch]

    def __init__(self, words: List[str], weights: List[str], syllables: List[int], match_threshold = 0, max_score_per_word = 1.2, purpose = "selection"):
        self.words = words
        self.length = len(words)
        self.weights = weights
        self.syllables = syllables
        self.match_threshold = match_threshold
        self.max_score = max_score_per_word
        self.potentials = [weight * max_score_per_word for weight in weights]
        self.purpose = purpose
        self.allowed_skips = len(words) - (1 if purpose == "correction" else 2 )
        self.starting_branches = []

    # Calculate the list of possible search branches that can lead to a match, sorted by most likely
    def get_possible_branches(self) -> List[List[int]]:
        impossible_potential = 0
        for potential in self.potentials:
            if self.max_score - potential < self.match_threshold:
                impossible_potential = max(potential, impossible_potential)
        
        # Add two- and three-word combinations as well
        combined_potentials = []
        for index, potential in enumerate(self.potentials):
            if index + 1 < len(self.potentials) and self.potentials[index] + self.potentials[index + 1] >= impossible_potential:
                combined_potentials.append({"index": [index, index + 1], "potential": self.potentials[index] + self.potentials[index + 1]})
            if index + 2 < len(self.potentials) and self.potentials[index] + self.potentials[index + 1] + + self.potentials[index + 2] >= impossible_potential:
                combined_potentials.append({"index": [index, index + 1, index + 2], "potential": self.potentials[index] + self.potentials[index + 1] + self.potentials[index + 2]})

        sorted_potentials = [{"index": [index], "potential": potential} for index, potential in enumerate(self.potentials) if potential >= impossible_potential]
        sorted_potentials.extend(combined_potentials)
        sorted_potentials.sort(key=lambda x: x["potential"], reverse=True)

        return [potential["index"] for potential in sorted_potentials]
    
    def append_starting_branch(self, query_indices: List[int], buffer_indices: List[int], score: float):
        combined_weight = sum([self.weights[index] for index in query_indices])
        reduced_potential = (self.max_score - score) * combined_weight
        self.starting_branches.append(VirtualBufferInitialBranch(query_indices, buffer_indices, score, self.max_score - reduced_potential))

    def get_starting_branches(self, submatrix) -> List[VirtualBufferInitialBranch]:
        return sorted(list(set([branch for branch in self.starting_branches if submatrix.is_valid_index(branch.buffer_indices[0] - submatrix.index)])), key=lambda branch: branch.score, reverse=True)

@dataclass
class VirtualBufferMatchMatrix:
    index: int
    tokens: List[VirtualBufferToken]
    end_index: int
    length: int

    def __init__(self, index: int, tokens: List[VirtualBufferToken]):
        self.index = index
        self.end_index = index + len(tokens) - 1
        self.tokens = tokens
        self.length = len(tokens)

    def get_submatrix(self, starting_index: int, ending_index: int):
        # These use local indices that get translated to global indices later
        max_index = len(self.tokens)
        submatrix_tokens = []
        if starting_index <= ending_index and starting_index >= 0 and ending_index <= max_index:
            submatrix_tokens = self.tokens[starting_index:ending_index]
        return VirtualBufferMatchMatrix(self.index + starting_index, submatrix_tokens)

    def is_valid_index(self, index) -> bool:
        return index >= 0 and index < self.length

    def to_global_index(self, index) -> int:
        return self.index + index
    
    def __hash__(self) -> int:
        return hash(str(self.index) + "_" + str(self.length))

@dataclass
class VirtualBufferMatch:
    query_indices: List[List[int]]
    buffer_indices: List[List[int]]
    query: List[str]
    buffer: List[str]
    scores: List[float]
    score_potential: float
    distance: float = 0.0

    def get_next_query_index(self, submatrix: VirtualBufferMatchMatrix, index_addition:int = 1) -> int:
        if index_addition < 0:
            next_query_index = self.query_indices[0][0] + index_addition if len(self.query_indices) > 0 else -1            
        else:
            next_query_index = self.query_indices[-1][-1] + index_addition if len(self.query_indices) > 0 else submatrix.length
        return next_query_index

    def get_next_buffer_index(self, submatrix: VirtualBufferMatchMatrix, index_addition:int = 1) -> int:
        if index_addition < 0:
            next_buffer_index = self.buffer_indices[0][0] + index_addition if len(self.buffer_indices) > 0 else -1            
        else:
            next_buffer_index = self.buffer_indices[-1][-1] + index_addition if len(self.buffer) > 0 else submatrix.length
        return next_buffer_index

    def can_expand_backward(self, submatrix: VirtualBufferMatchMatrix) -> bool:
        next_query_index = self.get_next_query_index(submatrix, -1)
        next_buffer_index = self.get_next_buffer_index(submatrix, -1)
        return next_query_index >= 0 and submatrix.is_valid_index(next_buffer_index)

    def can_expand_forward(self, calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix) -> bool:
        next_query_index = self.get_next_query_index(submatrix, 1)
        next_buffer_index = self.get_next_buffer_index(submatrix, 1)
        return next_query_index < calculation.length and submatrix.is_valid_index(next_buffer_index)

    def is_valid_index(self, calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, index: int) -> bool:
        return index >= 0 and index < submatrix.length and index < calculation.length
    
    def calculate_distance(self, leftmost_index: int, rightmost_index: int):
        if len(self.buffer_indices) > 0:
            if self.buffer_indices[-1][-1] < leftmost_index:
                self.distance = leftmost_index - self.buffer_indices[-1][-1]
            elif self.buffer_indices[0][0] > rightmost_index:
                self.distance = self.buffer_indices[0][0] - rightmost_index
            else:
                self.distance = 0

    def reduce_potential(self, max_score: float, score: float, weight: float):
        self.score_potential -= (max_score - score) * weight

    def to_global_index(self, submatrix: VirtualBufferMatchMatrix):
        global_buffer_indices = []
        for index_list in self.buffer_indices:
            global_buffer_indices.append([submatrix.to_global_index(index) for index in index_list])
        self.buffer_indices = global_buffer_indices

    def clone(self) -> Self:
        return VirtualBufferMatch(list(self.query_indices), list(self.buffer_indices), list(self.query), list(self.buffer), list(self.scores), self.score_potential, self.distance)

    def __hash__(self):
        query_indices = "-".join(map(str, ["".join(str(index)) for index in self.query_indices]))
        buffer_indices = "-".join(map(str, ["".join(str(index)) for index in self.buffer_indices]))
        return hash(query_indices + "-" + buffer_indices)


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