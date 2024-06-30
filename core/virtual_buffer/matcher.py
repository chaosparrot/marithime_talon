from ..phonetics.phonetics import PhoneticSearch
from ..phonetics.detection import EXACT_MATCH, HOMOPHONE_MATCH, PHONETIC_MATCH
from .typing import VirtualBufferToken, VirtualBufferTokenMatch, VirtualBufferMatchCalculation, VirtualBufferMatchMatrix, VirtualBufferMatch, VirtualBufferTokenContext, SELECTION_THRESHOLD, CORRECTION_THRESHOLD
import re
from typing import List, Dict
import math
from functools import cmp_to_key

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", ' ', text).replace("\n", " ")

# Class to find the best matches inside of virtual buffers
class VirtualBufferMatcher:

    phonetic_search: PhoneticSearch = None
    similarity_matrix: Dict[str, float] = None

    def __init__(self, phonetic_search: PhoneticSearch):
        self.phonetic_search = phonetic_search
        self.similarity_matrix = {}

    # Calculate the best matching score
    # Based on the similarity score times the amount of syllables
    # After all, a matching long word gives more confidence than a short word
    def calculate_syllable_score(self, score, query: str, match: str) -> float:
        return self.phonetic_search.calculate_syllable_score(score, normalize_text(query).replace(" ", ''), match)

    def is_phrase_selected(self, virtual_buffer, phrase: str) -> bool:
        if virtual_buffer.is_selecting():
            selection = virtual_buffer.caret_tracker.get_selection_text()
            return self.phonetic_search.phonetic_similarity_score(normalize_text(selection).replace(" ", ''), phrase) >= 2
        return False

    def has_matching_phrase(self, virtual_buffer, phrase: str) -> bool:
        score = 0
        for token in virtual_buffer.tokens:
            score = self.phonetic_search.phonetic_similarity_score(phrase, token.phrase)
            if score >= 0.6:
                return True

        return False

    def find_top_three_matches_in_matrix(self, virtual_buffer, phrases: List[str], match_threshold: float = SELECTION_THRESHOLD, selecting: bool = False, for_correction: bool = False):
        match_calculation = self.generate_match_calculation(phrases, match_threshold)
        matrix = VirtualBufferMatchMatrix(0, virtual_buffer.tokens)
        submatrices = self.find_potential_submatrices(match_calculation, matrix)

        leftmost_token_index = virtual_buffer.determine_leftmost_token_index()[0]
        rightmost_token_index = virtual_buffer.determine_rightmost_token_index()[0]
        split_submatrices = self.split_submatrices_by_cursor_position(submatrices, leftmost_token_index, rightmost_token_index)
        highest_score_achieved = False
        matches = []

        for matrix_group in split_submatrices:
            match_calculation.match_threshold = match_threshold
            matrix_group_matches = []
            highest_match = 0
            for submatrix in matrix_group:
                submatrix_matches = self.find_matches_in_matrix(match_calculation, submatrix, highest_match)
                if len(submatrix_matches) > 0:
                    highest_match = max(highest_match, submatrix_matches[0].score_potential)
                    match_calculation.match_threshold = highest_match
                    matrix_group_matches.extend(submatrix_matches)
                    highest_score_achieved = highest_match == match_calculation.max_score

                # Do not seek any further if we have reached the highest possible score
                # Since no improvement is possible
                # Also do not seek further for correction cases as we never look beyond matches closest to the cursor anyway
                if highest_score_achieved or (for_correction and len(submatrix_matches) > 0):
                    break
            
            # Calculate the distance from the cursor
            for matrix_group_match in matrix_group_matches:
                matrix_group_match.calculate_distance(leftmost_token_index, rightmost_token_index)

            if len(matrix_group_matches) > 0:
                if selecting:
                    matrix_group_matches.sort(key = cmp_to_key(self.compare_match_trees_by_score), reverse=True)
                if for_correction:
                    matrix_group_matches.sort(key = cmp_to_key(self.compare_match_trees_by_distance_and_score), reverse=True)
                matches.append(matrix_group_matches[0])
        
        return matches

    # Generate a match calculation based on the words to search for weighted by syllable count
    def generate_match_calculation(self, query_words: List[str], threshold: float = SELECTION_THRESHOLD, max_score_per_word: float = EXACT_MATCH) -> VirtualBufferMatchCalculation:
        syllables_per_word = [self.phonetic_search.syllable_count(word) for word in query_words]
        total_syllables = max(sum(syllables_per_word), 1)
        weights = [syllable_count / total_syllables for syllable_count in syllables_per_word]

        return VirtualBufferMatchCalculation(query_words, weights, threshold, max_score_per_word)
    
    # Generate a list of (sorted) potential submatrices to look through
    def find_potential_submatrices(self, match_calculation: VirtualBufferMatchCalculation, matrix: VirtualBufferMatchMatrix) -> List[VirtualBufferMatchMatrix]:
        word_indices = match_calculation.get_possible_branches()
        max_submatrix_size = len(match_calculation.words) * 3
        sub_matrices = []
        for word_index in word_indices:
            sub_matrices.extend(self.find_potential_submatrices_for_words(matrix, match_calculation, word_index, max_submatrix_size))

        sub_matrices = self.simplify_submatrices(sub_matrices)

        return sub_matrices

    # Split the submatrices up into three zones that are important for selection
    # The zone before, on and after the caret
    def split_submatrices_by_cursor_position(self, submatrices: List[VirtualBufferMatchMatrix], left_index: int, right_index: int) -> List[List[VirtualBufferMatchMatrix]]:
        before = []
        current = []
        after = []

        for submatrix in submatrices:
            if submatrix.end_index < left_index:
                before.append(submatrix)
            elif submatrix.index > right_index:
                after.append(submatrix)
            else:
                current.append(submatrix)

        # Sort the matrices before the cursor in the opposite direction,
        # the assumption being that the closest match to the cursor matters most
        before.reverse()

        return [before, current, after]
    
    def find_matches_in_matrix(self, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, highest_match: float = 0, early_stopping: bool = True) -> List[VirtualBufferMatch]:
        branches = match_calculation.get_possible_branches()
        query = match_calculation.words
        buffer = [token.phrase for token in submatrix.tokens]

        starting_match = VirtualBufferMatch([], [], [], [], [], match_calculation.max_score, 0)

        # Initial branches
        match_branches = []
        for branch in branches:
            query_match_branch = starting_match.clone()
            query_match_branch.query_indices.append(branch)
            query_match_branch.query.extend([query[index] for index in branch])
            combined_weight = sum([match_calculation.weights[index] for index in branch])
            is_multiple_query_match = len(branch) > 1

            word_index = branch[0]
            max_buffer_search = len(buffer) - (len(query) - 1)
            for buffer_index in range(word_index, word_index + max_buffer_search):
                buffer_word = buffer[buffer_index]
                score = self.get_memoized_similarity_score("".join(query_match_branch.query), buffer_word)

                # Only add a match branch for a combined query search if the combined search scores higher than individual scores
                if is_multiple_query_match:
                    individual_scores = [self.get_memoized_similarity_score(word, buffer_word) for word in match_calculation.words]
                    if max(individual_scores) > score:
                        continue

                # Attempt multi-buffer matches if they score higher than the single match buffer case
                highest_match_score = score
                buffer_indices_to_use = [buffer_index]
                if not is_multiple_query_match:
                    next_word = ""

                    # Combine two words
                    if buffer_index + 1 <= max_buffer_search:
                        next_word = buffer[buffer_index + 1]
                        next_forward_score = self.get_memoized_similarity_score("".join(query_match_branch.query), buffer_word + next_word)
                        if next_forward_score > highest_match_score:
                            highest_match_score = next_forward_score
                            buffer_indices_to_use = [buffer_index, buffer_index + 1]

                    # Combine three words
                    if buffer_index + 2 <= max_buffer_search and len(buffer_indices_to_use) == 2:
                        second_next_word = buffer[buffer_index + 2]
                        next_forward_score = self.get_memoized_similarity_score("".join(query_match_branch.query), buffer_word + next_word + second_next_word)
                        if next_forward_score > highest_match_score:
                            highest_match_score = next_forward_score
                            buffer_indices_to_use = [buffer_index, buffer_index + 1, buffer_index + 2]

                    # Combine two words backward
                    if buffer_index - 1 >= word_index:
                        previous_word = buffer[buffer_index - 1]
                        previous_backward_score = self.get_memoized_similarity_score("".join(query_match_branch.query), previous_word + buffer_word)
                        if previous_backward_score > highest_match_score:
                            highest_match_score = previous_backward_score
                            buffer_indices_to_use = [buffer_index - 1, buffer_index]

                    # Combine three words backward
                    if buffer_index - 2 >= word_index and len(buffer_indices_to_use) == 2:
                        second_previous_word = buffer[buffer_index - 2]
                        previous_backward_score = self.get_memoized_similarity_score("".join(query_match_branch.query), second_previous_word + previous_word + buffer_word)
                        if previous_backward_score > highest_match_score:
                            highest_match_score = previous_backward_score
                            buffer_indices_to_use = [buffer_index - 2, buffer_index - 1, buffer_index]
                
                # Add only a single combination even if multiple options might have a better overall chance
                # Only if the words compare well enough will we continue searching
                if highest_match_score >= match_calculation.match_threshold:
                    match_branch = query_match_branch.clone()
                    match_branch.buffer_indices.append(buffer_indices_to_use)
                    match_branch.buffer.extend([buffer[buffer_index] for buffer_index in buffer_indices_to_use])
                    match_branch.scores.append(highest_match_score)
                    match_branch.reduce_potential(match_calculation.max_score, score, combined_weight) 
                    match_branches.append(match_branch)

        # Filter searches that do not match the previous best and sort by the best score first
        searches = []
        for match_root in match_branches:
            searches.extend(self.expand_match_tree(match_root, match_calculation, submatrix))
        filtered_searches = [search for search in searches if search.score_potential >= highest_match]
        filtered_searches.sort(key = cmp_to_key(self.compare_match_trees_by_score), reverse=True)

        return filtered_searches

    def expand_match_tree(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix) -> List[VirtualBufferMatchMatrix]:
        match_trees = [match_tree]
        expanded_matrices: List[VirtualBufferMatch] = []

        # First expand backwards
        if match_tree.can_expand_backward(submatrix):
            can_expand_backward_count = 1
            while can_expand_backward_count != 0:
                expanded_matrices = []
                for match_tree in match_trees:
                    expanded_matrices.extend(self.expand_match_tree_backward(match_tree, match_calculation, submatrix))
                can_expand_backward_count = sum([expanded_matrix.can_expand_backward(submatrix) for expanded_matrix in expanded_matrices])
                match_trees = expanded_matrices

        # Then expand forwards if possible
        if match_tree.can_expand_forward(match_calculation, submatrix):
            can_expand_forward_count = 1
            while can_expand_forward_count != 0:
                expanded_matrices = []
                for match_tree in match_trees:
                    expanded_matrices.extend(self.expand_match_tree_forward(match_tree, match_calculation, submatrix))
                can_expand_forward_count = sum([expanded_matrix.can_expand_forward(match_calculation, submatrix) for expanded_matrix in expanded_matrices])
                match_trees = expanded_matrices

        # TODO FILTER BEST?

        return match_trees

    def expand_match_tree_backward(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix) -> List[VirtualBufferMatch]:
        expanded_match_trees = []

        # If no further expansion is possible, just return the input match tree
        if not match_tree.can_expand_backward(submatrix):
            expanded_match_trees.append(match_tree)
        else:
            expanded_match_trees.extend(self.expand_match_tree_in_direction(match_tree, match_calculation, submatrix, -1))

        # Only keep the branches that have a possibility to become the best
        return [expanded_match_tree for expanded_match_tree in expanded_match_trees if expanded_match_tree.score_potential >= match_calculation.match_threshold]
        
    def expand_match_tree_forward(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix) -> List[VirtualBufferMatch]:
        expanded_match_trees = []

        # If no further expansion is possible, just return the input match tree
        if not match_tree.can_expand_forward(match_calculation, submatrix):
            expanded_match_trees.append(match_tree)
        else:
            expanded_match_trees.extend(self.expand_match_tree_in_direction(match_tree, match_calculation, submatrix, 1))

        # Prune the branches that do not have a possibility to become the best
        return [expanded_match_tree for expanded_match_tree in expanded_match_trees if expanded_match_tree.score_potential >= match_calculation.match_threshold]

    def expand_match_tree_in_direction(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, direction: int = 1) -> List[VirtualBufferMatch]:
        expanded_match_trees = []

        next_query_index = match_tree.get_next_query_index(submatrix, direction)
        next_buffer_index = match_tree.get_next_buffer_index(submatrix, direction)
        next_buffer_skip_index = match_tree.get_next_buffer_index(submatrix, direction * 2)

        single_expanded_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, [next_query_index], [next_buffer_index], direction)
        expanded_match_trees.append(single_expanded_match_tree)
        expanded_match_trees.extend(self.determine_combined_query_matches(match_tree, match_calculation, submatrix, next_query_index, next_buffer_index, direction, single_expanded_match_tree))
        if submatrix.is_valid_index(next_buffer_skip_index):
            expanded_match_trees.extend(self.determine_combined_buffer_matches(match_tree, match_calculation, submatrix, next_query_index, next_buffer_index, direction, single_expanded_match_tree))

        # Skip a single token in the buffer for single and combined query matches
        if submatrix.is_valid_index(next_buffer_skip_index):
            single_skipped_expanded_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, [next_query_index], [next_buffer_skip_index], direction)
            expanded_match_trees.append(single_skipped_expanded_match_tree)
            expanded_match_trees.extend(self.determine_combined_query_matches(match_tree, match_calculation, submatrix, next_query_index, next_buffer_skip_index, direction, single_skipped_expanded_match_tree))

            # Combine buffer with single tokens
            next_buffer_second_skip_index = match_tree.get_next_buffer_index(submatrix, direction * 3)
            if submatrix.is_valid_index(next_buffer_second_skip_index):
                expanded_match_trees.extend(self.determine_combined_buffer_matches(match_tree, match_calculation, submatrix, next_query_index, next_buffer_skip_index, direction, single_skipped_expanded_match_tree))
        
        return expanded_match_trees
    
    def determine_combined_query_matches(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, next_query_index: int, next_buffer_index: int, direction: int, comparison_match_tree: VirtualBufferMatch) -> List[VirtualBufferMatch]:
        combined_match_trees = []
        next_query_skip_index = next_query_index + direction
        if match_tree.is_valid_index(match_calculation, submatrix, next_query_skip_index):
            combined_query_indices = [next_query_index]
            if direction < 0:
                combined_query_indices.insert(0, next_query_skip_index)
            else:
                combined_query_indices.append(next_query_skip_index)

            # Add the combined tokens, but only if the score increases
            # Compared to the current match tree, and the match tree that would be 
            combined_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, combined_query_indices, [next_buffer_index], direction)
            if sum(combined_match_tree.scores) == sum(match_tree.scores) or \
                sum(combined_match_tree.scores) < sum(comparison_match_tree.scores):
                return combined_match_trees
            combined_match_trees.append(combined_match_tree)

            # Combine three if possible
            next_query_second_skip_index = next_query_index + (direction * 2)
            if match_tree.is_valid_index(match_calculation, submatrix, next_query_second_skip_index):
                combined_query_indices = [next_query_index]
                if direction < 0:
                    combined_query_indices.insert(0, next_query_skip_index)
                    combined_query_indices.insert(0, next_query_second_skip_index)                    
                else:
                    combined_query_indices.append(next_query_skip_index)
                    combined_query_indices.append(next_query_second_skip_index)

                # Only add if the combined match tree increases the total score
                combined_second_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, combined_query_indices, [next_buffer_index], direction)
                if sum(combined_second_match_tree.scores) > sum(combined_match_tree.scores):
                    combined_match_trees.append(combined_second_match_tree)
        return combined_match_trees
    
    def determine_combined_buffer_matches(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, next_query_index: int, next_buffer_index: int, direction: int, comparison_match_tree: VirtualBufferMatch) -> List[VirtualBufferMatch]:
        combined_buffer_match_trees = []
        next_buffer_skip_index = next_buffer_index + direction
        if submatrix.is_valid_index(next_buffer_skip_index):
            combined_buffer_indices = [next_buffer_index]
            if direction < 0:
                combined_buffer_indices.insert(0, next_buffer_skip_index)
            else:
                combined_buffer_indices.append(next_buffer_skip_index)
            
            # Add the combined tokens, but only if the score increases
            combined_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, [next_query_index], combined_buffer_indices, direction)
            if sum(combined_match_tree.scores) == sum(match_tree.scores) or \
                sum(combined_match_tree.scores) < sum(comparison_match_tree.scores):
                return combined_buffer_match_trees
            combined_buffer_match_trees.append(combined_match_tree)

            # Combine three if possible
            next_buffer_second_skip_index = next_buffer_index + (direction * 2)
            if submatrix.is_valid_index(next_buffer_second_skip_index):
                combined_buffer_indices = [next_buffer_index]
                if direction < 0:
                    combined_buffer_indices.insert(0, next_buffer_skip_index)
                    combined_buffer_indices.insert(0, next_buffer_second_skip_index)
                else:
                    combined_buffer_indices.append(next_buffer_skip_index)
                    combined_buffer_indices.append(next_buffer_second_skip_index)

                # Only add if the combined match tree increases the total score
                combined_second_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, [next_query_index], combined_buffer_indices, direction)
                if sum(combined_second_match_tree.scores) > sum(combined_match_tree.scores):
                    combined_buffer_match_trees.append(combined_second_match_tree)

        return combined_buffer_match_trees

    def add_tokens_to_match_tree(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, query_indices: List[int], buffer_indices: List[int], direction: int = 1) -> VirtualBufferMatch:
        expanded_tree = match_tree.clone()

        query_words = [match_calculation.words[query_index] for query_index in query_indices]
        buffer_words = [submatrix.tokens[buffer_index].phrase for buffer_index in buffer_indices]
        weight = sum([match_calculation.weights[query_index] for query_index in query_indices])
        score = self.get_memoized_similarity_score("".join(query_words), "".join(buffer_words))
        skipped_scores = []
        skipped_words = []

        if direction < 0:
            # Add skipped words as well
            last_buffer_index = buffer_indices[-1] + 1
            last_found_index = expanded_tree.buffer_indices[0][0]
            for skipped_index in range(last_buffer_index, last_found_index):
                skipped_words.insert(0, submatrix.tokens[skipped_index].phrase)

            expanded_tree.query_indices.insert(0, query_indices)
            expanded_tree.buffer_indices.insert(0, buffer_indices)
            query_words.extend(expanded_tree.query)
            expanded_tree.query = query_words
            buffer_words.extend(skipped_words)
            buffer_words.extend(expanded_tree.buffer)
            expanded_tree.buffer = buffer_words

            skipped_scores = [0.0 for _ in skipped_words]
            for skipped_score in skipped_scores:
                expanded_tree.scores.insert(0, skipped_score)

            expanded_tree.scores.insert(0, score)
        else:
            # Add skipped words as well
            last_buffer_index = buffer_indices[0]
            last_found_index = expanded_tree.buffer_indices[-1][-1]
            for skipped_index in range(last_found_index + 1, last_buffer_index):
                skipped_words.append(submatrix.tokens[skipped_index].phrase)

            expanded_tree.query_indices.append(query_indices)
            expanded_tree.buffer_indices.append(buffer_indices)
            expanded_tree.query.extend(query_words)

            skipped_scores = [0.0 for _ in skipped_words]

            for skipped_score in skipped_scores:
                expanded_tree.scores.append(skipped_score)

            skipped_words.extend(buffer_words)
            expanded_tree.buffer.extend(skipped_words)

            expanded_tree.scores.append(score)

        expanded_tree.reduce_potential(match_calculation.max_score, score, weight)
        return expanded_tree

    def compare_match_trees_by_distance_and_score(self, a: VirtualBufferMatch, b: VirtualBufferMatch) -> int:
        sort_by_score = self.compare_match_trees_by_score(a, b)
        a_overlap_padding = min(1, max(0, round(len(a.buffer_indices) / 3)))
        a_start = a.buffer_indices[0][0] - a_overlap_padding
        a_end = a.buffer_indices[-1][-1] + a_overlap_padding

        b_overlap_padding = min(1, max(0, round(len(b.buffer_indices) / 3)))
        b_start = b.buffer_indices[0][0] - b_overlap_padding
        b_end = b.buffer_indices[-1][-1] + b_overlap_padding

        # Overlap detected, check score instead
        if a_start <= b_end and b_start <= a_end:
            return sort_by_score
        elif a.distance < b.distance:
            return 1
        elif a.distance > b.distance:
            return -1
        else:
            return sort_by_score

    def compare_match_trees_by_score(self, a: VirtualBufferMatch, b: VirtualBufferMatch) -> int:
        # Favour the matches without dropped matches over ones with dropped matches
        a_missing_difference = len(a.query_indices) - len(a.buffer_indices)
        b_missing_difference = len(b.query_indices) - len(b.buffer_indices)
        if a_missing_difference == 0 and b_missing_difference != 0:
            return 1
        elif a_missing_difference != 0 and b_missing_difference == 0:
            return -1

        # Favour matches with a higher score than ones with a lower score
        if a.score_potential > b.score_potential:
            return 1
        elif a.score_potential < b.score_potential:
            return -1

        # Favour matches with the least amount of skips priority over matches with more skips
        a_skip_difference = len(a.scores) - len(a.query_indices)
        b_skip_difference = len(b.scores) - len(b.query_indices)
        if a_skip_difference < b_skip_difference:
            return 1
        elif a_skip_difference > b_skip_difference:
            return -1
        else:
            return 0

    def find_potential_submatrices_for_words(self, matrix: VirtualBufferMatchMatrix, match_calculation: VirtualBufferMatchCalculation, word_indices: List[int], max_submatrix_size: int) -> List[VirtualBufferMatchMatrix]:
        submatrices = []
        relative_left_index = -(word_indices[0] + ( max_submatrix_size - match_calculation.length ) / 2)
        relative_right_index = relative_left_index + max_submatrix_size

        # Only search within the viable range ( no cut off matches at the start and end of the matrix )
        # Due to multiple different fuzzy matches being possible, it isn't possible to do token skipping
        # Like in the Boyer–Moore string-search algorithm 
        for matrix_index in range(word_indices[0], (len(matrix.tokens) - 1) - (match_calculation.length - 1 - word_indices[0])):
            matrix_token = matrix.tokens[matrix_index]
            threshold = match_calculation.match_threshold * sum([match_calculation.weights[word_index] for word_index in word_indices])

            # TODO DYNAMIC SCORE CALCULATION BASED ON CORRECTION VS SELECTION?
            score = self.get_memoized_similarity_score(matrix_token.phrase, "".join([match_calculation.words[word_index] for word_index in word_indices]))

            has_starting_match = score >= threshold
            if has_starting_match:
                starting_index = max(0, round(matrix_index + relative_left_index))
                ending_index = min(len(matrix.tokens), round(matrix_index + relative_right_index))
                submatrix = matrix.get_submatrix(starting_index, ending_index)
                if (len(submatrix.tokens) > 0):
                    submatrices.append(submatrix)

        return submatrices

    def simplify_submatrices(self, submatrices: List[VirtualBufferMatchMatrix]) -> List[VirtualBufferMatchMatrix]:
        # Sort by index so it is easier to merge by index later
        submatrices.sort(key=lambda x: x.index)

        merged_matrices = []
        current_submatrix = None
        for submatrix in submatrices:
            if current_submatrix is not None:

                # Merge and continue on overlap
                if self.matrices_overlap(current_submatrix, submatrix):
                    current_submatrix = self.merge_matrices(current_submatrix, submatrix)
                    continue

                # Append and set the current submatrix
                else:
                    merged_matrices.append(current_submatrix)
            current_submatrix = submatrix

        if current_submatrix is not None:
            merged_matrices.append(current_submatrix)
        return submatrices
    
    def can_merge_matrices(self, a: VirtualBufferMatchMatrix, b: VirtualBufferMatchMatrix) -> bool:
        return a.index <= b.end_index and b.index <= a.end_index
    
    def merge_matrices(self, a: VirtualBufferMatchMatrix, b: VirtualBufferMatchMatrix) -> VirtualBufferMatchMatrix:
        # Complete overlap just returns the overlapping matrix
        if (a.index <= b.index and a.end_index >= b.end_index):
            return a
        elif (b.index <= a.index and b.end_index >= a.end_index):
            return b

        starting_matrix = a if a.index < b.index else b
        ending_matrix = b if a.index < b.index else a

        combined_tokens = []
        combined_tokens.extend(starting_matrix.tokens)
        if ending_matrix.end_index > starting_matrix.end_index:
            combined_tokens.extend(ending_matrix.tokens[-(ending_matrix.end_index - starting_matrix.end_index):])

        return VirtualBufferMatchMatrix(starting_matrix.index, combined_tokens)

    def find_self_repair_match(self, virtual_buffer, phrases: List[str]) -> VirtualBufferTokenMatch:
        # Do not allow punctuation to activate self repair
        phrases = [phrase for phrase in phrases if not phrase.replace(" ", "").endswith((",", ".", "!", "?"))]

        # We don't do any self repair checking with selected text, only in free-flow text
        if not virtual_buffer.is_selecting():
            current_index = virtual_buffer.determine_token_index()

            if current_index[0] != -1 and current_index[1] != -1:
                earliest_index_for_look_behind = max(0, current_index[0] - len(phrases))
                index_offset = 1 if current_index[0] - len(phrases) > 0 else 0
                tokens_behind = virtual_buffer.tokens[earliest_index_for_look_behind:current_index[0] + 1]

                # We consider punctuations as statements that the user cannot match with
                tokens_from_last_punctuation = []
                for token in tokens_behind:
                    if not token.text.replace("\n", ".").replace(" ", "").endswith((",", ".", "!", "?")):
                        tokens_from_last_punctuation.append(token)
                    else:
                        tokens_from_last_punctuation = []

                if len(tokens_from_last_punctuation) > 0:
                    matches = self.find_matches_by_phrases(tokens_from_last_punctuation, phrases, CORRECTION_THRESHOLD, 'most_direct_matches')
                    starting_offset = index_offset + max(0, current_index[0] - len(tokens_from_last_punctuation))

                    # Get the match with the most matches, closest to the end
                    # Make sure we adhere to 'reasonable' self repair of about 5 words back max
                    for best_match in matches:

                        # Make sure we normalize the index to our best knowledge
                        best_match.starts += starting_offset
                        best_match.indices = [index + starting_offset for index in best_match.indices]

                        avg_score = best_match.score / (len(best_match.indices) + best_match.distance)
                        standard_deviation = math.sqrt(sum(pow(score - avg_score, 2) for score in best_match.scores) / (len(best_match.indices) + best_match.distance))

                        # When the final index does not align with the current index, it won't be a self repair replacement
                        if best_match.indices[-1] < current_index[0]:
                            continue
                            
                        # When we have unmatched new words coming before the match, it won't be a self repair replacement
                        elif best_match.starts - index_offset - best_match.indices[-1] > 0:
                            continue

                        # If the average score minus half the std is smaller than one, we do not have a match
                        elif avg_score - ( standard_deviation / 2 ) < 1:
                            continue

                        else:
                            return best_match
        
        return None
    
    def find_best_match_by_phrases(self, virtual_buffer, phrases: List[str], match_threshold: float = SELECTION_THRESHOLD, next_occurrence: bool = True, selecting: bool = False, for_correction: bool = False, verbose: bool = False) -> List[VirtualBufferToken]:
        matches = self.find_matches_by_phrases( virtual_buffer.tokens, phrases, match_threshold, verbose=verbose)
        if verbose:
            print( "MATCHES!", matches, match_threshold )

        if len(matches) > 0:

            # For selection only, we want the best possible match score wise
            # Before getting the closest distance wise
            if not for_correction:
                max_score = max([match.syllable_score - match.distance for match in matches])
                matches = [match for match in matches if match.syllable_score - match.distance >= max_score]

            best_match = matches[0]

            if len(matches) > 1:
                current_index = virtual_buffer.determine_token_index()
                if current_index[0] != -1:
                    # Get the closest item to the caret in the case of multiple matches
                    distance = 1000000
                    for match in matches:
                        end_index = max(match.indices)
                        start_index = min(match.indices)
                        
                        distance_from_found_end = abs(end_index - current_index[0])
                        distance_from_found_start = abs(start_index - current_index[0])
                        
                        if distance_from_found_end < distance:
                            best_match = match
                            distance = distance_from_found_end
                        
                        elif distance_from_found_start < distance:
                            best_match = match
                            distance = distance_from_found_start
            
            best_match_tokens = []
            for index in best_match.indices:
                best_match_tokens.append(virtual_buffer.tokens[index])

            return best_match_tokens
        else:
            return None

    def find_matches_by_phrases(self, tokens: List[VirtualBufferToken], phrases: List[str], match_threshold: float = 2.5, strategy='highest_score', verbose=False) -> List[VirtualBufferTokenMatch]:
        matrix = self.generate_similarity_matrix(tokens, phrases)
        #verbose = False

        # Scale match threshold based on amount of phrases and syllable count
        phrase_syllable_counts = [self.phonetic_search.syllable_count(phrase) for phrase in phrases]
        phrase_syllable_count = sum(phrase_syllable_counts)
        phrase_weights = [count / phrase_syllable_count for count in phrase_syllable_counts]
        match_threshold = match_threshold if len(phrases) > 2 else match_threshold + (0.8 / len(phrases))
        #match_threshold = (match_threshold * (len(phrases) / phrase_syllable_count))
        if verbose:
            print("SYLLABLE COUNT FOR " + " ".join(phrases), phrase_syllable_count, match_threshold)

        needed_average_score = match_threshold * len(phrases)
        used_indices = {}

        matches = []
        for phrase_index, phrase in enumerate(phrases):
            if not str(phrase_index) in used_indices:
                used_indices[str(phrase_index)] = [0 for _ in range(0, len(matrix[phrase]))]
            skip_count = 0

            current_match = None
            for index, score in enumerate(matrix[phrase]):
                # Skip indices that we have already checked for this phrase
                if used_indices[str(phrase_index)][index] == 1:
                    skip_count += 1
                    continue

                if score >= match_threshold:
                    syllable_score = self.calculate_syllable_score(score, phrase, tokens[index].text)
                    current_match = VirtualBufferTokenMatch(phrase_index, [index], [[phrase], [tokens[index].text]], score, [score], syllable_score, [syllable_score])

                    # Keep a list of used indexes to know which to skip for future passes
                    used_indices[str(phrase_index)][index] = 1
                    missed_phrase_length = 0

                    current_word_index = index
                    current_phrase_index = phrase_index
                    missing_end_indices = []
                    last_matching_index = -1
                    while(current_phrase_index + 1 < len(phrases)):                        
                        tokens_left = len(phrases) - current_phrase_index - 1
                        current_word_index += 1
                        current_phrase_index += 1 
                        if not str(current_phrase_index) in used_indices:
                            used_indices[str(current_phrase_index)] = [0 for _ in range(0, len(matrix[phrase]))]

                        # Calculate the minimum threshold required to meet the average match threshold in the next sequence
                        if tokens_left > 0:
                            min_threshold_to_meet_average = max(0.2, ((needed_average_score - current_match.score ) / tokens_left) - 1)
                            
                        next_index = self.match_next_in_phrases(matrix, current_word_index, phrases, current_phrase_index, min_threshold_to_meet_average)
                        if next_index[0] != -1:
                            last_matching_index = next_index[0]
                            current_match.comparisons[0].append(phrases[current_phrase_index - missed_phrase_length])
                            current_match.comparisons[1].append(tokens[next_index[0]].phrase)
                            current_match.distance += next_index[0] - current_word_index

                            # Add the score of the missed phrases in between the matches
                            while missed_phrase_length > 0:
                                # Make sure we only count item scores in between words rather than skipped words entirely
                                if next_index[0] - missed_phrase_length > current_match.indices[-1]:
                                    current_match.distance -= 1
                                    current_match.indices.append(next_index[0] - missed_phrase_length)
                                    added_score = matrix[phrases[current_phrase_index - missed_phrase_length]][next_index[0] - missed_phrase_length]
                                    current_match.comparisons[0].append(phrases[current_phrase_index - missed_phrase_length])
                                    current_match.comparisons[1].append(tokens[next_index[0] - missed_phrase_length].phrase)
                                    current_match.score += added_score
                                    current_match.scores.append( added_score )
                                    
                                    syllable_score = self.calculate_syllable_score(added_score, phrases[current_phrase_index - missed_phrase_length], tokens[next_index[0] - missed_phrase_length].phrase)
                                    current_match.syllable_score += syllable_score
                                    current_match.syllable_scores.append( syllable_score)

                                missed_phrase_length -= 1

                            current_match.indices.append(next_index[0])
                            current_match.score += next_index[1]
                            current_match.scores.append( next_index[1] )
                            
                            syllable_score = self.calculate_syllable_score(next_index[1], phrases[current_phrase_index - missed_phrase_length], tokens[next_index[0]].phrase)
                            current_match.syllable_score += syllable_score
                            current_match.syllable_scores.append( syllable_score)

                            current_word_index = next_index[0]

                            # Keep a list of used indexes to know which to skip for future passes
                            used_indices[str(current_phrase_index)][next_index[0]] = 1
                            missed_phrase_length = 0
                            missing_end_indices = []
                        else:
                            missed_phrase_length += 1
                            missing_end_indices.append(current_phrase_index)

                    # Do a simple look back without another search
                    if current_match != None and phrase_index > 0:
                        previous_indices = []
                        previous_score = 0
                        previous_syllable_score = 0
                        current_phrase_index = phrase_index
                        prepend_index = -1
                        for previous_phrase_index in range(0 - phrase_index, 0):
                            if index + previous_phrase_index >= 0:
                                previous_indices.append(index + previous_phrase_index)
                                previous_phrase = phrases[phrase_index + previous_phrase_index]
                                new_previous_score = matrix[previous_phrase][index + previous_phrase_index]
                                previous_score += new_previous_score
                                current_match.comparisons[0].insert(prepend_index, previous_phrase)
                                current_match.comparisons[1].insert(prepend_index, tokens[index + previous_phrase_index].phrase)
                                current_match.scores.insert(prepend_index, new_previous_score)

                                syllable_score = self.calculate_syllable_score(new_previous_score, previous_phrase, tokens[index + previous_phrase_index].phrase)
                                previous_syllable_score += syllable_score
                                current_match.syllable_scores.insert(prepend_index, new_previous_score)                                
                            prepend_index += 1
                        
                        previous_indices.extend(current_match.indices)
                        current_match.indices = previous_indices
                        current_match.score += previous_score
                        current_match.syllable_score += previous_syllable_score

                    # Add score of missing matches at the end
                    if current_match != None and last_matching_index > -1 and len(missing_end_indices) > 0:
                        next_score = 0
                        next_syllable_score = 0
                        next_indices = []
                        for next_index in missing_end_indices:
                            last_matching_index += 1
                            if last_matching_index < len(tokens):
                                next_phrase = phrases[next_index]
                                next_indices.append(last_matching_index)
                                new_next_score = matrix[next_phrase][last_matching_index]
                                next_score += new_next_score
                                current_match.scores.append(new_next_score)
                                current_match.comparisons[0].append(next_phrase)
                                current_match.comparisons[1].append(tokens[last_matching_index].phrase)

                                syllable_score = self.calculate_syllable_score(new_next_score, next_phrase, tokens[last_matching_index].phrase)
                                next_syllable_score += syllable_score
                                current_match.syllable_scores.append(syllable_score)                                

                        current_match.indices.extend(next_indices)
                        current_match.score += next_score
                        current_match.syllable_score += next_syllable_score

                # Syllable score is a weighted sum
                syllable_score = 0
                if current_match is not None:
                    for index, weight in enumerate(phrase_weights):
                        syllable_score += 0 if len(current_match.syllable_scores) <= index else current_match.syllable_scores[index] * weight
                    current_match.syllable_score = syllable_score

                # Prune out matches below the average score threshold
                # And with a distance between words that is larger than forgetting a word in between every word
                if current_match != None and (current_match.distance <= len(phrases) - 1) and strategy == 'most_direct_matches':
                    if verbose:
                        print("CAN ADD, BECAUSE DISTANCE ", current_match.distance , "<=", len(phrases) - 1)
                    matches.append(current_match)
                elif current_match != None and (current_match.syllable_score / (len(phrases) + current_match.distance / 2)) >= match_threshold / len(phrases) and (current_match.distance <= len(phrases) - 1):
                    if verbose:
                        print( "CAN ADD, BECAUSE score ", (current_match.syllable_score / (len(phrases) + current_match.distance / 2)), " >= ", match_threshold, " and distance ", current_match.distance, "<=", len(phrases) - 1 )
                    matches.append(current_match)
                elif current_match != None and verbose:
                    print( "No match, score ", (current_match.syllable_score / (len(phrases) + current_match.distance / 2)), " >= ", match_threshold, " and distance ", current_match.distance, "<=", len(phrases) - 1, current_match )
                
                current_match = None

        if strategy == 'highest_score':
            matches = sorted(matches, key=lambda match: match.syllable_score - (match.distance / len(match.indices)), reverse=True)

        # Place the highest direct matches on top
        elif strategy == 'most_direct_matches':
            matches = sorted(matches, key=lambda match: len(list(filter(lambda x: x >= 0.8, match.syllable_scores))) - (match.distance / len(match.indices)), reverse=True)
        return matches
    
    def match_next_in_phrases(self, matrix, matrix_index: int, phrases: List[str], phrase_index: int, match_threshold: float):
        phrase = phrases[phrase_index]

        for i in range(matrix_index, len(matrix[phrase])):
            score = matrix[phrase][i]
            if score >= match_threshold:
                return (i, score)
        
        return (-1, -1)

    def find_single_match_by_phrase(self, virtual_buffer, phrase: str, char_position: int = -1, next_occurrence: bool = True, selecting: bool = False) -> VirtualBufferToken:
        exact_matching_tokens: List[(int, VirtualBufferToken)] = []
        fuzzy_matching_tokens: List[(int, VirtualBufferToken, float)] = []

        for index, token in enumerate(virtual_buffer.tokens):
            score = self.phonetic_search.phonetic_similarity_score(phrase, token.phrase)
            if score >= HOMOPHONE_MATCH:
                exact_matching_tokens.append((index, token))
            elif score > SELECTION_THRESHOLD:
                fuzzy_matching_tokens.append((index, token, score))

        # If we have no valid matches or valid carets, we cannot find the phrase
        caret_index = virtual_buffer.caret_tracker.get_caret_index()
        if (len(exact_matching_tokens) + len(fuzzy_matching_tokens) == 0) or caret_index[0] < 0:
            return None
        
        # Get the first exact match
        if len(exact_matching_tokens) == 1:
            return exact_matching_tokens[0][1]
        
        # Get a fuzzy match if it is the only match
        elif len(exact_matching_tokens) == 0 and len(fuzzy_matching_tokens) == 1:
            return fuzzy_matching_tokens[0][1]
        else:
            token_index = virtual_buffer.determine_token_index()
            current_token = virtual_buffer.tokens[token_index[0]]
            text_length = len(current_token.text.replace("\n", ""))
            current_phrase_similar = self.phonetic_search.phonetic_similarity_score(phrase, current_token.phrase) >= 1

            if token_index[1] == text_length and not current_phrase_similar:
                # Move to the next token if that token matches our phrase
                next_token_phrase = "" if token_index[0] + 1 >= len(virtual_buffer.tokens) else virtual_buffer.tokens[token_index[0] + 1].phrase 
                if self.phonetic_search.phonetic_similarity_score(phrase, next_token_phrase) >= 1:
                    current_token = virtual_buffer.tokens[token_index[0] + 1]
                    token_index = (token_index[0] + 1, 0)
                    current_phrase_similar = True

            # If the current token is the token we are looking for, make sure to check if we should cycle through it
            if current_phrase_similar:    
                # If the caret is in the middle of the token we are trying to find, make sure we don't look further                
                if token_index[1] > 0 and token_index[1] < text_length:
                    return current_token
                
                # If the caret is on the opposite end of the token we are trying to find, make sure we don't look further
                # Unless we are actively selecting new ocurrences
                elif not (selecting and next_occurrence) and ( (token_index[1] == 0 and char_position == -1) or (token_index[1] == text_length and char_position >= 0) ):
                    return current_token
                
            # Loop through the occurrences one by one, starting back at the end if we have reached the first token
            if next_occurrence:
                matched_token = None
                for token in exact_matching_tokens:
                    if token[0] < token_index[0]:
                        matched_token = token[1]
                    elif (virtual_buffer.last_action_type == "insert" or virtual_buffer.last_action_type == "remove") and token[0] == token_index[0]:
                        matched_token = token[1]
                
                if matched_token is None:
                    matched_token = exact_matching_tokens[-1][1]

            # Just get the nearest matching token to the caret as this is most likely the one we were after
            # Not all cases have been properly tested for this
            else:
                distance_to_token = 1000000
                current_token = virtual_buffer.tokens[token_index[0]]

                matched_token = None
                for token_index, token in exact_matching_tokens:
                    line_distance = abs(token.line_index - current_token.line_index) * 10000
                    distance_from_token_end = abs(token.index_from_line_end) + line_distance
                    distance_from_token_start = abs(token.index_from_line_end + len(token.text.replace("\n", ""))) + line_distance
                    
                    if abs(distance_from_token_end - current_token.index_from_line_end) < distance_to_token:
                        matched_token = token
                        distance_to_token = abs(distance_from_token_end - current_token.index_from_line_end)
                    
                    elif abs(distance_from_token_start - current_token.index_from_line_end) < distance_to_token:
                        matched_token = token
                        distance_to_token = abs(distance_from_token_start - current_token.index_from_line_end)

                if matched_token is None:
                    matched_token = exact_matching_tokens[-1]

            return matched_token
        
    def get_memoized_similarity_score(self, word_a: str, word_b: str) -> float:
        # Quick memoized look up
        if word_a in self.similarity_matrix and word_b in self.similarity_matrix[word_a]:
            return self.similarity_matrix[word_a][word_b]
        elif word_b in self.similarity_matrix and word_a in self.similarity_matrix[word_b]:
            return self.similarity_matrix[word_b][word_a]
        
        # Generate single cache entry using calculated similarity score
        if word_a not in self.similarity_matrix:
            self.similarity_matrix[word_a] = {}

        self.similarity_matrix[word_a][word_b] = self.phonetic_search.phonetic_similarity_score(word_a, word_b)
        return self.similarity_matrix[word_a][word_b]

    def generate_similarity_matrix(self, tokens: List[VirtualBufferToken], phrases: List[str]) -> Dict[str, List[float]]:
        matrix = {}
        for phrase in phrases:
            if phrase in matrix:
                continue
            matrix[phrase] = []
            for token in tokens:
                similarity_key = phrase + "." + token.phrase
                if similarity_key not in self.similarity_matrix:

                    # Keep a list of known results to make it faster to generate the matrix in the future
                    self.similarity_matrix[similarity_key] = self.phonetic_search.phonetic_similarity_score(token.phrase, phrase)
                
                matrix[phrase].append(self.similarity_matrix[similarity_key])
        return matrix