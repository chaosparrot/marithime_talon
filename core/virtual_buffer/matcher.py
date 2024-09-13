from ..phonetics.phonetics import PhoneticSearch
from ..phonetics.detection import EXACT_MATCH, HOMOPHONE_MATCH, PHONETIC_MATCH
from .typing import VirtualBufferToken, VirtualBufferTokenMatch, VirtualBufferMatchCalculation, VirtualBufferMatchMatrix, VirtualBufferMatch, VirtualBufferTokenContext, VirtualBufferMatchVisitCache, SELECTION_THRESHOLD, CORRECTION_THRESHOLD
import re
from typing import List, Dict, Tuple
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
        self.checked_comparisons = {}

    # Calculate the best matching score
    # Based on the similarity score times the amount of syllables
    # After all, a matching long word gives more confidence than a short word
    def calculate_syllable_score(self, score, query: str, match: str) -> float:
        return self.phonetic_search.calculate_syllable_score(score, normalize_text(query).replace(" ", ''), match)

    def is_phrase_selected(self, virtual_buffer, phrase: str) -> bool:
        if virtual_buffer.is_selecting():
            selection = virtual_buffer.caret_tracker.get_selection_text()
            return self.phonetic_search.phonetic_similarity_score(normalize_text(selection).replace(" ", ''), phrase) >= PHONETIC_MATCH
        return False

    def has_matching_phrase(self, virtual_buffer, phrase: str) -> bool:
        score = 0
        for token in virtual_buffer.tokens:
            score = self.phonetic_search.phonetic_similarity_score(phrase, token.phrase)
            if score >= SELECTION_THRESHOLD:
                return True

        return False
    
    def get_threshold_for_selection(self, phrases: List[str], match_threshold: float = SELECTION_THRESHOLD) -> float:
        # Taper the threshold according to the amount of queried words
        # So we are more stringent with single words than double words
        # After 3 it is settled
        match_threshold += 0.1 * max(0, (3 - len(phrases)))
        return min(0.83, match_threshold)

    def find_top_three_matches_in_matrix(self, virtual_buffer, phrases: List[str], match_threshold: float = SELECTION_THRESHOLD, selecting: bool = False, for_correction: bool = False, for_selfrepair: bool = False, verbose: bool = False):
        # Don't change the match threshold for corrections
        if not for_correction:
            match_threshold = self.get_threshold_for_selection(phrases, match_threshold)

        leftmost_token_index = virtual_buffer.determine_leftmost_token_index()[0]
        rightmost_token_index = virtual_buffer.determine_rightmost_token_index()[0]
        starting_index = 0
        ending_index = len(virtual_buffer.tokens)
        if for_selfrepair:
            starting_index = max(0, rightmost_token_index + 1 - (len(phrases) * 2))
            ending_index = rightmost_token_index + 1
        matrix = VirtualBufferMatchMatrix(starting_index, virtual_buffer.tokens[starting_index:ending_index])
        match_calculation = self.generate_match_calculation(phrases, match_threshold, purpose=("correction" if for_correction else "selection"))
        match_calculation.cache.index_matrix(matrix)
        windowed_submatrices = matrix.get_windowed_submatrices(leftmost_token_index, match_calculation)

        if verbose:
            print( "- Using match threshold: " + str(match_calculation.match_threshold))
            print( "- Splitting into " + str(len(windowed_submatrices)) + " windowed submatrices for rapid searching")

        found_match_combinations = []
        highest_score_achieved = False
        for windowed_submatrix in windowed_submatrices:
            submatrices, match_calculation = self.find_potential_submatrices(match_calculation, windowed_submatrix, verbose=verbose)
            split_submatrices = self.split_submatrices_by_cursor_position(submatrices, leftmost_token_index, rightmost_token_index)
            matches = []

            highest_found_match = match_threshold
            for index, matrix_group in enumerate(split_submatrices):
                match_calculation.match_threshold = match_threshold
                matrix_group_matches = []
                highest_match = 0
                for submatrix in matrix_group:
                    submatrix_matches, match_calculation = self.find_matches_in_matrix(match_calculation, submatrix, highest_match, verbose=verbose)
                    if len(submatrix_matches) > 0:
                        highest_match = max(highest_match, submatrix_matches[0].score_potential)
                        #if verbose:
                        #    print( "- Updating threshold to: " + str(highest_match))
                        matrix_group_matches.extend(submatrix_matches)
                        if not for_correction:
                            highest_score_achieved = highest_match == match_calculation.max_score

                    # Do not seek any further if we have reached the highest possible score
                    # Since no improvement is possible
                    # Also do not seek further for correction cases as we never look beyond matches closest to the cursor anyway
                    if highest_score_achieved or (for_correction and len(submatrix_matches) > 0):
                        break
                
                if verbose:
                    print( "- Found matches for split " + str(index), matrix_group_matches )

                # Calculate the distance from the cursor
                for matrix_group_match in matrix_group_matches:
                    matrix_group_match.calculate_distance(leftmost_token_index, rightmost_token_index)

                if len(matrix_group_matches) > 0:
                    if selecting:
                        matrix_group_matches.sort(key = cmp_to_key(self.compare_match_trees_for_selection), reverse=True)
                    if for_correction:
                        matrix_group_matches.sort(key = cmp_to_key(self.compare_match_trees_for_correction), reverse=True)
                    matches.append(matrix_group_matches[0])
                    highest_found_match = max(highest_found_match, highest_match)

            if highest_score_achieved:
                break
            match_calculation.match_threshold = highest_found_match

            # Make sure we do not match on the exact matches again as we are sure we are closest to the cursor
            # For the currently found matches
            for match in matches:
                match_calculation.cache.skip_word_sequence(match.buffer)

            # Add indices to skip because they do not match anything in the total matrix
            if verbose and windowed_submatrix.index == 0:
                print( "BUFFER INDEX SCORES", match_calculation.cache.buffer_index_scores)
            non_match_threshold = 0.1 if match_calculation.purpose == "correction" else 0.29
            for windowed_index in range(windowed_submatrix.index, windowed_submatrix.end_index):
                if not match_calculation.cache.should_skip_index(windowed_index):
                    score_for_index = match_calculation.cache.get_highest_score_for_buffer_index(windowed_index)
                    if score_for_index >= 0 and score_for_index < non_match_threshold:
                        if verbose:
                            print("SKIP SPECIFIC WORD!", score_for_index, windowed_index)
                        match_calculation.cache.skip_word_sequence([matrix.tokens[windowed_index - matrix.index].phrase])
                    elif verbose:
                        print("DO NOT SKIP WORD", score_for_index, windowed_index)
                elif verbose:
                    print("SKIP INDEX", windowed_index)
        

        return matches

    # Generate a match calculation based on the words to search for weighted by syllable count
    def generate_match_calculation(self, query_words: List[str], threshold: float = SELECTION_THRESHOLD, max_score_per_word: float = EXACT_MATCH, purpose: str = "selection") -> VirtualBufferMatchCalculation:
        syllables_per_word = [self.phonetic_search.syllable_count(word) for word in query_words]
        total_syllables = max(sum(syllables_per_word), 1)
        weights = [syllable_count / total_syllables for syllable_count in syllables_per_word]

        # TODO - Perhaps give more weight to starting and ending words
        # If we are dealing with a heavy ^ shaped weights for correction, mellow out the weights
        if purpose == "correction" and len(query_words) == 3 and weights[1] > weights[0] and weights[1] > weights[2]:
            rescaled_syllable_count = syllables_per_word[1] - 1
            rescaled_syllables = [min(rescaled_syllable_count, syllable_count) for syllable_count in syllables_per_word]
            total_syllables = sum(rescaled_syllables)
            weights = [syllable_count / total_syllables for syllable_count in rescaled_syllables]
        
        match_calculation = VirtualBufferMatchCalculation(query_words, weights, syllables_per_word, threshold, max_score_per_word, purpose)
        match_calculation.cache = VirtualBufferMatchVisitCache()
        return match_calculation
    
    # Generate a list of (sorted) potential submatrices to look through
    def find_potential_submatrices(self, match_calculation: VirtualBufferMatchCalculation, matrix: VirtualBufferMatchMatrix, verbose: bool = False):
        match_calculation.starting_branches = []
        word_indices = match_calculation.get_possible_branches()
        max_submatrix_size = len(match_calculation.words) * 3
        sub_matrices = []

        # Create a dictionary of indices to skip over for exact matches
        # For performance gains for large fuzzy searches
        if match_calculation.cache.should_skip_submatrix(matrix, match_calculation):
            if verbose:
                print( "    - SKIPPING ENTIRE MATRIX BECAUSE THE MAX SEQUENCE ISN'T ENOUGH FOR A MATCH")
            return [], match_calculation
        elif verbose:
            print( "    - CAN USE MATRIX BECAUSE THERE IS A BIG ENOUGH MAX SEQUENCE")

        if verbose:
            print("BEFORE COMPARISONS", sum(self.checked_comparisons.values()))
        for word_index in word_indices:
            potential_submatrices, match_calculation = self.find_potential_submatrices_for_words(matrix, match_calculation, word_index, max_submatrix_size, verbose=verbose)
            sub_matrices.extend(potential_submatrices)
        if verbose:
            duplicates = sum([value - 1 for value in self.checked_comparisons.values() if value > 1])
            print("AFTER COMPARISONS", sum(self.checked_comparisons.values()), duplicates)

        if verbose:
            print( "    - FOUND ROOTS FOR THESE MATRICES", len(sub_matrices))
            print( match_calculation.starting_branches )

        sub_matrices = self.simplify_submatrices(sub_matrices)
        if verbose:
            print("    - Simplified to these matrices", len(sub_matrices))

        return sub_matrices, match_calculation

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
    
    def find_matches_in_matrix(self, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, highest_match: float = 0, early_stopping: bool = True, verbose: bool = False) -> Tuple[List[VirtualBufferMatch], VirtualBufferMatchCalculation]:
        branches = match_calculation.get_starting_branches(submatrix)
        query = match_calculation.words
        buffer = [token.phrase for token in submatrix.tokens]

        starting_match = VirtualBufferMatch([], [], [], [], [], match_calculation.max_score, 0)

        # Initial branches
        if verbose:
            print(" - Starting branches", branches)
        match_branches = []
        for branch in branches:
            combined_weight = sum([match_calculation.weights[index] for index in branch.query_indices])
            if branch.score_potential >= match_calculation.match_threshold:
                match_branch = starting_match.clone()
                match_branch.query_indices.append(branch.query_indices)
                match_branch.query.extend([query[index] for index in branch.query_indices])
                normalized_buffer_indices = [index - submatrix.index for index in branch.buffer_indices]
                match_branch.buffer_indices.append(normalized_buffer_indices)
                match_branch.buffer.extend([buffer[buffer_index] for buffer_index in normalized_buffer_indices])
                match_branch.scores.append(branch.score)
                match_branch.reduce_potential(match_calculation.max_score, branch.score, combined_weight) 
                match_branches.append(match_branch)
            elif verbose:
                print( "Branch rejected because ", branch.score_potential, "<", match_calculation.match_threshold, branch )

            #word_index = branch.query_indices[0]
            #end_word_index = branch.query_indices[-1]
            #max_buffer_search = len(buffer) - (len(query))
            #if verbose:
            #    print(" - Attempting", query_match_branch.query, combined_weight)

            #for buffer_index in range(word_index, end_word_index + max_buffer_search + 1):
            #    buffer_word = buffer[buffer_index]
            #    score = self.get_memoized_similarity_score("".join(query_match_branch.query), buffer_word)
            #    if verbose:
            #        print( "     - Score with " + buffer_word + ": " + str(score))

                # Only add a match branch for a combined query search if the combined search scores higher than individual scores
            #    if is_multiple_query_match:
            #        individual_scores = [self.get_memoized_similarity_score(word, buffer_word) for word in match_calculation.words]
            #        if max(individual_scores) > score:
            #            continue

                # Attempt multi-buffer matches if they score higher than the single match buffer case
            #    highest_match_score = score
            #    buffer_indices_to_use = [buffer_index]
            #    if not is_multiple_query_match:
            #        next_word = ""

                    # Combine two words
            #        if buffer_index + 1 <= max_buffer_search and buffer_index + 1 < len(buffer):
            #            next_word = buffer[buffer_index + 1]
            #            next_forward_score = self.get_memoized_similarity_score("".join(query_match_branch.query), buffer_word + next_word)
            #            if next_forward_score > highest_match_score:
            #                highest_match_score = next_forward_score
            #                buffer_indices_to_use = [buffer_index, buffer_index + 1]

                    # Combine three words
            #        if buffer_index + 2 <= max_buffer_search and buffer_index + 2 < len(buffer) and len(buffer_indices_to_use) == 2:
            #            second_next_word = buffer[buffer_index + 2]
            #            next_forward_score = self.get_memoized_similarity_score("".join(query_match_branch.query), buffer_word + next_word + second_next_word)
            #            if next_forward_score > highest_match_score:
            #                highest_match_score = next_forward_score
            #                buffer_indices_to_use = [buffer_index, buffer_index + 1, buffer_index + 2]

                    # Combine two words backward
            #        if buffer_index - 1 >= word_index:
            #            previous_word = buffer[buffer_index - 1]
            #            previous_backward_score = self.get_memoized_similarity_score("".join(query_match_branch.query), previous_word + buffer_word)
            #            if previous_backward_score > highest_match_score:
            #                highest_match_score = previous_backward_score
            #                buffer_indices_to_use = [buffer_index - 1, buffer_index]

                    # Combine three words backward
            #        if buffer_index - 2 >= word_index and len(buffer_indices_to_use) == 2:
            #            second_previous_word = buffer[buffer_index - 2]
            #            previous_backward_score = self.get_memoized_similarity_score("".join(query_match_branch.query), second_previous_word + previous_word + buffer_word)
            #            if previous_backward_score > highest_match_score:
            #                highest_match_score = previous_backward_score
            #                buffer_indices_to_use = [buffer_index - 2, buffer_index - 1, buffer_index]

                # Add only a single combination even if multiple options might have a better overall chance
                # Only if the words compare well enough will we continue searching
            #    if highest_match_score >= match_calculation.match_threshold:
            #        match_branch = query_match_branch.clone()
            #        match_branch.buffer_indices.append(buffer_indices_to_use)
            #        match_branch.buffer.extend([buffer[buffer_index] for buffer_index in buffer_indices_to_use])
            #        match_branch.scores.append(highest_match_score)
            #        match_branch.reduce_potential(match_calculation.max_score, score, combined_weight) 
            #        match_branches.append(match_branch)

        # Filter searches that do not match the previous best and sort by the best score first
        searches = []
        if verbose:
            print("Found matched branches", match_branches )
        for match_root in match_branches:
            if verbose:
                print( "Expand root for ", match_root )
            expanded_tree, match_calculation = self.expand_match_tree(match_root, match_calculation, submatrix, verbose=verbose)
            searches.extend(expanded_tree)
        filtered_searches = [search for search in searches if search.score_potential >= highest_match and len(search.query) == len(match_calculation.words)]
        filtered_searches.sort(key = cmp_to_key(self.compare_match_trees_by_score), reverse=True)

        # Use global matrix indices for every match
        for search in filtered_searches:
            search.to_global_index(submatrix)
        return filtered_searches, match_calculation

    def expand_match_tree(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, verbose: bool = False) -> Tuple[List[VirtualBufferMatchMatrix], VirtualBufferMatchCalculation]:
        match_trees = [match_tree]
        expanded_match_trees: List[VirtualBufferMatch] = []

        # First expand backwards if we haven't already walked that path
        if match_tree.can_expand_backward(submatrix):
            can_expand_backward_count = 1
            while can_expand_backward_count != 0:
                expanded_match_trees = []
                for match_tree in match_trees:
                    backward_expanded_match_tree, match_calculation = self.expand_match_tree_backward(match_tree, match_calculation, submatrix, verbose=verbose)
                    expanded_match_trees.extend(backward_expanded_match_tree)
                can_expand_backward_count = sum([expanded_match_tree.can_expand_backward(submatrix) for expanded_match_tree in expanded_match_trees])
                match_trees = list(set(expanded_match_trees))
            
            if verbose:
                print( "---- BACKWARD", match_trees )
        elif verbose:
            print( "---- Match tree cannot expand backward from the start")

        # Then expand forwards if possible
        if match_tree.can_expand_forward(match_calculation, submatrix):
            can_expand_forward_count = 1
            while can_expand_forward_count != 0:
                expanded_match_trees = []
                for match_tree in match_trees:
                    forward_expanded_match_tree, match_calculation = self.expand_match_tree_forward(match_tree, match_calculation, submatrix, verbose=verbose)
                    expanded_match_trees.extend(forward_expanded_match_tree)
                can_expand_forward_count = sum([expanded_match_tree.can_expand_forward(match_calculation, submatrix) for expanded_match_tree in expanded_match_trees])
                match_trees = list(set(expanded_match_trees))
            
            if verbose:
                print( "---- FORWARD", match_trees )
        elif verbose:
            print( "---- Match tree cannot expand forward from the start")

        # Filter out results with multiple consecutive bad results
        low_score_threshold = match_calculation.match_threshold / 2
        single_word_score_threshold = -1 if match_calculation.purpose == "correction" else 0.29
        combined_word_score_threshold = 0.1 if match_calculation.purpose == "correction" else 0.5
        
        if match_calculation.purpose == "correction":
            consecutive_low_score_threshold = 2
        else:
            consecutive_low_score_threshold = 1 if len(match_calculation.words) <= 2 else 2
        filtered_trees = []
        for match_tree in match_trees:
            consecutive_low_scores = 0

            # Cannot start or end with a 0 / skip for selections
            threshold_met = match_calculation.purpose == "correction" or ( match_tree.scores[0] > 0.0 and match_tree.scores[-1] > 0.0 )
            buffer_index = -1
            index_offset = 0
            for index, query_index in enumerate(match_tree.query_indices):
                # Calculate the weighted score
                if buffer_index == -1:
                    buffer_index = 0
                else:
                    buffer_index += 1

                    # Skip found - Add another score index
                    if match_tree.buffer_indices[buffer_index - 1][-1] != match_tree.buffer_indices[buffer_index][0] - 1:
                        index_offset += 1

                score = match_tree.scores[index + index_offset]
                weight = 0
                for inner_index, _ in enumerate(query_index):
                    weight += match_calculation.weights[inner_index]
                
                weighted_low_score_threshold = low_score_threshold * weight / 1.5

                if score * weight <= weighted_low_score_threshold:
                    consecutive_low_scores += 1
                else:
                    consecutive_low_scores = 0

                matches_muliple_words = len(query_index) > 1 or len(match_tree.buffer_indices[buffer_index]) > 1
                single_threshold = combined_word_score_threshold if matches_muliple_words else single_word_score_threshold
                if score > 0.0 and score <= single_threshold:
                    threshold_met = False
                    if verbose:
                        print("SKIPPED BECAUSE SINGLE THRESHOLD NOT MET")

                if consecutive_low_scores >= consecutive_low_score_threshold:
                    threshold_met = False
                    if verbose:
                        print("SKIPPED BECAUSE CONSECUTIVE THRESHOLD NOT MET")
                
                if not threshold_met:
                    break

            if threshold_met:
                filtered_trees.append(match_tree)
            elif verbose:
                print( "--- FILTERING OUT BECAUSE OF BAD CONSECUTIVE SCORES", match_tree)
        return filtered_trees, match_calculation

    def expand_match_tree_backward(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, verbose: bool = False) -> Tuple[List[VirtualBufferMatch], VirtualBufferMatchCalculation]:
        expanded_match_trees = []

        # If no further expansion is possible, just return the input match tree
        if not match_tree.can_expand_backward(submatrix):
            expanded_match_trees.append(match_tree)
        else:
            expanded_match_trees, match_calculation = self.expand_match_tree_in_direction(match_tree, match_calculation, submatrix, -1, verbose=verbose)

        # Only keep the branches that have a possibility to become the best
        return [expanded_match_tree for expanded_match_tree in expanded_match_trees if expanded_match_tree.score_potential >= match_calculation.match_threshold], match_calculation
        
    def expand_match_tree_forward(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, verbose: bool = False) -> Tuple[List[VirtualBufferMatch], VirtualBufferMatchCalculation]:
        expanded_match_trees = []

        # If no further expansion is possible, just return the input match tree
        if not match_tree.can_expand_forward(match_calculation, submatrix):
            expanded_match_trees.append(match_tree)
        else:
            expanded_match_trees, match_calculation = self.expand_match_tree_in_direction(match_tree, match_calculation, submatrix, 1, verbose=verbose)

        # Prune the branches that do not have a possibility to become the best
        return [expanded_match_tree for expanded_match_tree in expanded_match_trees if expanded_match_tree.score_potential >= match_calculation.match_threshold], match_calculation

    def expand_match_tree_in_direction(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, direction: int = 1, verbose: bool = False) -> Tuple[List[VirtualBufferMatch], VirtualBufferMatchCalculation]:
        expanded_match_trees = []

        previous_index = 0 if direction < 1 else -1
        previous_query_index = match_tree.query_indices[previous_index]
        previous_buffer_index = match_tree.buffer_indices[previous_index]
        next_query_index = match_tree.get_next_query_index(submatrix, direction)
        next_buffer_index = match_tree.get_next_buffer_index(submatrix, direction)
        next_buffer_skip_index = match_tree.get_next_buffer_index(submatrix, direction * 2)

        if verbose:
            print("- Attempting expand with " + match_calculation.words[next_query_index])

        if match_calculation.cache.should_visit_branch(previous_query_index, [next_query_index], previous_buffer_index, [next_buffer_index], submatrix):
            single_expanded_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, [next_query_index], [next_buffer_index], direction)
            match_calculation.cache.cache_score(previous_query_index, [next_query_index], previous_buffer_index, [next_buffer_index], single_expanded_match_tree.scores[previous_index], submatrix)
            expanded_match_trees.append(single_expanded_match_tree)
            if verbose:
                print( " - SINGLE EXPANSION", single_expanded_match_tree )

            combined_query_matches = self.determine_combined_query_matches(match_tree, match_calculation, submatrix, next_query_index, next_buffer_index, direction, single_expanded_match_tree)
            for combined_match in combined_query_matches:
                match_calculation.cache.cache_score(previous_query_index, combined_match.query_indices[previous_index], previous_buffer_index, [next_buffer_index], combined_match.scores[previous_index], submatrix)
            expanded_match_trees.extend(combined_query_matches)
            if verbose:
                print( " - COMBINED QUERY EXPANSION", combined_query_matches)

            if submatrix.is_valid_index(next_buffer_skip_index):
                combined_buffer_matches = self.determine_combined_buffer_matches(match_tree, match_calculation, submatrix, next_query_index, next_buffer_index, direction, single_expanded_match_tree, verbose=verbose)
                for combined_match in combined_buffer_matches:
                    match_calculation.cache.cache_score(previous_query_index, [next_query_index], previous_buffer_index, combined_match.buffer_indices[previous_index], combined_match.scores[previous_index], submatrix)
                expanded_match_trees.extend(combined_buffer_matches)
                if verbose:
                    print( " - EXPANDING COMBINED BUFFER", combined_buffer_matches )
        elif verbose:
            print( "- Already visited branch, skipping expansion" )

        # Skip a single token in the buffer for single and combined query matches
        if submatrix.is_valid_index(next_buffer_skip_index) and match_calculation.cache.should_visit_branch(previous_query_index, [next_query_index], previous_buffer_index, [next_buffer_skip_index], submatrix):
            single_skipped_expanded_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, [next_query_index], [next_buffer_skip_index], direction)

            previous_word = submatrix.tokens[next_buffer_index - (1 * direction)].phrase
            skipped_word = submatrix.tokens[next_buffer_index].phrase
            next_word = submatrix.tokens[next_buffer_skip_index].phrase
            previous_word_syllables = self.phonetic_search.syllable_count(previous_word)
            skipped_word_syllables = self.phonetic_search.syllable_count(skipped_word)
            next_word_syllables = self.phonetic_search.syllable_count(next_word)

            if verbose:
                print( " - SKIP! PREVIOUS '" + previous_word + "'", previous_word_syllables )
                print( " - SKIP! CURRENT '" + skipped_word + "'", skipped_word_syllables )
                print( " - SKIP! NEXT '" + next_word + "'", next_word_syllables )

            long_word_skip_rule = skipped_word_syllables <= previous_word_syllables and skipped_word_syllables <= next_word_syllables
            perfect_skip_rule = single_skipped_expanded_match_tree.scores[-1 if direction > 0 else 0] >= PHONETIC_MATCH and \
                single_skipped_expanded_match_tree.scores[-3 if direction > 0 else 2] >= PHONETIC_MATCH
            within_allowed_skip_count = match_tree.scores.count(0.0) + 1 <= match_calculation.allowed_skips

            check_for_select = within_allowed_skip_count and ( long_word_skip_rule or perfect_skip_rule )
            check_for_correction =  within_allowed_skip_count
            skip_check = check_for_select if match_calculation.purpose == "selection" else check_for_correction
            if skip_check:
                if verbose:
                    print( " - SINGLE SKIP EXPANSION", single_skipped_expanded_match_tree )
                expanded_match_trees.append(single_skipped_expanded_match_tree)
                match_calculation.cache.cache_score(previous_query_index, [next_query_index], previous_buffer_index, [next_buffer_skip_index], single_skipped_expanded_match_tree.scores[previous_index], submatrix)
            elif verbose:
                print( "DISCARDED SINGLE SKIPPED DUE TO LOW SCORE", single_skipped_expanded_match_tree, match_calculation.match_threshold )

            skipped_combined_query_matches = self.determine_combined_query_matches(match_tree, match_calculation, submatrix, next_query_index, next_buffer_skip_index, direction, single_skipped_expanded_match_tree)
            for combined_match in skipped_combined_query_matches:
                match_calculation.cache.cache_score(previous_query_index, combined_match.query_indices[previous_index], previous_buffer_index, [next_buffer_skip_index], combined_match.scores[previous_index], submatrix)
            expanded_match_trees.extend(skipped_combined_query_matches)

            # Combine buffer with single tokens
            next_buffer_second_skip_index = match_tree.get_next_buffer_index(submatrix, direction * 3)
            if submatrix.is_valid_index(next_buffer_second_skip_index):
                skipped_combined_buffer_matches = self.determine_combined_buffer_matches(match_tree, match_calculation, submatrix, next_query_index, next_buffer_skip_index, direction, single_skipped_expanded_match_tree, verbose=verbose)
                for combined_match in skipped_combined_buffer_matches:
                    match_calculation.cache.cache_score(previous_query_index, [next_query_index], previous_buffer_index, combined_match.buffer_indices[previous_index], combined_match.scores[previous_index], submatrix)
                expanded_match_trees.extend(skipped_combined_buffer_matches)
                if verbose:
                    print( " - EXPANDING SKIPPED COMBINED BUFFER", skipped_combined_buffer_matches)
        elif verbose:
            print( " - SKIPPED SKIP CHECKS" )

        return expanded_match_trees, match_calculation

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
    
    def determine_combined_buffer_matches(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, next_query_index: int, next_buffer_index: int, direction: int, comparison_match_tree: VirtualBufferMatch, verbose: bool = False) -> List[VirtualBufferMatch]:
        combined_buffer_match_trees = []
        next_buffer_skip_index = next_buffer_index + direction
        if submatrix.is_valid_index(next_buffer_skip_index):
            combined_buffer_indices = [next_buffer_index]
            if direction < 0:
                combined_buffer_indices.insert(0, next_buffer_skip_index)
            else:
                combined_buffer_indices.append(next_buffer_skip_index)

            # If we exceed the to-match syllables, exclude the matches?            
            query_syllable_count = self.phonetic_search.syllable_count(match_calculation.words[next_query_index])
            combined_buffer_words = submatrix.tokens[combined_buffer_indices[0]].phrase + submatrix.tokens[combined_buffer_indices[-1]].phrase
            combined_syllabe_count = self.phonetic_search.syllable_count(combined_buffer_words)
            if query_syllable_count < combined_syllabe_count:
                if verbose:
                    print( " - DISCARDED BECAUSE INCREASING SYLLABLES " + str(query_syllable_count) + " < " + str(combined_syllabe_count))
                return combined_buffer_match_trees
            elif verbose:
                print( "SYLLABLE CHECK " + "".join([token.phrase for token in submatrix.tokens[next_buffer_index:next_buffer_skip_index]]) )
            
            # Add the combined tokens, but only if the score increases
            # Compared to the single matches
            combined_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, [next_query_index], combined_buffer_indices, direction)
            skipped_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, [next_query_index], [next_buffer_skip_index], direction)
            if sum(combined_match_tree.scores) == sum(match_tree.scores) or \
                sum(combined_match_tree.scores) <= sum(comparison_match_tree.scores) or \
                sum(combined_match_tree.scores) <= sum(skipped_match_tree.scores):
                if verbose:
                    print( " - DISCARDED COMBINED BUFFER " + str(sum(combined_match_tree.scores)) + " <= " + str(sum(comparison_match_tree.scores)) + "|" + str(sum(skipped_match_tree.scores)))
                return combined_buffer_match_trees
            combined_buffer_match_trees.append(combined_match_tree)
            if verbose:
                print( " - KEPT COMBINED BUFFER " + str(sum(combined_match_tree.scores)) + " > " + str(sum(match_tree.scores)) )

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
                #print( "B COMBINED STAGE 2!", submatrix.is_valid_index(next_buffer_second_skip_index))
                combined_second_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, submatrix, [next_query_index], combined_buffer_indices, direction)
                if sum(combined_second_match_tree.scores) > sum(combined_match_tree.scores):
                    if verbose:
                        print( " - KEPT DOUBLE COMBINED BUFFER " + str(sum(combined_second_match_tree.scores)) + " > " + str(sum(combined_match_tree.scores)))
                    combined_buffer_match_trees.append(combined_second_match_tree)
                elif verbose:
                    print( " - DISCARD DOUBLE COMBINED BUFFER " + str(sum(combined_second_match_tree.scores)) + " > " + str(sum(combined_match_tree.scores)))

        return combined_buffer_match_trees

    def add_tokens_to_match_tree(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, submatrix: VirtualBufferMatchMatrix, query_indices: List[int], buffer_indices: List[int], direction: int = 1) -> VirtualBufferMatch:
        expanded_tree = match_tree.clone()

        skip_score_penalty = 0.08 # Found using trial and error

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
                expanded_tree.score_potential -= skip_score_penalty

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
                expanded_tree.score_potential -= skip_score_penalty

            skipped_words.extend(buffer_words)
            expanded_tree.buffer.extend(skipped_words)

            expanded_tree.scores.append(score)

        expanded_tree.reduce_potential(match_calculation.max_score, score, weight)
        return expanded_tree

    def compare_match_trees_for_correction(self, a: VirtualBufferMatch, b: VirtualBufferMatch) -> int:
        sort_by_score = self.compare_match_trees_by_score(a, b)
        a_overlap_padding = min(1, max(0, round(len(a.buffer_indices))))
        a_start = a.buffer_indices[0][0] - a_overlap_padding
        a_end = a.buffer_indices[-1][-1] + a_overlap_padding

        b_overlap_padding = min(1, max(0, round(len(b.buffer_indices))))
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
        
    def compare_match_trees_for_selection(self, a: VirtualBufferMatch, b: VirtualBufferMatch) -> int:
        result = self.compare_match_trees_by_score(a, b)
        if result == 0:
            if a.distance < b.distance:
                return 1
            elif a.distance > b.distance:
                return -1
        return result

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

    def find_potential_submatrices_for_words(self, matrix: VirtualBufferMatchMatrix, match_calculation: VirtualBufferMatchCalculation, word_indices: List[int], max_submatrix_size: int, verbose: bool = False) -> List[VirtualBufferMatchMatrix]:
        submatrices = []
        relative_left_index = -(word_indices[0] + ( max_submatrix_size - match_calculation.length ) / 2)
        relative_right_index = relative_left_index + max_submatrix_size

        # Only search within the viable range ( no cut off matches at the start and end of the matrix )
        # Due to multiple different fuzzy matches being possible, it isn't possible to do token skipping
        # Like in the Boyer–Moore string-search algorithm
        # But if we have exact matches that we need to filter out, we can do something similar to Boyer-Moore
        for matrix_index in range(word_indices[0], len(matrix.tokens)):
            if match_calculation.cache.should_skip_index(matrix.index + matrix_index):
                continue
            matrix_token = matrix.tokens[matrix_index]
            threshold = match_calculation.match_threshold * sum([match_calculation.weights[word_index] for word_index in word_indices])

            query_tokens = "".join([match_calculation.words[word_index] for word_index in word_indices])
            score = self.get_memoized_similarity_score(matrix_token.phrase.replace(" ", ""), query_tokens)
            single_score = score
            buffer_indices = [matrix_index]

            # Add buffer combinations as well if we are matching with a single word
            if len(word_indices) == 1:
                # Combine forward
                if matrix_index + 1 < len(matrix.tokens):
                    phrases = [matrix_token.phrase, matrix.tokens[matrix_index + 1].phrase]
                    combined_score = self.get_memoized_similarity_score("".join(phrases).replace(" ", ""), query_tokens)
                    if combined_score > single_score:
                        if matrix_index + 2 < len(matrix.tokens):
                            phrases.append( matrix.tokens[matrix_index + 2].phrase )
                            triple_combined_score = self.get_memoized_similarity_score("".join(phrases).replace(" ", ""), query_tokens)
                            if triple_combined_score > combined_score:
                                buffer_indices = [matrix_index, matrix_index + 1, matrix_index + 2]
                                score = triple_combined_score
                        if combined_score > score:
                            buffer_indices = [matrix_index, matrix_index + 1]
                            score = combined_score

                # Combine backward
                if matrix_index - 1 >= 0:
                    phrases = [matrix.tokens[matrix_index - 1].phrase, matrix_token.phrase]
                    combined_score = self.get_memoized_similarity_score("".join(phrases).replace(" ", ""), query_tokens)
                    if combined_score > single_score:
                        if matrix_index - 2 >= 0:
                            phrases.insert(0, matrix.tokens[matrix_index - 2].phrase)
                            triple_combined_score = self.get_memoized_similarity_score("".join(phrases).replace(" ", ""), query_tokens)
                            if triple_combined_score > combined_score and triple_combined_score > score:
                                buffer_indices = [matrix_index - 2, matrix_index - 1, matrix_index]
                                score = triple_combined_score
                        if combined_score > score:
                            buffer_indices = [matrix_index - 1, matrix_index]
                            score = combined_score

            has_starting_match = score >= threshold
            if verbose:
                print( "Score for " + query_tokens + " = " + matrix_token.phrase.replace(" ", "") + ": " + str(score) + " with weighted thresh:" + str(threshold), score >= threshold)
            if has_starting_match:
                starting_index = max(0, round(matrix_index + relative_left_index - 1))
                ending_index = min(len(matrix.tokens), round(matrix_index + relative_right_index))
                submatrix = matrix.get_submatrix(starting_index, ending_index)
                if (len(submatrix.tokens) > 0):
                    submatrices.append(submatrix)
                    match_calculation.append_starting_branch(word_indices, [matrix.index + index for index in buffer_indices], score)

        return submatrices, match_calculation

    def simplify_submatrices(self, submatrices: List[VirtualBufferMatchMatrix]) -> List[VirtualBufferMatchMatrix]:
        # Sort by index so it is easier to merge by index later
        submatrices = list(set(submatrices))
        submatrices.sort(key=lambda x: x.index)

        merged_matrices = []
        current_submatrix = None
        for submatrix in submatrices:
            if current_submatrix is not None:

                # Merge and continue on overlap
                if self.can_merge_matrices(current_submatrix, submatrix):
                    current_submatrix = self.merge_matrices(current_submatrix, submatrix)
                    continue

                # Append and set the current submatrix
                else:
                    merged_matrices.append(current_submatrix)
            current_submatrix = submatrix

        if current_submatrix is not None:
            merged_matrices.append(current_submatrix)
        return merged_matrices

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

    def find_self_repair_match(self, virtual_buffer, phrases: List[str], verbose: bool = False) -> VirtualBufferMatch:
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
                    phrases_to_use = [phrase for phrase in phrases]                    
                    while len(phrases_to_use) > 0:
                        tokens, best_match = self.find_best_match_by_phrases(virtual_buffer, phrases_to_use, CORRECTION_THRESHOLD, for_correction=True, for_selfrepair=True, verbose=verbose)

                        # Get the match with the most matches, closest to the end
                        # Make sure we adhere to 'reasonable' self repair of about 5 words back max
                        if best_match is not None:
                            # When the final index does not align with the current index, it won't be a self repair replacement
                            final_token_matches = best_match.buffer_indices[-1][-1] >= current_index[0]

                            # When the first word of the match isn't exact it is not a self repair
                            if len(best_match.scores) <= 2:
                                first_token_matches = best_match.scores[0] >= self.get_threshold_for_selection([token.phrase for token in tokens], SELECTION_THRESHOLD)
                            else:
                                first_token_matches = best_match.scores[0] >= CORRECTION_THRESHOLD

                            # If it is only the first token that doesn't match, but the rest is very confident
                            # We expect we need to replace the first item
                            first_token_doesnt_match_but_others_high = best_match.scores[0] < CORRECTION_THRESHOLD and \
                                best_match.score_potential > SELECTION_THRESHOLD
                            if final_token_matches and (first_token_matches or first_token_doesnt_match_but_others_high):
                                if verbose:
                                    print("FOUND SELF-REPAIR MATCH", best_match)
                                return best_match
                        phrases_to_use.pop()
        
        return None

    def find_best_match_by_phrases(self, virtual_buffer, phrases: List[str], match_threshold: float = SELECTION_THRESHOLD, next_occurrence: bool = True, selecting: bool = False, for_correction: bool = False, for_selfrepair: bool = False, verbose: bool = False) -> (List[VirtualBufferToken], VirtualBufferMatch):
        matches = self.find_top_three_matches_in_matrix(virtual_buffer, phrases, match_threshold, selecting, for_correction, for_selfrepair, verbose)

        if verbose:
            print( "All available matches:", matches, next_occurrence )

        if len(matches) > 0:
            best_match_tokens = []
            best_match = matches[0]

            if len(matches) > 1:
                # Sort matches
                if selecting:
                    matches.sort(key = cmp_to_key(self.compare_match_trees_for_selection), reverse=True)
                if for_correction:
                    matches.sort(key = cmp_to_key(self.compare_match_trees_for_correction), reverse=True)

                # TODO SELECT NEXT IN DIRECTION IN CASE OF REPETITION
                # For now it will just skip between two nearest elements
                if verbose:
                    print( "After sorting", matches)
                if next_occurrence and len(matches) > 1:
                    if verbose:
                        print( "Discarding first item due to it being selected", matches )
                    matches.pop(0)

                best_match = matches[0]

            for index_list in best_match.buffer_indices:
                for subindex in index_list:
                    best_match_tokens.append(virtual_buffer.tokens[subindex])

            if verbose:
                print( "BEST MATCH TOKENS", best_match_tokens )

            return (best_match_tokens, best_match)
        else:
            return (None, None)
    
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
        if word_a + ":" + word_b not in self.checked_comparisons:
            self.checked_comparisons[word_a + ":" + word_b] = 0
        self.checked_comparisons[word_a + ":" + word_b] += 1

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