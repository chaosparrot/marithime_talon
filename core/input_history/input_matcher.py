from ..phonetics.phonetics import PhoneticSearch
from .input_history_typing import InputHistoryEvent, InputEventMatch
import re
from typing import List, Dict

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", ' ', text).replace("\n", " ")

# Class to find the best matches inside of input histories
class InputMatcher:

    phonetic_search: PhoneticSearch = None
    similarity_matrix: Dict[str, float] = None

    def __init__(self, phonetic_search: PhoneticSearch):
        self.phonetic_search = phonetic_search
        self.similarity_matrix = {}

    def is_phrase_selected(self, input_history, phrase: str) -> bool:
        if input_history.is_selecting():
            selection = input_history.cursor_position_tracker.get_selection_text()
            return self.phonetic_search.phonetic_similarity_score(normalize_text(selection).replace(" ", ''), phrase) >= 2
        return False

    def has_matching_phrase(self, input_history, phrase: str) -> bool:
        score = 0
        for event in input_history.input_history:
            score = self.phonetic_search.phonetic_similarity_score(phrase, event.phrase)
            if score >= 1:
                return True

        return False
    
    def find_self_repair_match(self, input_history, phrases: List[str]) -> InputEventMatch:
        # Do not allow punctuation to activate self repair
        phrases = [phrase for phrase in phrases if not phrase.replace(" ", "").endswith((",", ".", "!", "?"))]

        # We don't do any self repair checking with selected text, only in free-flow text
        if not input_history.is_selecting():
            current_index = input_history.determine_input_index()

            if current_index[0] != -1 and current_index[1] != -1:
                earliest_index_for_look_behind = max(0, current_index[0] - len(phrases))
                events_behind = input_history.input_history[earliest_index_for_look_behind:current_index[0] + 1]

                # We consider punctuations as statements that the user cannot match with
                events_from_last_punctuation = []
                for event in events_behind:
                    if not event.text.replace("\n", ".").replace(" ", "").endswith((",", ".", "!", "?")):
                        events_from_last_punctuation.append(event)
                    else:
                        events_from_last_punctuation = []

                if len(events_from_last_punctuation) > 0:
                    matches = self.find_matches_by_phrases(events_from_last_punctuation, phrases, 1, 'most_direct_matches')

                    # Get the match with the most matches, closest to the end
                    # Make sure we adhere to 'reasonable' self repair of about 5 words back max
                    for best_match in matches:

                        # Make sure we normalize the index to our best knowledge
                        index_offset = earliest_index_for_look_behind
                        best_match.starts += index_offset
                        best_match.indices = [index_offset + index for index in best_match.indices]

                        #print( best_match )

                        # When the final index does not align with the current index, it won't be a self repair replacement
                        if best_match.indices[-1] != current_index[0]:
                            #print( "NOT CONNECTED TO END")
                            continue
                            
                        # When we have unmatched new words coming before the match, it won't be a self repair replacement
                        elif best_match.starts - index_offset - best_match.indices[-1] > 0:
                            #print( "NOT CONNECTED TO START OF PHRASE")
                            continue

                        # If the average score of all the matching parts is lower than 1, we can assume we haven't had a proper match for self repair                        
                        elif best_match.score / len(best_match.indices) + best_match.distance < 1:
                            #print( "BAD SCORE")
                            continue

                        else:
                            return best_match
        
        return None
    
    def find_best_match_by_phrases(self, input_history, phrases: List[str], match_threshold: float = 3, next_occurrence: bool = True, selecting: bool = False) -> List[InputHistoryEvent]:
        matches = self.find_matches_by_phrases( input_history.input_history, phrases, match_threshold)
        if len(matches) > 0:
            best_match = matches[0]

            current_index = input_history.determine_input_index()
            if current_index[0] != -1:
                # Get the closest item to the cursor in the case of multiple matches
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
            
            best_match_events = []
            for index in best_match.indices:
                best_match_events.append(input_history.input_history[index])

            return best_match_events
        else:
            return None

    def find_matches_by_phrases(self, input_history_events: List[InputHistoryEvent], phrases: List[str], match_threshold: float = 2, strategy='highest_score') -> List[InputEventMatch]:
        matrix = self.generate_similarity_matrix(input_history_events, phrases)

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
                    current_match = InputEventMatch(phrase_index, [index], [[phrase], [input_history_events[index].text]], score, [score])

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
                            current_match.comparisons[1].append(input_history_events[next_index[0]].phrase)
                            current_match.distance += next_index[0] - current_word_index

                            # Add the score of the missed phrases in between the matches
                            while missed_phrase_length > 0:
                                # Make sure we only count item scores in between words rather than skipped words entirely
                                if next_index[0] - missed_phrase_length > current_match.indices[-1]:
                                    current_match.distance -= 1
                                    current_match.indices.append(next_index[0] - missed_phrase_length)
                                    added_score = matrix[phrases[current_phrase_index - missed_phrase_length]][next_index[0] - missed_phrase_length]
                                    current_match.comparisons[0].append(phrases[current_phrase_index - missed_phrase_length])
                                    current_match.comparisons[1].append(input_history_events[next_index[0]].phrase)
                                    current_match.score += added_score
                                    current_match.scores.append( added_score )

                                missed_phrase_length -= 1

                            current_match.indices.append(next_index[0])
                            current_match.score += next_index[1]
                            current_match.scores.append( next_index[1] )
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
                        current_phrase_index = phrase_index
                        prepend_index = -1
                        for previous_phrase_index in range(0 - phrase_index, 0):
                            if index + previous_phrase_index >= 0:
                                previous_indices.append(index + previous_phrase_index)
                                previous_phrase = phrases[phrase_index + previous_phrase_index]
                                new_previous_score = matrix[previous_phrase][index + previous_phrase_index]
                                previous_score += new_previous_score
                                current_match.comparisons[0].insert(prepend_index, previous_phrase)
                                current_match.comparisons[1].insert(prepend_index, input_history_events[index + previous_phrase_index].phrase)
                                current_match.scores.insert(prepend_index, new_previous_score)
                            prepend_index += 1
                        
                        previous_indices.extend(current_match.indices)
                        current_match.indices = previous_indices
                        current_match.score += previous_score

                    # Add score of missing matches at the end
                    if current_match != None and last_matching_index > -1 and len(missing_end_indices) > 0:
                        next_score = 0
                        next_indices = []
                        for next_index in missing_end_indices:
                            last_matching_index += 1
                            if last_matching_index < len(input_history_events):
                                next_phrase = phrases[next_index]
                                next_indices.append(next_index)
                                new_next_score = matrix[next_phrase][last_matching_index]
                                next_score += new_next_score
                                current_match.scores.append(new_next_score)
                                current_match.comparisons[0].append(next_phrase)
                                current_match.comparisons[1].append(input_history_events[last_matching_index].phrase)
                        current_match.indices.extend(next_indices)
                        current_match.score += next_score

                # Prune out matches below the average score threshold
                # And with a distance between words that is larger than forgetting a word in between every word
                if current_match != None and (current_match.distance <= len(phrases) - 1) and strategy == 'most_direct_matches':
                    matches.append(current_match)
                    current_match = None
                elif current_match != None and (current_match.score / len(phrases)) >= match_threshold and (current_match.distance <= len(phrases) - 1):
                    matches.append(current_match)
                    current_match = None

        if strategy == 'highest_score':
            matches = sorted(matches, key=lambda match: match.score, reverse=True)

        # Place the highest direct matches on top
        elif strategy == 'most_direct_matches':
            matches = sorted(matches, key=lambda match: len(list(filter(lambda x: x >= 1, match.scores))), reverse=True)
        return matches
    
    def match_next_in_phrases(self, matrix, matrix_index: int, phrases: List[str], phrase_index: int, match_threshold: float):
        phrase = phrases[phrase_index]

        for i in range(matrix_index, len(matrix[phrase])):
            score = matrix[phrase][i]
            if score >= match_threshold:
                return (i, score)
        
        return (-1, -1)

    def find_single_match_by_phrase(self, input_history, phrase: str, char_position: int = -1, next_occurrence: bool = True, selecting: bool = False) -> InputHistoryEvent:
        exact_matching_events: List[(int, InputHistoryEvent)] = []
        fuzzy_matching_events: List[(int, InputHistoryEvent, float)] = []

        for index, event in enumerate(input_history.input_history):
            score = self.phonetic_search.phonetic_similarity_score(phrase, event.phrase)
            if score >= 2:
                exact_matching_events.append((index, event))
            elif score > 0.8:
                fuzzy_matching_events.append((index, event, score))

        # If we have no valid matches or valid cursors, we cannot find the phrase
        cursor_index = input_history.cursor_position_tracker.get_cursor_index()
        if (len(exact_matching_events) + len(fuzzy_matching_events) == 0) or cursor_index[0] < 0:
            return None
        
        # Get the first exact match
        if len(exact_matching_events) == 1:
            return exact_matching_events[0][1]
        
        # Get a fuzzy match if it is the only match
        elif len(exact_matching_events) == 0 and len(fuzzy_matching_events) == 1:
            return fuzzy_matching_events[0][1]
        else:
            input_index = input_history.determine_input_index()
            current_event = input_history.input_history[input_index[0]]
            text_length = len(current_event.text.replace("\n", ""))
            current_phrase_similar = self.phonetic_search.phonetic_similarity_score(phrase, current_event.phrase) >= 1

            if input_index[1] == text_length and not current_phrase_similar:
                # Move to the next event if that event matches our phrase
                next_event_phrase = "" if input_index[0] + 1 >= len(input_history.input_history) else input_history.input_history[input_index[0] + 1].phrase 
                if self.phonetic_search.phonetic_similarity_score(phrase, next_event_phrase) >= 1:
                    current_event = input_history.input_history[input_index[0] + 1]
                    input_index = (input_index[0] + 1, 0)
                    current_phrase_similar = True

            # If the current event is the event we are looking for, make sure to check if we should cycle through it
            if current_phrase_similar:    
                # If the cursor is in the middle of the event we are trying to find, make sure we don't look further                
                if input_index[1] > 0 and input_index[1] < text_length:
                    return current_event
                
                # If the cursor is on the opposite end of the event we are trying to find, make sure we don't look further
                # Unless we are actively selecting new ocurrences
                elif not (selecting and next_occurrence) and ( (input_index[1] == 0 and char_position == -1) or (input_index[1] == text_length and char_position >= 0) ):
                    return current_event
                
            # Loop through the occurrences one by one, starting back at the end if we have reached the first event
            if next_occurrence:
                matched_event = None
                for event in exact_matching_events:
                    if event[0] < input_index[0]:
                        matched_event = event[1]
                    elif (input_history.last_action_type == "insert" or input_history.last_action_type == "remove") and event[0] == input_index[0]:
                        matched_event = event[1]
                
                if matched_event is None:
                    matched_event = exact_matching_events[-1][1]

            # Just get the nearest matching event to the cursor as this is most likely the one we were after
            # Not all cases have been properly tested for this
            else:
                distance_to_event = 1000000
                current_event = input_history.input_history[input_index[0]]

                matched_event = None
                for event_index, event in exact_matching_events:
                    line_distance = abs(event.line_index - current_event.line_index) * 10000
                    distance_from_event_end = abs(event.index_from_line_end) + line_distance
                    distance_from_event_start = abs(event.index_from_line_end + len(event.text.replace("\n", ""))) + line_distance
                    
                    if abs(distance_from_event_end - current_event.index_from_line_end) < distance_to_event:
                        matched_event = event
                        distance_to_event = abs(distance_from_event_end - current_event.index_from_line_end)
                    
                    elif abs(distance_from_event_start - current_event.index_from_line_end) < distance_to_event:
                        matched_event = event
                        distance_to_event = abs(distance_from_event_start - current_event.index_from_line_end)

                if matched_event is None:
                    matched_event = exact_matching_events[-1]

            return matched_event

    def generate_similarity_matrix(self, input_history_events: List[InputHistoryEvent], phrases: List[str]) -> Dict[str, List[float]]:
        matrix = {}
        for phrase in phrases:
            if phrase in matrix:
                continue
            matrix[phrase] = []
            for event in input_history_events:
                similarity_key = phrase + "." + event.phrase
                if similarity_key not in self.similarity_matrix:

                    # Keep a list of known results to make it faster to generate the matrix in the future
                    self.similarity_matrix[similarity_key] = self.phonetic_search.phonetic_similarity_score(event.phrase, phrase)
                
                matrix[phrase].append(self.similarity_matrix[similarity_key])
        return matrix