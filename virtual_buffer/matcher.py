from ..phonetics.phonetics import PhoneticSearch
from ..phonetics.detection import EXACT_MATCH, HOMOPHONE_MATCH, PHONETIC_MATCH
from .typing import VirtualBufferToken, VirtualBufferTokenMatch, VirtualBufferMatchCalculation, VirtualBufferTokenList, VirtualBufferMatch, VirtualBufferTokenContext, VirtualBufferMatchVisitCache, SELECTION_THRESHOLD, CORRECTION_THRESHOLD
import re
from typing import List, Dict, Tuple
import math
from functools import cmp_to_key

# Number found through experimentation
# A combined score needs to be at least this number better of a match to be considered a valid root
combined_better_threshold = 0.075

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", ' ', text).replace("\n", " ")

# Class to find the best matches inside of virtual buffers
class VirtualBufferMatcher:

    phonetic_search: PhoneticSearch = None
    similarity_token_list: Dict[str, float] = None

    def __init__(self, phonetic_search: PhoneticSearch):
        self.phonetic_search = phonetic_search
        self.similarity_token_list = {}

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

    def find_top_three_matches_in_token_list(self, virtual_buffer, phrases: List[str], match_threshold: float = SELECTION_THRESHOLD, selecting: bool = False, for_correction: bool = False, verbose: bool = False):
        # Don't change the match threshold for corrections
        if not for_correction:
            match_threshold = self.get_threshold_for_selection(phrases, match_threshold)

        leftmost_token_index = virtual_buffer.determine_leftmost_token_index()[0]
        rightmost_token_index = virtual_buffer.determine_rightmost_token_index()[0]
        starting_index = 0
        ending_index = len(virtual_buffer.tokens)
        token_list = VirtualBufferTokenList(starting_index, virtual_buffer.tokens[starting_index:ending_index])
        match_calculation = self.generate_match_calculation(phrases, match_threshold, purpose=("correction" if for_correction else "selection"))
        match_calculation.cache.index_token_list(token_list)
        windowed_sublists = token_list.get_windowed_sublists(leftmost_token_index, match_calculation)

        if verbose:
            print( "- Using match threshold: " + str(match_calculation.match_threshold))
            print( "- Splitting into " + str(len(windowed_sublists)) + " windowed sublists for rapid searching")

        highest_score_achieved = False
        for windowed_sublist in windowed_sublists:
            sublists, match_calculation = self.find_potential_sublists(match_calculation, windowed_sublist, verbose=verbose)
            split_sublists = self.split_sublists_by_cursor_position(sublists, leftmost_token_index, rightmost_token_index)
            matches = []

            highest_found_match = match_threshold
            for index, token_list_group in enumerate(split_sublists):
                match_calculation.match_threshold = match_threshold
                token_list_group_matches = []
                highest_match = 0
                for sublist in token_list_group:
                    sublist_matches, match_calculation = self.find_matches_in_token_list(match_calculation, sublist, highest_match, verbose=verbose)
                    if len(sublist_matches) > 0:
                        highest_match = max(highest_match, sublist_matches[0].score_potential)
                        #if verbose:
                        #    print( "- Updating threshold to: " + str(highest_match))
                        token_list_group_matches.extend(sublist_matches)
                        if not for_correction:
                            highest_score_achieved = highest_match == match_calculation.max_score

                    # Do not seek any further if we have reached the highest possible score
                    # Since no improvement is possible
                    # Also do not seek further for correction cases as we never look beyond matches closest to the cursor anyway
                    if highest_score_achieved or (for_correction and len(sublist_matches) > 0):
                        break
                
                if verbose:
                    print( "- Found matches for split " + str(index), token_list_group_matches )

                # Calculate the distance from the cursor
                for token_list_group_match in token_list_group_matches:
                    token_list_group_match.calculate_distance(leftmost_token_index, rightmost_token_index)

                if len(token_list_group_matches) > 0:
                    if selecting:
                        token_list_group_matches.sort(key = cmp_to_key(self.compare_match_trees_for_selection), reverse=True)
                    if for_correction:
                        token_list_group_matches.sort(key = cmp_to_key(self.compare_match_trees_for_correction), reverse=True)
                    matches.append(token_list_group_matches[0])
                    highest_found_match = max(highest_found_match, highest_match)

            if highest_score_achieved:
                break
            match_calculation.match_threshold = highest_found_match

            # Make sure we do not match on the exact matches again as we are sure we are closest to the cursor
            # For the currently found matches
            for match in matches:
                if verbose:
                    print("SKIP WORD SEQUENCE", match.buffer)
                match_calculation.cache.skip_word_sequence(match.buffer)
            
            # Add indices to skip because they do not match anything in the total token_list
            if verbose and windowed_sublist.index == 0:
                print( "BUFFER INDEX SCORES", match_calculation.cache.buffer_index_scores)
            non_match_threshold = 0.1 if match_calculation.purpose == "correction" else 0.29
            for windowed_index in range(windowed_sublist.index, windowed_sublist.end_index):
                if not match_calculation.cache.should_skip_index(windowed_index):
                    score_for_index = match_calculation.cache.get_highest_score_for_buffer_index(windowed_index)
                    if score_for_index >= 0 and score_for_index < non_match_threshold:
                        if verbose:
                            print("SKIP SPECIFIC WORD!", score_for_index, windowed_index, token_list.tokens[windowed_index - token_list.index].phrase)
                        match_calculation.cache.skip_word_sequence([token_list.tokens[windowed_index - token_list.index].phrase])
                    elif verbose:
                        print("DO NOT SKIP WORD", score_for_index, non_match_threshold, windowed_index)
                elif verbose:
                    print("SKIP INDEX", windowed_index)
        
        return matches

    # Generate a match calculation based on the words to search for weighted by syllable count
    def generate_match_calculation(self, query_words: List[str], threshold: float = SELECTION_THRESHOLD, max_score_per_word: float = EXACT_MATCH, purpose: str = "selection") -> VirtualBufferMatchCalculation:
        syllables_per_word = [self.phonetic_search.syllable_count(word) for word in query_words]
        total_syllables = max(sum(syllables_per_word), 1)
        weights = [syllable_count / total_syllables for syllable_count in syllables_per_word]
        
        match_calculation = VirtualBufferMatchCalculation(query_words, weights, syllables_per_word, threshold, max_score_per_word, purpose)
        match_calculation.cache = VirtualBufferMatchVisitCache()
        return match_calculation
    
    # Generate a list of (sorted) potential sublists to look through
    def find_potential_sublists(self, match_calculation: VirtualBufferMatchCalculation, token_list: VirtualBufferTokenList, verbose: bool = False):
        match_calculation.starting_branches = []
        word_indices = match_calculation.get_possible_branches()
        max_sublist_size = len(match_calculation.words) * 3
        sub_token_lists = []

        # Create a dictionary of indices to skip over for exact matches
        # For performance gains for large fuzzy searches
        if match_calculation.cache.should_skip_sublist(token_list, match_calculation):
            if verbose:
                print( "    - SKIPPING ENTIRE token_list BECAUSE THE MAX SEQUENCE ISN'T ENOUGH FOR A MATCH")
            return [], match_calculation
        elif verbose:
            print( "    - CAN USE token_list BECAUSE THERE IS A BIG ENOUGH MAX SEQUENCE")

        for word_index in word_indices:
            potential_sublists, match_calculation = self.find_potential_sublists_for_words(token_list, match_calculation, word_index, max_sublist_size, verbose=verbose)
            sub_token_lists.extend(potential_sublists)

        if verbose:
            print( "    - FOUND ROOTS FOR THESE token_lists", len(sub_token_lists))
            print( match_calculation.starting_branches )

        sub_token_lists = self.simplify_sublists(sub_token_lists)
        if verbose:
            print("    - Simplified to these token_lists", len(sub_token_lists))

        return sub_token_lists, match_calculation

    # Split the sublists up into three zones that are important for selection
    # The zone before, on and after the caret
    def split_sublists_by_cursor_position(self, sublists: List[VirtualBufferTokenList], left_index: int, right_index: int) -> List[List[VirtualBufferTokenList]]:
        before = []
        current = []
        after = []

        for sublist in sublists:
            if sublist.end_index < left_index:
                before.append(sublist)
            elif sublist.index > right_index:
                after.append(sublist)
            else:
                current.append(sublist)

        # Sort the token_lists before the cursor in the opposite direction,
        # the assumption being that the closest match to the cursor matters most
        before.reverse()

        return [before, current, after]
    
    def find_matches_in_token_list(self, match_calculation: VirtualBufferMatchCalculation, sublist: VirtualBufferTokenList, highest_match: float = 0, early_stopping: bool = True, verbose: bool = False) -> Tuple[List[VirtualBufferMatch], VirtualBufferMatchCalculation]:
        branches = match_calculation.get_starting_branches(sublist)
        query = match_calculation.words
        buffer = [token.phrase for token in sublist.tokens]

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
                normalized_buffer_indices = [index - sublist.index for index in branch.buffer_indices]
                match_branch.buffer_indices.append(normalized_buffer_indices)
                match_branch.buffer.extend([buffer[buffer_index] for buffer_index in normalized_buffer_indices])
                match_branch.scores.append(branch.score)
                match_branch.reduce_potential(match_calculation.max_score, branch.score, combined_weight) 
                match_branches.append(match_branch)
            elif verbose:
                print( "Branch rejected because ", branch.score_potential, "<", match_calculation.match_threshold, branch )

        # Filter searches that do not match the previous best and sort by the best score first
        searches = []
        if verbose:
            print("Found matched branches", match_branches )
        for match_root in match_branches:
            if verbose:
                print( "Expand root for ", match_root )
            expanded_tree, match_calculation = self.expand_match_tree(match_root, match_calculation, sublist, verbose=verbose)
            searches.extend(expanded_tree)
        filtered_searches = [search for search in searches if search.score_potential >= highest_match and len(search.query) == len(match_calculation.words)]
        filtered_searches.sort(key = cmp_to_key(self.compare_match_trees_by_score), reverse=True)

        # Use global token_list indices for every match
        for search in filtered_searches:
            search.to_global_index(sublist)
        return filtered_searches, match_calculation

    def expand_match_tree(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, sublist: VirtualBufferTokenList, verbose: bool = False) -> Tuple[List[VirtualBufferTokenList], VirtualBufferMatchCalculation]:
        match_trees = [match_tree]
        expanded_match_trees: List[VirtualBufferMatch] = []

        # First expand backwards if we haven't already walked that path
        if match_tree.can_expand_backward(sublist):
            can_expand_backward_count = 1
            while can_expand_backward_count != 0:
                expanded_match_trees = []
                for match_tree in match_trees:
                    backward_expanded_match_tree, match_calculation = self.expand_match_tree_backward(match_tree, match_calculation, sublist, verbose=verbose)
                    expanded_match_trees.extend(backward_expanded_match_tree)
                can_expand_backward_count = sum([expanded_match_tree.can_expand_backward(sublist) for expanded_match_tree in expanded_match_trees])
                match_trees = list(set(expanded_match_trees))
            
            if verbose:
                print( "---- BACKWARD", match_trees )
        elif verbose:
            print( "---- Match tree cannot expand backward from the start")

        # Then expand forwards if possible
        if match_tree.can_expand_forward(match_calculation, sublist):
            can_expand_forward_count = 1
            while can_expand_forward_count != 0:
                expanded_match_trees = []
                for match_tree in match_trees:
                    forward_expanded_match_tree, match_calculation = self.expand_match_tree_forward(match_tree, match_calculation, sublist, verbose=verbose)
                    expanded_match_trees.extend(forward_expanded_match_tree)
                can_expand_forward_count = sum([expanded_match_tree.can_expand_forward(match_calculation, sublist) for expanded_match_tree in expanded_match_trees])
                match_trees = list(set(expanded_match_trees))
            
            if verbose:
                print( "---- FORWARD", match_trees )
        elif verbose:
            print( "---- Match tree cannot expand forward from the start")

        return self.filter_expanded_match_trees(match_trees, match_calculation, verbose=verbose), match_calculation
    
    def filter_expanded_match_trees(self, match_trees: List[VirtualBufferMatch], match_calculation: VirtualBufferMatchCalculation, verbose=False) -> List[VirtualBufferMatch]:
        # Filter out results with multiple consecutive bad results
        low_score_threshold = match_calculation.match_threshold / 2
        single_word_score_threshold = -1 if match_calculation.purpose == "correction" else 0.29
        combined_word_score_threshold = 0.3 if match_calculation.purpose == "correction" else 0.5
        three_combined_word_score_threshold = 0.5
        
        if match_calculation.purpose == "correction":
            consecutive_low_score_threshold = 2
        else:
            consecutive_low_score_threshold = 1 if len(match_calculation.words) <= 2 else 2

        filtered_trees = []
        for match_tree in match_trees:
            consecutive_low_scores = 0

            # Cannot start or end with a 0 / skip for selections
            threshold_met = match_calculation.purpose == "correction" or ( match_tree.scores[0] > 0.0 and match_tree.scores[-1] > 0.0 )
            
            # We want to do a rescaling of the match calculation as if we used the full query and buffer result
            # So we can determine if matches would be made one way or the other
            matched_words = match_tree.get_matched_words()
            rescaled_query_match_calculation = self.generate_match_calculation(matched_words.get_query_words(), match_calculation.match_threshold, purpose=match_calculation.purpose)
            rescaled_buffer_match_calculation = self.generate_match_calculation(matched_words.get_buffer_words(), match_calculation.match_threshold, purpose=match_calculation.purpose)
            rescaled_query_score_potential = 0
            rescaled_buffer_score_potential = 0

            query_offset = 0
            buffer_offset = 0
            for index, score in enumerate(matched_words.scores):
                query_weight = 0
                query = matched_words.query[index]
                for inner_index in range(0, len(query)):
                    query_weight += rescaled_query_match_calculation.weights[inner_index + query_offset]
                query_offset += len(query)

                buffer_weight = 0
                buffer = matched_words.buffer[index]
                for inner_buffer_index in range(0, len(buffer)):
                    buffer_weight += rescaled_buffer_match_calculation.weights[inner_buffer_index + buffer_offset]
                buffer_offset += len(buffer)

                # Rescaling weights and scores for self repair
                # Because often the query matches are incomplete if more text is added after the self repair match
                # And the match calculation score potentials are calculated based on a full match instead
                # We need to rescale the potentials based on the actual query words and weights involved
                # Before filtering out the match trees based on the correction rules
                rescaled_query_score_potential += score * query_weight
                rescaled_buffer_score_potential += score * buffer_weight

                weighted_low_score_threshold = low_score_threshold * query_weight / 1.5
                weighted_low_buffer_score_threshold = low_score_threshold * buffer_weight / 1.5

                if score * query_weight <= weighted_low_score_threshold or \
                    score * buffer_weight <= weighted_low_buffer_score_threshold:
                    consecutive_low_scores += 1
                else:
                    consecutive_low_scores = 0
                
                matches_muliple_words = len(query) > 1 or len(buffer) > 1
                single_threshold = combined_word_score_threshold if matches_muliple_words else single_word_score_threshold
                if not match_calculation.selfrepair and ( len(query) == 3 or len(buffer) == 3 ):
                    single_threshold = three_combined_word_score_threshold

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

            if match_calculation.selfrepair and match_tree.query_indices[0][0] != 0:
                if verbose:
                    print("SKIPPED BECAUSE SELF REPAIR DOES NOT START WITH THE INDEX AT THE START")
                threshold_met = False

            if threshold_met:
                if match_calculation.selfrepair or match_calculation.purpose != "correction":
                    min_score_potential = min(rescaled_buffer_score_potential, rescaled_query_score_potential)
                    if verbose:
                        print( "Rescaling match tree score potential from ", match_tree.score_potential, " to ", min_score_potential, " picking from ", rescaled_buffer_score_potential, "and ", rescaled_query_score_potential)
                    match_tree.score_potential = min_score_potential
                    threshold_met = match_tree.score_potential >= match_calculation.match_threshold

            if threshold_met:
                filtered_trees.append(match_tree)
            elif verbose:
                print( "--- FILTERING OUT BECAUSE OF BAD CONSECUTIVE SCORES", match_tree)
        return filtered_trees

    def expand_match_tree_backward(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, sublist: VirtualBufferTokenList, verbose: bool = False) -> Tuple[List[VirtualBufferMatch], VirtualBufferMatchCalculation]:
        expanded_match_trees = []

        # If no further expansion is possible, just return the input match tree
        if not match_tree.can_expand_backward(sublist):
            expanded_match_trees.append(match_tree)
        else:
            expanded_match_trees, match_calculation = self.expand_match_tree_in_direction(match_tree, match_calculation, sublist, -1, verbose=verbose)

        # Only keep the branches that have a possibility to become the best
        return [expanded_match_tree for expanded_match_tree in expanded_match_trees if expanded_match_tree.score_potential >= match_calculation.match_threshold], match_calculation
        
    def expand_match_tree_forward(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, sublist: VirtualBufferTokenList, verbose: bool = False) -> Tuple[List[VirtualBufferMatch], VirtualBufferMatchCalculation]:
        expanded_match_trees = []

        # If no further expansion is possible, just return the input match tree
        if not match_tree.can_expand_forward(match_calculation, sublist):
            expanded_match_trees.append(match_tree)
        else:
            expanded_match_trees, match_calculation = self.expand_match_tree_in_direction(match_tree, match_calculation, sublist, 1, verbose=verbose)

        # Prune the branches that do not have a possibility to become the best
        return [expanded_match_tree for expanded_match_tree in expanded_match_trees if expanded_match_tree.score_potential >= match_calculation.match_threshold], match_calculation

    def expand_match_tree_in_direction(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, sublist: VirtualBufferTokenList, direction: int = 1, verbose: bool = False) -> Tuple[List[VirtualBufferMatch], VirtualBufferMatchCalculation]:
        expanded_match_trees = []

        previous_index = 0 if direction < 1 else -1
        previous_query_index = match_tree.query_indices[previous_index]
        previous_buffer_index = match_tree.buffer_indices[previous_index]
        next_query_index = match_tree.get_next_query_index(sublist, direction)
        next_buffer_index = match_tree.get_next_buffer_index(sublist, direction)
        next_buffer_skip_index = match_tree.get_next_buffer_index(sublist, direction * 2)

        if verbose:
            print("- Attempting expand with " + match_calculation.words[next_query_index])

        single_expanded_match_tree = None
        # Only check the visit branch if we are starting off a branch
        if len(match_tree.query_indices) > 1 or match_calculation.cache.should_visit_branch(previous_query_index, [next_query_index], previous_buffer_index, [next_buffer_index], sublist):
            single_expanded_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, sublist, [next_query_index], [next_buffer_index], direction)
            match_calculation.cache.cache_score(previous_query_index, [next_query_index], previous_buffer_index, [next_buffer_index], single_expanded_match_tree.scores[previous_index], sublist)
            expanded_match_trees.append(single_expanded_match_tree)
            if verbose:
                print( " - SINGLE EXPANSION", single_expanded_match_tree )

            combined_query_matches = self.determine_combined_query_matches(match_tree, match_calculation, sublist, next_query_index, next_buffer_index, direction, single_expanded_match_tree)
            for combined_match in combined_query_matches:
                match_calculation.cache.cache_score(previous_query_index, combined_match.query_indices[previous_index], previous_buffer_index, [next_buffer_index], combined_match.scores[previous_index], sublist)
            expanded_match_trees.extend(combined_query_matches)
            if verbose:
                print( " - COMBINED QUERY EXPANSION", combined_query_matches)

            if sublist.is_valid_index(next_buffer_skip_index):
                combined_buffer_matches = self.determine_combined_buffer_matches(match_tree, match_calculation, sublist, next_query_index, next_buffer_index, direction, single_expanded_match_tree, verbose=verbose)
                for combined_match in combined_buffer_matches:
                    match_calculation.cache.cache_score(previous_query_index, [next_query_index], previous_buffer_index, combined_match.buffer_indices[previous_index], combined_match.scores[previous_index], sublist)
                expanded_match_trees.extend(combined_buffer_matches)
                if verbose:
                    print( " - EXPANDING COMBINED BUFFER", combined_buffer_matches )
        elif verbose:
            print( "- Already visited branch, skipping expansion" )

        # Skip a single token in the buffer for single and combined query matches
        if sublist.is_valid_index(next_buffer_skip_index) and ( len(match_tree.query_indices) > 1 or match_calculation.cache.should_visit_branch(previous_query_index, [next_query_index], previous_buffer_index, [next_buffer_skip_index], sublist) ):
            single_skipped_expanded_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, sublist, [next_query_index], [next_buffer_skip_index], direction)

            previous_word = sublist.tokens[next_buffer_index - (1 * direction)].phrase
            skipped_word = sublist.tokens[next_buffer_index].phrase
            next_word = sublist.tokens[next_buffer_skip_index].phrase
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
            if match_calculation.selfrepair:
                higher_score_rule = not single_expanded_match_tree or (single_expanded_match_tree.scores[previous_index] < single_skipped_expanded_match_tree.scores[-1 if direction > 0 else 0])
                skip_check = within_allowed_skip_count and higher_score_rule

            if skip_check:
                if verbose:
                    print( " - SINGLE SKIP EXPANSION", single_skipped_expanded_match_tree )

                expanded_match_trees.append(single_skipped_expanded_match_tree)
                match_calculation.cache.cache_score(previous_query_index, [next_query_index], previous_buffer_index, [next_buffer_skip_index], single_skipped_expanded_match_tree.scores[previous_index], sublist)
            elif verbose:
                print( "DISCARDED SINGLE SKIPPED DUE TO LOW SCORE", single_skipped_expanded_match_tree, match_calculation.match_threshold )

            skipped_combined_query_matches = self.determine_combined_query_matches(match_tree, match_calculation, sublist, next_query_index, next_buffer_skip_index, direction, single_skipped_expanded_match_tree)
            for combined_match in skipped_combined_query_matches:
                match_calculation.cache.cache_score(previous_query_index, combined_match.query_indices[previous_index], previous_buffer_index, [next_buffer_skip_index], combined_match.scores[previous_index], sublist)
            expanded_match_trees.extend(skipped_combined_query_matches)

            # Combine buffer with single tokens
            next_buffer_second_skip_index = match_tree.get_next_buffer_index(sublist, direction * 3)
            if sublist.is_valid_index(next_buffer_second_skip_index):
                skipped_combined_buffer_matches = self.determine_combined_buffer_matches(match_tree, match_calculation, sublist, next_query_index, next_buffer_skip_index, direction, single_skipped_expanded_match_tree, verbose=verbose)
                for combined_match in skipped_combined_buffer_matches:
                    match_calculation.cache.cache_score(previous_query_index, [next_query_index], previous_buffer_index, combined_match.buffer_indices[previous_index], combined_match.scores[previous_index], sublist)
                expanded_match_trees.extend(skipped_combined_buffer_matches)
                if verbose:
                    print( " - EXPANDING SKIPPED COMBINED BUFFER", skipped_combined_buffer_matches)
        elif verbose:
            print( " - SKIPPED SKIP CHECKS" )

        return expanded_match_trees, match_calculation

    def determine_combined_query_matches(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, sublist: VirtualBufferTokenList, next_query_index: int, next_buffer_index: int, direction: int, comparison_match_tree: VirtualBufferMatch) -> List[VirtualBufferMatch]:
        combined_match_trees = []
        next_query_skip_index = next_query_index + direction
        if match_tree.is_valid_index(match_calculation, sublist, next_query_skip_index):
            combined_query_indices = [next_query_index]
            if direction < 0:
                combined_query_indices.insert(0, next_query_skip_index)
            else:
                combined_query_indices.append(next_query_skip_index)

            # Add the combined tokens, but only if the score increases
            # Compared to the current match tree, and the match tree that would be 
            combined_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, sublist, combined_query_indices, [next_buffer_index], direction)
            if sum(combined_match_tree.scores) - combined_better_threshold == sum(match_tree.scores) or \
                sum(combined_match_tree.scores) - combined_better_threshold < sum(comparison_match_tree.scores):
                return combined_match_trees
            combined_match_trees.append(combined_match_tree)

            # Combine three if possible
            next_query_second_skip_index = next_query_index + (direction * 2)
            if match_tree.is_valid_index(match_calculation, sublist, next_query_second_skip_index):
                combined_query_indices = [next_query_index]
                if direction < 0:
                    combined_query_indices.insert(0, next_query_skip_index)
                    combined_query_indices.insert(0, next_query_second_skip_index)                    
                else:
                    combined_query_indices.append(next_query_skip_index)
                    combined_query_indices.append(next_query_second_skip_index)

                # Only add if the combined match tree increases the total score
                combined_second_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, sublist, combined_query_indices, [next_buffer_index], direction)
                if sum(combined_second_match_tree.scores) > sum(combined_match_tree.scores):
                    combined_match_trees.append(combined_second_match_tree)
        return combined_match_trees
    
    def determine_combined_buffer_matches(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, sublist: VirtualBufferTokenList, next_query_index: int, next_buffer_index: int, direction: int, comparison_match_tree: VirtualBufferMatch, verbose: bool = False) -> List[VirtualBufferMatch]:
        combined_buffer_match_trees = []
        next_buffer_skip_index = next_buffer_index + direction
        if sublist.is_valid_index(next_buffer_skip_index):
            combined_buffer_indices = [next_buffer_index]
            if direction < 0:
                combined_buffer_indices.insert(0, next_buffer_skip_index)
            else:
                combined_buffer_indices.append(next_buffer_skip_index)

            # If we exceed the to-match syllables, exclude the matches?            
            query_syllable_count = self.phonetic_search.syllable_count(match_calculation.words[next_query_index])
            combined_buffer_words = sublist.tokens[combined_buffer_indices[0]].phrase + sublist.tokens[combined_buffer_indices[-1]].phrase
            combined_syllabe_count = self.phonetic_search.syllable_count(combined_buffer_words)
            if query_syllable_count < combined_syllabe_count:
                if verbose:
                    print( " - DISCARDED BECAUSE INCREASING SYLLABLES " + str(query_syllable_count) + " < " + str(combined_syllabe_count))
                return combined_buffer_match_trees
            elif verbose:
                print( "SYLLABLE CHECK " + "".join([token.phrase for token in sublist.tokens[next_buffer_index:next_buffer_skip_index]]) )
            
            # Add the combined tokens, but only if the score increases
            # Compared to the single matches
            combined_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, sublist, [next_query_index], combined_buffer_indices, direction)
            skipped_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, sublist, [next_query_index], [next_buffer_skip_index], direction)
            if sum(combined_match_tree.scores) - combined_better_threshold == sum(match_tree.scores) or \
                sum(combined_match_tree.scores) - combined_better_threshold <= sum(comparison_match_tree.scores) or \
                sum(combined_match_tree.scores) - combined_better_threshold <= sum(skipped_match_tree.scores):
                if verbose:
                    print( " - DISCARDED COMBINED BUFFER " + str(sum(combined_match_tree.scores)) + " <= " + str(sum(comparison_match_tree.scores)) + "|" + str(sum(skipped_match_tree.scores)))
                return combined_buffer_match_trees
            combined_buffer_match_trees.append(combined_match_tree)
            if verbose:
                print( " - KEPT COMBINED BUFFER " + str(sum(combined_match_tree.scores)) + " > " + str(sum(match_tree.scores)) )

            # Combine three if possible
            next_buffer_second_skip_index = next_buffer_index + (direction * 2)
            if sublist.is_valid_index(next_buffer_second_skip_index):
                combined_buffer_indices = [next_buffer_index]
                if direction < 0:
                    combined_buffer_indices.insert(0, next_buffer_skip_index)
                    combined_buffer_indices.insert(0, next_buffer_second_skip_index)
                else:
                    combined_buffer_indices.append(next_buffer_skip_index)
                    combined_buffer_indices.append(next_buffer_second_skip_index)

                # Only add if the combined match tree increases the total score
                #print( "B COMBINED STAGE 2!", sublist.is_valid_index(next_buffer_second_skip_index))
                combined_second_match_tree = self.add_tokens_to_match_tree(match_tree, match_calculation, sublist, [next_query_index], combined_buffer_indices, direction)
                if sum(combined_second_match_tree.scores) > sum(combined_match_tree.scores):
                    if verbose:
                        print( " - KEPT DOUBLE COMBINED BUFFER " + str(sum(combined_second_match_tree.scores)) + " > " + str(sum(combined_match_tree.scores)))
                    combined_buffer_match_trees.append(combined_second_match_tree)
                elif verbose:
                    print( " - DISCARD DOUBLE COMBINED BUFFER " + str(sum(combined_second_match_tree.scores)) + " > " + str(sum(combined_match_tree.scores)))

        return combined_buffer_match_trees

    def add_tokens_to_match_tree(self, match_tree: VirtualBufferMatch, match_calculation: VirtualBufferMatchCalculation, sublist: VirtualBufferTokenList, query_indices: List[int], buffer_indices: List[int], direction: int = 1) -> VirtualBufferMatch:
        expanded_tree = match_tree.clone()

        skip_score_penalty = 0.08 # Found using trial and error

        query_words = [match_calculation.words[query_index] for query_index in query_indices]
        buffer_words = [sublist.tokens[buffer_index].phrase for buffer_index in buffer_indices]
        weight = sum([match_calculation.weights[query_index] for query_index in query_indices])
        score = self.get_memoized_similarity_score("".join(query_words), "".join(buffer_words))
        skipped_scores = []
        skipped_words = []

        if direction < 0:
            # Add skipped words as well
            last_buffer_index = buffer_indices[-1] + 1
            last_found_index = expanded_tree.buffer_indices[0][0]
            for skipped_index in range(last_buffer_index, last_found_index):
                skipped_words.insert(0, sublist.tokens[skipped_index].phrase)

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
                skipped_words.append(sublist.tokens[skipped_index].phrase)

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
        overlap_size = max(0.33, (len(a.buffer) / 2) * 0.5)
        a_overlap_padding = max(1, round(len(a.buffer) * overlap_size))
        a_start = max(0, a.buffer_indices[0][0] - a_overlap_padding)
        a_end = a.buffer_indices[-1][-1] + a_overlap_padding

        overlap_size = max(0.33, (len(b.buffer) / 2) * 0.5)
        b_overlap_padding = max(1, round(len(b.buffer) * overlap_size))
        b_start = max(0, b.buffer_indices[0][0] - b_overlap_padding)
        b_end = b.buffer_indices[-1][-1] + b_overlap_padding

        # Sort by distance only if the score is significantly different
        # And no overlap is detected, check score instead
        should_sort_by_score = abs(a.score_potential - b.score_potential) > 0.1 or \
            ( a_start <= b_end and b_start <= a_end )

        if not should_sort_by_score:
            if a.distance < b.distance:
                return 1
            elif a.distance > b.distance:
                return -1
        return sort_by_score
        
    def compare_match_trees_for_selection(self, a: VirtualBufferMatch, b: VirtualBufferMatch) -> int:
        result = self.compare_match_trees_by_score(a, b)
        if result == 0:
            if a.distance < b.distance:
                return 1
            elif a.distance > b.distance:
                return -1
        return result

    def compare_match_trees_for_selfrepair(self, a: VirtualBufferMatch, b: VirtualBufferMatch) -> int:
        # Pick the one with the most direct matches
        direct_matches_a = [score for score in a.scores if score >= 0.9]
        direct_matches_b = [score for score in b.scores if score >= 0.9]

        if len(direct_matches_a) > len(direct_matches_b):
            return 1
        elif len(direct_matches_a) < len(direct_matches_b):
            return -1
        else:
            # If the self repair starts with a bad score, we want to choose
            # The one with the shortest amount of bad scores at the start
            bad_starting_scores_a = 0
            for score in a.scores:
                if score < CORRECTION_THRESHOLD:
                    bad_starting_scores_a += 1
                else:
                    break
            
            bad_starting_scores_b = 0
            for score in b.scores:
                if score < CORRECTION_THRESHOLD:
                    bad_starting_scores_b += 1
                else:
                    break

            if bad_starting_scores_a > bad_starting_scores_b:
                return -1
            elif bad_starting_scores_a < bad_starting_scores_b:
                return 1
            else:
                return self.compare_match_trees_by_score(a, b)

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

    def find_potential_sublists_for_words(self, token_list: VirtualBufferTokenList, match_calculation: VirtualBufferMatchCalculation, word_indices: List[int], max_sublist_size: int, verbose: bool = False) -> List[VirtualBufferTokenList]:
        sublists = []
        relative_left_index = -(word_indices[0] + ( max_sublist_size - match_calculation.length ) / 2)
        relative_right_index = relative_left_index + max_sublist_size


        # Only search within the viable range ( no cut off matches at the start and end of the token_list )
        # Due to multiple different fuzzy matches being possible, it isn't possible to do token skipping
        # Like in the Boyer–Moore string-search algorithm
        # But if we have exact matches that we need to filter out, we can do something similar to Boyer-Moore
        for token_list_index in range(word_indices[0], len(token_list.tokens)):
            if match_calculation.cache.should_skip_index(token_list.index + token_list_index):
                continue
            token_list_token = token_list.tokens[token_list_index]

            # Use a high threshold if we explore all branches, otherwise use a weighed threshold
            threshold = match_calculation.match_threshold
            if match_calculation.has_initial_branch_pruning():
                threshold = threshold * sum([match_calculation.weights[word_index] for word_index in word_indices])

            query_tokens = "".join([match_calculation.words[word_index] for word_index in word_indices])
            score = self.get_memoized_similarity_score(token_list_token.phrase.replace(" ", ""), query_tokens)
            single_score = score
            buffer_indices = [token_list_index]
            match_calculation.cache.cache_buffer_index_score(score, buffer_indices, token_list)
            is_multiple_query_match = len(word_indices) > 1

            query_words = [match_calculation.words[word_index] for word_index in word_indices]
            individual_scores = [0.0] if match_calculation.selfrepair else [self.get_memoized_similarity_score(word, token_list_token.phrase.replace(" ", "")) for word in query_words]

            # Add single combination
            if score >= threshold:
                if verbose:
                    print( "Score for " + query_tokens + " = " + token_list_token.phrase.replace(" ", "") + " " + ",".join([str(bufin) for bufin in buffer_indices]) + ": " + str(score) + " with weighted thresh:" + str(threshold), score >= threshold)

                # Only add a match branch for a combined query search if the combined search scores higher than individual scores
                if not is_multiple_query_match or max(individual_scores) < score:
                    match_calculation.append_starting_branch(word_indices, [token_list.index + index for index in buffer_indices], score)
            biggest_score = score

            # Add buffer combinations as well if we are matching with a single word
            if not is_multiple_query_match:
                query_word = query_words[0]
                # Combine forward
                if token_list_index + 1 < len(token_list.tokens):
                    phrases = [token_list_token.phrase, token_list.tokens[token_list_index + 1].phrase]
                    combined_score = self.get_memoized_similarity_score("".join(phrases).replace(" ", ""), query_tokens)
                    if (combined_score - combined_better_threshold ) > single_score and (combined_score - combined_better_threshold) >= threshold:
                        if token_list_index + 2 < len(token_list.tokens):
                            triple_phrases = [token_list_token.phrase, token_list.tokens[token_list_index + 1].phrase, token_list.tokens[token_list_index + 2].phrase]
                            triple_combined_score = self.get_memoized_similarity_score("".join(triple_phrases).replace(" ", ""), query_tokens)
                            if (triple_combined_score - combined_better_threshold) > combined_score:
                                buffer_indices = [token_list_index, token_list_index + 1, token_list_index + 2]
                                score = triple_combined_score
                                phrases = triple_phrases
                                match_calculation.cache.cache_buffer_index_score(score, buffer_indices, token_list)
                        if (combined_score - combined_better_threshold) > score:
                            buffer_indices = [token_list_index, token_list_index + 1]
                            score = combined_score
                            match_calculation.cache.cache_buffer_index_score(score, buffer_indices, token_list)
                        individual_scores = [0.0] if match_calculation.selfrepair else[self.get_memoized_similarity_score(query_word, word) for word in phrases]

                        # Add the combined match branch that matched the best
                        if combined_score >= threshold and combined_score > max(individual_scores):
                            if verbose:
                                print( "Score for forwards combined " + query_tokens + " = " + "".join(phrases).replace(" ", "") + " " + ",".join([str(bufin) for bufin in buffer_indices]) + ": " + str(combined_score) + " with weighted thresh:" + str(threshold), combined_score >= threshold)
                            match_calculation.append_starting_branch(word_indices, [token_list.index + index for index in buffer_indices], score)
                        biggest_score = max(score, biggest_score)

                # Combine backwards
                if token_list_index - 1 >= 0:
                    phrases = [token_list.tokens[token_list_index - 1].phrase, token_list_token.phrase]
                    combined_score = self.get_memoized_similarity_score("".join(phrases).replace(" ", ""), query_tokens)
                    if (combined_score - combined_better_threshold) > single_score and (combined_score - combined_better_threshold) >= threshold:
                        if token_list_index - 2 >= 0:
                            triple_phrases = [token_list.tokens[token_list_index - 2].phrase, token_list.tokens[token_list_index - 1].phrase, token_list_token.phrase]
                            triple_combined_score = self.get_memoized_similarity_score("".join(triple_phrases).replace(" ", ""), query_tokens)
                            if (triple_combined_score - combined_better_threshold) > combined_score:
                                buffer_indices = [token_list_index - 2, token_list_index - 1, token_list_index]
                                score = triple_combined_score
                                match_calculation.cache.cache_buffer_index_score(triple_combined_score, buffer_indices, token_list)
                                phrases = triple_phrases
                        if (combined_score - combined_better_threshold) > score:
                            buffer_indices = [token_list_index - 1, token_list_index]
                            score = combined_score
                            match_calculation.cache.cache_buffer_index_score(score, buffer_indices, token_list)
                        individual_scores = [0.0] if match_calculation.selfrepair else [self.get_memoized_similarity_score(query_word, word) for word in phrases]

                        # Add the combined match branch that matched the best
                        if combined_score >= threshold and combined_score > max(individual_scores):
                            if verbose:
                                print( "Score for backwards combined " + query_tokens + " = " + "".join(phrases).replace(" ", "") + " " + ",".join([str(bufin) for bufin in buffer_indices]) + ": " + str(combined_score) + " with weighted thresh:" + str(threshold), combined_score >= threshold)
                            match_calculation.append_starting_branch(word_indices, [token_list.index + index for index in buffer_indices], score)            
                        biggest_score = max(score, biggest_score)

            has_starting_match = biggest_score >= threshold
            if has_starting_match:
                starting_index = max(0, round(token_list_index + relative_left_index - 1))
                ending_index = min(len(token_list.tokens), round(token_list_index + relative_right_index))
                sublist = token_list.get_sublist(starting_index, ending_index)
                if (len(sublist.tokens) > 0):
                    sublists.append(sublist)
                elif verbose:
                    print( query_tokens, "RESULTED IN EMPTY sublist!")

        return sublists, match_calculation

    def simplify_sublists(self, sublists: List[VirtualBufferTokenList]) -> List[VirtualBufferTokenList]:
        # Sort by index so it is easier to merge by index later
        sublists = list(set(sublists))
        sublists.sort(key=lambda x: x.index)

        merged_token_lists = []
        current_sublist = None
        for sublist in sublists:
            if current_sublist is not None:

                # Merge and continue on overlap
                if self.can_merge_token_lists(current_sublist, sublist):
                    current_sublist = self.merge_token_lists(current_sublist, sublist)
                    continue

                # Append and set the current sublist
                else:
                    merged_token_lists.append(current_sublist)
            current_sublist = sublist

        if current_sublist is not None:
            merged_token_lists.append(current_sublist)
        return merged_token_lists

    def can_merge_token_lists(self, a: VirtualBufferTokenList, b: VirtualBufferTokenList) -> bool:
        return a.index <= b.end_index and b.index <= a.end_index

    def merge_token_lists(self, a: VirtualBufferTokenList, b: VirtualBufferTokenList) -> VirtualBufferTokenList:
        # Complete overlap just returns the overlapping token_list
        if (a.index <= b.index and a.end_index >= b.end_index):
            return a
        elif (b.index <= a.index and b.end_index >= a.end_index):
            return b

        starting_token_list = a if a.index < b.index else b
        ending_token_list = b if a.index < b.index else a

        combined_tokens = []
        combined_tokens.extend(starting_token_list.tokens)
        if ending_token_list.end_index > starting_token_list.end_index:
            combined_tokens.extend(ending_token_list.tokens[-(ending_token_list.end_index - starting_token_list.end_index):])

        return VirtualBufferTokenList(starting_token_list.index, combined_tokens)

    def find_self_repair_match(self, virtual_buffer, phrases: List[str], verbose: bool = False) -> VirtualBufferMatch:
        # Do not allow punctuation to activate self repair
        punctuation_phrases = []
        for phrase in phrases:
            normalized_phrase = phrase.replace("\n", ".").replace(" ", "")
            if normalized_phrase.startswith((",", ".", "!", "?")):
                break
            elif normalized_phrase.endswith((",", ".", "!", "?")):
                if len(normalized_phrase) > 1:
                    punctuation_phrases.append(phrase)
                break
            else:
                punctuation_phrases.append(phrase)
        phrases = punctuation_phrases

        # We don't do any self repair checking with selected text, only in free-flow text
        if not virtual_buffer.is_selecting() and len(phrases) > 0:
            current_index = virtual_buffer.determine_token_index()

            if current_index[0] != -1 and current_index[1] != -1:
                phrases_to_use = [phrase for phrase in phrases]
                return self.find_best_match_by_phrases_for_self_repair(virtual_buffer, phrases_to_use, CORRECTION_THRESHOLD, verbose=verbose)

        return None

    def find_best_match_by_phrases_for_self_repair(self, virtual_buffer, phrases: List[str], match_threshold: float = CORRECTION_THRESHOLD, verbose=False):
        rightmost_token_index = virtual_buffer.determine_rightmost_token_index()[0]
        starting_index = max(0, rightmost_token_index + 1 - (len(phrases) * 3))
        ending_index = rightmost_token_index + 1

        # We consider punctuations as statements that the user cannot match with
        # Because sentences can end in the same word as a word used for the new sentence
        tokens_from_last_punctuation = []
        for token_index in range(starting_index, ending_index):
            token = virtual_buffer.tokens[token_index]
            if token.text.replace("\n", ".").replace(" ", "").endswith((",", ".", "!", "?")):
                starting_index = token_index + 1

        # Skip checking if through punctuation the self repair got broken
        if starting_index >= ending_index:
            return None

        token_list = VirtualBufferTokenList(starting_index, virtual_buffer.tokens[starting_index:ending_index])

        match_calculation = self.generate_match_calculation(phrases, match_threshold, purpose="selfrepair")
        match_calculation.cache.index_token_list(token_list)
        starting_match = VirtualBufferMatch([], [], [], [], [], match_calculation.max_score, 0)
        query = match_calculation.words
        buffer = [token.phrase for token in token_list.tokens]
        matches = []

        # Because self repair only activates if the start matches, we only use the first (combined) tokens for matching
        # For performance improvements without impacting accuracy
        match_calculation = self.fill_starting_branches_for_self_repair(token_list, match_threshold, match_calculation, verbose)
        starting_branches = match_calculation.get_starting_branches(token_list)
        if verbose:
            print( "    - FOUND ROOTS FOR SELF-REPAIR" )
            print( match_calculation.starting_branches )
        
        for branch in starting_branches:
            combined_weight = sum([match_calculation.weights[index] for index in branch.query_indices])
            if branch.score_potential >= match_calculation.match_threshold:
                match_branch = starting_match.clone()
                match_branch.query_indices.append(branch.query_indices)
                match_branch.query.extend([query[index] for index in branch.query_indices])
                normalized_buffer_indices = [index - token_list.index for index in branch.buffer_indices]
                match_branch.buffer_indices.append(normalized_buffer_indices)
                match_branch.buffer.extend([buffer[buffer_index] for buffer_index in normalized_buffer_indices])
                match_branch.scores.append(branch.score)
                match_branch.reduce_potential(match_calculation.max_score, branch.score, combined_weight)

                # Expand backwards, because sometimes we have matches that have direct matches not on the first tokens
                match_trees = [match_branch]
                if match_branch.can_expand_backward(token_list):
                    can_expand_backward_count = 1
                    while can_expand_backward_count != 0:
                        expanded_match_trees = []
                        for match_tree in match_trees:
                            backward_expanded_match_tree, match_calculation = self.expand_match_tree_backward(match_tree, match_calculation, token_list, verbose=verbose)
                            expanded_match_trees.extend(backward_expanded_match_tree)
                        can_expand_backward_count = sum([expanded_match_tree.can_expand_backward(token_list) for expanded_match_tree in expanded_match_trees])
                        match_trees = list(set(expanded_match_trees))

                # Expand forwards until it is no longer possible within the token_list
                # Because the query can contain words beyond the token_list that will be used for insertion
                if match_branch.can_expand_forward(match_calculation, token_list):
                    can_expand_forward_count = 1
                    while can_expand_forward_count != 0:
                        expanded_match_trees = []
                        for match_tree in match_trees:
                            forward_expanded_match_tree, match_calculation = self.expand_match_tree_forward(match_tree, match_calculation, token_list, verbose=verbose)
                            expanded_match_trees.extend(forward_expanded_match_tree)
                        can_expand_forward_count = sum([expanded_match_tree.can_expand_forward(match_calculation, token_list) for expanded_match_tree in expanded_match_trees])
                        match_trees = list(set(expanded_match_trees))

                match_trees = self.filter_expanded_match_trees(match_trees, match_calculation, verbose=verbose)

                if verbose:
                    print( "FOUND MATCH TREES FOR SELF-REPAIR", match_trees )

                # Filter out all the match trees that don't connect with the end of the token_list
                for match_tree in match_trees:
                    match_tree.to_global_index(token_list)
                    if match_tree.buffer_indices[-1][-1] + 1 >= token_list.index + token_list.length:

                        # When the first word of the match isn't exact it is not a self repair
                        first_token_matches = match_tree.scores[0] >= SELECTION_THRESHOLD

                        # Check if the found match is a direct continuation of the uttered word
                        if not first_token_matches:
                            starting_buffer_length = len(match_tree.buffer_indices[0])
                            buffer_words = ""
                            for buffer_index, buffer_word in enumerate(match_tree.buffer):
                                buffer_words += buffer_word
                                if buffer_index + 1 >= starting_buffer_length:
                                    break

                            starting_query_length = len(match_tree.query_indices[0])
                            query_words = ""
                            for query_index, query_word in enumerate(match_tree.query):
                                query_words += query_word
                                if query_index + 1 >= starting_query_length:
                                    break

                            is_continuation = query_words.startswith(buffer_words)
                            first_token_matches = is_continuation

                        second_token_matches = len(match_tree.scores) > 1 and not first_token_matches and \
                            match_tree.scores[1] >= SELECTION_THRESHOLD and match_tree.score_potential > CORRECTION_THRESHOLD

                        has_skip_before_end = len(match_tree.scores) > 2 and match_tree.scores[-2] == 0
                        final_combined_tokens_bad = ( has_skip_before_end or len(match_tree.query_indices[-1]) > 1 or len(match_tree.buffer_indices[-1]) > 1 ) and \
                            match_tree.scores[-1] < CORRECTION_THRESHOLD

                        # If it is only the first token that doesn't match, but the rest is very confident
                        # We expect we need to replace the first item
                        first_token_doesnt_match_but_others_high = match_tree.scores[0] < CORRECTION_THRESHOLD and \
                            match_tree.score_potential > SELECTION_THRESHOLD
                        if not final_combined_tokens_bad and (first_token_matches or first_token_doesnt_match_but_others_high or second_token_matches):
                            if verbose:
                                print("FOUND SELF-REPAIR MATCH", match_tree)
                                print("Final combined tokens bad", final_combined_tokens_bad, "First token matches", first_token_matches, "second token matches", second_token_matches, " or rest matches well", first_token_doesnt_match_but_others_high)
                            matches.append(match_tree)
                        elif verbose:
                            print("SKIPPING MATCH TREE", match_tree)
                            print("Final combined tokens bad", final_combined_tokens_bad, "First token matches", first_token_matches, "second token matches", second_token_matches, " or rest matches well", first_token_doesnt_match_but_others_high)
                    elif verbose:
                        print( "SKIPPING MATCH TREE BECAUSE IT DOES NOT REACH THE END", match_tree)

        # Sort matches by longest selection
        matches.sort(key = cmp_to_key(self.compare_match_trees_for_selfrepair), reverse=True)
        if verbose:
            print("TOTAL MATCHES", matches)
        return None if len(matches) == 0 else matches[0]

    def fill_starting_branches_for_self_repair(self, token_list: VirtualBufferTokenList, starting_threshold: float, match_calculation: VirtualBufferMatchCalculation, verbose = False) -> VirtualBufferMatchCalculation:
        for query_indices in match_calculation.get_possible_branches():
            threshold = starting_threshold

            query_tokens = "".join([match_calculation.words[word_index] for word_index in query_indices])
            for token_list_index in range(token_list.length - 1, -1, -1):
                token_list_token = token_list.tokens[token_list_index]
                score = self.get_memoized_similarity_score(token_list_token.phrase.replace(" ", ""), query_tokens)
                single_score = score
                buffer_indices = [token_list_index]
                match_calculation.cache.cache_buffer_index_score(score, buffer_indices, token_list)

                # Add buffer combinations as well if we are matching with a single word
                if len(query_indices) == 1:
                    # Combine backward
                    if token_list_index - 1 >= 0:
                        # Make sure we check if the combined word is both worth more than if the words were matched separately
                        checking_single_score = max(single_score, self.get_memoized_similarity_score(token_list.tokens[token_list_index - 1].phrase.replace(" ", ""), query_tokens))

                        phrases = [token_list.tokens[token_list_index - 1].phrase, token_list_token.phrase]
                        combined_score = self.get_memoized_similarity_score("".join(phrases).replace(" ", ""), query_tokens)
                        if combined_score > checking_single_score:
                            if token_list_index - 2 >= 0:
                                phrases.insert(0, token_list.tokens[token_list_index - 2].phrase)
                                triple_combined_score = self.get_memoized_similarity_score("".join(phrases).replace(" ", ""), query_tokens)
                                if triple_combined_score > combined_score and triple_combined_score > score:
                                    buffer_indices = [token_list_index - 2, token_list_index - 1, token_list_index]
                                    score = triple_combined_score
                            if combined_score > score:
                                buffer_indices = [token_list_index - 1, token_list_index]
                                score = combined_score
                            match_calculation.cache.cache_buffer_index_score(score, buffer_indices, token_list)

                has_starting_match = score >= threshold
                if verbose:
                    print( "Score for " + query_tokens + " = " + token_list_token.phrase.replace(" ", "") + ": " + str(score) + " with weighted thresh:" + str(threshold), score >= threshold)

                # Filter exact buffer index matches that don't score as high
                if has_starting_match:
                    matched_buffer_indices = [token_list.index + index for index in buffer_indices]
                    match_calculation.append_starting_branch(query_indices, matched_buffer_indices, score)

        return match_calculation

    def find_best_match_by_phrases(self, virtual_buffer, phrases: List[str], match_threshold: float = SELECTION_THRESHOLD, next_occurrence: bool = True, selecting: bool = False, for_correction: bool = False, verbose: bool = False) -> (List[VirtualBufferToken], VirtualBufferMatch):
        matches = self.find_top_three_matches_in_token_list(virtual_buffer, phrases, match_threshold, selecting, for_correction, verbose)

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
        # Quick memoized look up
        if word_a in self.similarity_token_list and word_b in self.similarity_token_list[word_a]:
            return self.similarity_token_list[word_a][word_b]
        elif word_b in self.similarity_token_list and word_a in self.similarity_token_list[word_b]:
            return self.similarity_token_list[word_b][word_a]
        
        # Generate single cache entry using calculated similarity score
        if word_a not in self.similarity_token_list:
            self.similarity_token_list[word_a] = {}

        self.similarity_token_list[word_a][word_b] = self.phonetic_search.phonetic_similarity_score(word_a, word_b)
        return self.similarity_token_list[word_a][word_b]