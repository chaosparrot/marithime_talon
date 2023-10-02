from ..phonetics.phonetics import PhoneticSearch
from .input_history_typing import InputHistoryEvent
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
    
    def find_best_match_by_phrases(self, input_history, phrases: List[str], match_threshold: float = 3, next_occurrence: bool = True, selecting: bool = False) -> List[InputHistoryEvent]:
        matches = self.find_matches_by_phrases( input_history, phrases, match_threshold)
        if len(matches) > 0:
            best_match_events = []
            for index in matches[0]['indices']:
                best_match_events.append(input_history.input_history[index])

            return best_match_events
        else:
            return None

    def find_matches_by_phrases(self, input_history, phrases: List[str], match_threshold: float = 3) -> List[Dict]:
        matrix = self.generate_similarity_matrix(input_history, phrases)
        matches = []
        for phrase_index, phrase in enumerate(phrases):
            current_match = None
            for index, score in enumerate(matrix[phrase]):
                if score >= match_threshold:
                    current_match = {
                        "starts": phrase_index,
                        "indices": [index],
                        "score": score,
                        "distance": 0
                    }
                    # TODO ADD CONSEQUTIVE INDICES
                
                if current_match != None:
                    matches.append(current_match)
                    current_match = None

        sorted(matches, key=lambda match: match['score'], reverse=True)
        return matches

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

    def generate_similarity_matrix(self, input_history, phrases: List[str]) -> Dict[str, List[float]]:
        matrix = {}
        for phrase in phrases:
            if phrase in matrix:
                continue
            matrix[phrase] = []
            for event in input_history.input_history:
                similarity_key = phrase + "." + event.phrase
                if similarity_key not in self.similarity_matrix:
                    # Keep a list of known results to make it faster to generate the matrix in the future
                    self.similarity_matrix[similarity_key] = self.phonetic_search.phonetic_similarity_score(event.phrase, phrase)
                
                matrix[phrase].append(self.similarity_matrix[similarity_key])
        return matrix