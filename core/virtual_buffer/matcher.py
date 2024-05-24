from ..phonetics.phonetics import PhoneticSearch
from .typing import VirtualBufferToken, VirtualBufferTokenMatch, VirtualBufferMatchCalculation, VirtualBufferMatchMatrix
import re
from typing import List, Dict
import math

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
    
    # Generate a match calculation based on the words to search for weighted by syllable count
    def generate_match_calculation(self, query_words: List[str], threshold: float = 1, max_score_per_word: float = 3) -> VirtualBufferMatchCalculation:
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
            sub_matrices.extend(self.find_potential_submatrices_for_word(matrix, match_calculation, word_index, max_submatrix_size))

        sub_matrices = self.simplify_submatrices(sub_matrices)

        # TODO SORT BY DISTANCE ?

        return sub_matrices
    
    def find_potential_submatrices_for_word(self, matrix: VirtualBufferMatchMatrix, match_calculation: VirtualBufferMatchCalculation, word_index: int, max_submatrix_size: int) -> List[VirtualBufferMatchMatrix]:
        submatrices = []
        relative_left_index = -(word_index + ( max_submatrix_size - match_calculation.length ) / 2)
        relative_right_index = relative_left_index + max_submatrix_size

        # Only search within the viable range ( no cut off matches at the start and end of the matrix )
        # Due to multiple different fuzzy matches being possible, it isn't possible to do token skipping
        # Like in the Boyer–Moore string-search algorithm 
        for matrix_index in range(word_index, (len(matrix.tokens) - 1) - (match_calculation.length - 1 - word_index)):
            matrix_token = matrix.tokens[matrix_index]
            threshold = match_calculation.match_threshold * match_calculation.weights[word_index]

            # TODO DYNAMIC SCORE CALCULATION BASED ON CORRECTION VS SELECTION?
            score = self.get_memoized_similarity_score(matrix_token.phrase, match_calculation.words[word_index])

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
                    matches = self.find_matches_by_phrases(tokens_from_last_punctuation, phrases, 1, 'most_direct_matches')
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
    
    def find_best_match_by_phrases(self, virtual_buffer, phrases: List[str], match_threshold: float = 3, next_occurrence: bool = True, selecting: bool = False, for_correction: bool = False, verbose: bool = False) -> List[VirtualBufferToken]:
        matches = self.find_matches_by_phrases( virtual_buffer.tokens, phrases, match_threshold, verbose=verbose)
        if verbose:
            print( "MATCHES!", matches )

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
            if score >= 2:
                exact_matching_tokens.append((index, token))
            elif score > 0.8:
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