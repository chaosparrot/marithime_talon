from talon import actions, cron, settings
from .typing import InputFix, InputMutation, VirtualBufferToken, CORRECTION_THRESHOLD, SELECTION_THRESHOLD
from .buffer import VirtualBuffer
import re
import time
from typing import List, Dict, Tuple
import os
import csv
from pathlib import Path
from dataclasses import fields
from ..phonetics.detection import EXACT_MATCH
from ..phonetics.actions import PhoneticSearch, phonetic_search

SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "settings")

# Thresholds when a fix should be done automatically
CONTEXT_THRESHOLD_MOST = 1
CONTEXT_THRESHOLD_SINGLE = 3
CONTEXT_THRESHOLD_NONE = 6

# Class to automatically fix words depending on the context and previous fixes
class InputFixer:
    phonetic_search: PhoneticSearch
    path_prefix: str = ""
    language: str = "en"
    done_fixes: Dict[str, List[InputFix]] = {}
    known_fixes: Dict[str, List[InputFix]] = {}
    verbose: bool = False
    testing: bool = False

    poll_buffer_commit_seconds = 0
    buffer_committing_job = None
    buffer: List[InputMutation] = []

    def __init__(self, language: str = "en", engine: str = "", path_prefix: str = str(Path(SETTINGS_DIR) / "cache"), poll_buffer_seconds: int = 30, verbose = False, testing = False):
        self.language = language
        self.engine = engine
        self.path_prefix = path_prefix
        self.buffer = []
        self.done_fixes = {}
        self.known_fixes = {}
        self.phonetic_search = phonetic_search
        self.verbose = verbose
        self.load_fixes(language, engine)
        self.poll_buffer_seconds = poll_buffer_seconds
        self.testing = testing

    def load_fixes(self, language: str, engine: str):
        if language and engine and self.path_prefix :
            self.language = language
            self.engine = engine
            self.known_fixes = {}

            fix_file_path = self.get_current_fix_file_path()

            # Create an initial fix file if it does not exist for the engine / language combination yet
            if not os.path.exists( fix_file_path ):

                # Create cache folder if the path does not exist
                if not os.path.exists(self.path_prefix):
                    os.makedirs(self.path_prefix)
                
                with open(fix_file_path, 'w') as new_file:
                    writer = csv.writer(new_file, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\n")
                    writer.writerow([field.name for field in fields(InputFix) if field.name != "key"])

            # Read the fixes from the known CSV file
            with open(fix_file_path, 'r') as fix_file:
                file = csv.DictReader(fix_file, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\n")
                for row in file:
                    if "from_text" in row:
                        if row["from_text"].lower() not in self.known_fixes:
                            self.known_fixes[row["from_text"]] = []
                        known_fix = InputFix(self.get_key(row["from_text"], row["to_text"]), row["from_text"], row["to_text"], int(row["amount"]), row["previous"], row["next"])
                        self.known_fixes[row["from_text"].lower()].append(known_fix)

    # Find fixes for lists of words
    # Can replace
    # - One word into one word
    # - Two words into a single word
    # - One word into multiple words
    def automatic_fix_list(self, words: List[str], previous: str, next: str) -> List[str]:
        used_indices = []
        new_words = []
        for index, word in enumerate(words):
            if index in used_indices:
                continue

            previous_word = new_words[-1] if len(new_words) > 0 else re.sub(r"[^\w]", '', previous.strip().split()[-1]) if previous != "" else ""
            next_combine_word = re.sub(r"[^\w]", '', words[index + 1]).lower() if index + 1 < len(words) else None
            next_word = next_combine_word if next_combine_word is not None else re.sub(r"[^\w]", '', next.strip().split()[0]) if next != "" else ""
            follow_up_word = re.sub(r"[^\w]", '', words[index + 2]).lower() if index + 2 < len(words) else ""
            unformatted_word = re.sub(r"[^\w]", '', word).lower()

            # Use the fix but do not keep track of the automatic fixes as it would give too much weight over time
            two_words_fix = None if next_combine_word is None else self.find_fix(unformatted_word + " " + next_combine_word, previous_word, follow_up_word)
            if two_words_fix:
                # Use the fix to replace two words into one word
                new_words.extend(two_words_fix.to_text.split())
                used_indices.append(index)
                used_indices.append(index + 1)
            else:
                # Use the fix to replace one word into one or more words
                single_word_fix = self.find_fix(word, previous_word, next_word)
                if single_word_fix:
                    new_words.extend(single_word_fix.to_text.split())
                # No known fixes - Keep the same
                else:
                    new_words.append(word)
                used_indices.append(index)
        return new_words

    def automatic_fix(self, text: str, previous: str, next: str) -> str:
        # Fixing isn't allowed - just return the text
        if not self.is_fixing_allowed():
            return text

        fix = self.find_fix(text, previous, next)
        if fix:
            # Use the fix but do not keep track of the automatic fixes as it would give too much weight over time
            return fix.to_text
        # No known fixes - Keep the same
        else:
            return text

    # Detect if we are doing a phonetic correction
    # A phonetic correction when repeated should clear the previous item and then
    # Insert the changed item
    def determine_phonetic_fixes(self, virtual_buffer: VirtualBuffer, tokens: List[VirtualBufferToken]) -> List[str]:
        fixed_phrases = []

        # When selecting, we know if we have a phonetic fix if the selected text
        # Contains all the items that need to be corrected ( 'where' has homophones to correct etc. )
        if virtual_buffer.is_selecting() or len(virtual_buffer.virtual_selection) > 0:
            phonetic_fix_count = 0
            selected_token_count = 0
            if virtual_buffer.is_phrase_selected("".join([token.phrase for token in tokens])):
                for token in tokens:
                    known_fixes_for_item = virtual_buffer.matcher.phonetic_search.get_known_fixes(token.phrase)
                    phonetic_fix_count += len(known_fixes_for_item)
                    selected_token_count += 1
            if phonetic_fix_count > 0 and selected_token_count == len(tokens):
                fixed_phrases = tokens

        # We can cycle through the inserted words
        else:
            phonetic_fix_count = 0
            for token in tokens:
                known_fixes_for_item = virtual_buffer.matcher.phonetic_search.get_known_fixes(token.phrase)
                phonetic_fix_count += len(known_fixes_for_item)
            if phonetic_fix_count > 0:
                fixed_phrases = tokens
        return fixed_phrases

    # Get a count of all the fix cycles that we can get from the text
    def determine_cycles_for_words(self, words: List[str], starting_words: List[str] = None) -> List[List[str]]:
        word_cycles = []
        for word_index, word in enumerate(words):
            fixes = self.phonetic_search.get_known_fixes(word)
            fixes.insert(0, word)
            word_cycles.append((fixes, len(fixes) - 1))

        flattened_cycles = []

        # Determine what word to replace in the sequence
        # By walking backwards through the list of words and replacing them
        # One by one imagining only a single fix being possible
        #
        # We prioritize later words because they have a bigger possibility 
        # that a user notices a mistake in a dictation sequence
        reversed_word_cycles = list(reversed(word_cycles))
        total_cycle_amount = sum([word_cycle[1] for word_cycle in word_cycles])
        for cycle_amount in range(0, total_cycle_amount + 1):
            replaced_words = []
            replace_count = 0
            for word_cycle in reversed_word_cycles:
                if word_cycle[1] > 0 and cycle_amount > replace_count and \
                    cycle_amount <= replace_count + word_cycle[1]:
                    replaced_words.insert(0, word_cycle[0][cycle_amount - replace_count])
                else:
                    replaced_words.insert(0, word_cycle[0][0])
                replace_count += word_cycle[1]
            
            flattened_cycles.append(replaced_words)

        # Add the starting word as the second option if available
        # But not as a duplicate
        # TODO this does not fix phonetic combination duplications
        # - affix -> a fix, a fix -> affix
        if starting_words is not None and len(starting_words) > 0 and len(flattened_cycles) > 0:
            found_indices_flattened_cycles = []
            for index, flattened_cycle in enumerate(flattened_cycles):
                if " ".join(flattened_cycle) == " ".join(starting_words):
                    found_indices_flattened_cycles.append(index)

            # Remove if this is an existing element later in the list
            while len(found_indices_flattened_cycles) > 0:
                del flattened_cycles[found_indices_flattened_cycles[-1]]
                del found_indices_flattened_cycles[-1]

            flattened_cycles.insert(1, starting_words)

        return flattened_cycles

    # Repeat the same input or correction to cycle through the possible changes
    def cycle_through_fixes(self, text: str, cycle_amount: int = 0, initial_state: str = None) -> Tuple[str, int]:
        words = text.split(" ")
        starting_words = [word.lower() for word in initial_state.split(" ") if word != ""] if initial_state is not None else []
        flattened_word_cycles = self.determine_cycles_for_words(words, starting_words)
        total_cycle_amount = len(flattened_word_cycles)
        cycle_amount = cycle_amount % total_cycle_amount

        # Determine what word to replace in the sequence
        # By walking backwards through the list of words and replacing them
        # One by one imagining only a single fix being possible
        #
        # We prioritize later words because they have a bigger possibility 
        # that a user notices a mistake in a dictation sequence
        replaced_words = flattened_word_cycles[cycle_amount]
        fixed_text = " ".join(replaced_words)
        
        return (fixed_text, cycle_amount)

    # Commit the buffer as proper changes
    def commit_buffer(self, cutoff_timestamp: float) -> List[InputFix]:
        new_fixes = []
        buffer_to_commit = [mutation for mutation in self.buffer if mutation.time <= cutoff_timestamp]
        for index, mutation in enumerate(buffer_to_commit):

            # Skip subsitutions that have been immediately removed afterwards
            if index + 1 < len(buffer_to_commit) and buffer_to_commit[index + 1].deletion == mutation.insertion:
                continue

            # Detect changes in substitutions
            elif len(mutation.insertion) > 0 and len(mutation.deletion) > 0:
                from_words = mutation.deletion.split(" ")
                to_words = mutation.insertion.split(" ")
                fixes = self.find_fixes_in_mutation(from_words, to_words, mutation.previous, mutation.next)
                for fix in fixes:
                    new_fixes.extend(self.create_fixes(fix[0], fix[1], fix[2], fix[3]))

        # TODO MAKE SURE TO ONLY COMMIT BUFFER IF CHANGES HAVEN'T BEEN MADE LATER
        self.buffer = [mutation for mutation in self.buffer if mutation.time > cutoff_timestamp]

        # Restart the polling if the buffer is filled still
        if self.poll_buffer_seconds > 0:
            if len(self.buffer) > 0:
                self.buffer_committing_job = cron.after(str(self.poll_buffer_seconds) + "s", lambda: self.commit_buffer(time.time() - self.poll_buffer_seconds))
            else:
                cron.cancel(self.buffer_committing_job)
                self.buffer_committing_job = None

        return new_fixes

    def add_to_buffer(self, insertion: str = "", deletion: str = "", previous: str = "", next: str = ""):

        # Only start the buffer committing job if the buffer has been filled
        if len(self.buffer) == 0 and self.poll_buffer_commit_seconds > 0:
            self.buffer_committing_job = cron.after(str(self.poll_buffer_seconds) + "s", lambda: self.commit_buffer(time.time() - self.poll_buffer_seconds))

        mutation = InputMutation(time.time(), insertion, deletion, previous, next)
        self.buffer.append(mutation)
        self.merge_buffer()

    # Simplify the buffer to properly detect changes
    def merge_buffer(self):
        # Merge consecutive insertions, deletions and insertions into a single change
        merged_buffer = []
        for item in self.buffer:
            if len(merged_buffer) > 0:
                # Merge insert - delete - insert into a single mutation change
                if len(merged_buffer) > 1 and item.insertion and merged_buffer[-2].insertion == merged_buffer[-1].deletion:
                    merged_buffer.pop()
                    merged_buffer[-1].time = item.time

                    # Only change the deletion if it is empty
                    # This way we can track changes 'thats' -> 'hat' -> 'that' correctly
                    if merged_buffer[-1].deletion == "":
                        merged_buffer[-1].deletion = merged_buffer[-1].insertion
                    merged_buffer[-1].insertion = item.insertion
                
                # Merge complete substitution fixes
                elif item.insertion and item.deletion == merged_buffer[-1].insertion:
                    merged_buffer[-1].time = item.time
                    merged_buffer[-1].insertion = item.insertion
                else:
                    # Merge item if they are connected
                    if item.previous != "" and merged_buffer[-1].insertion.endswith(item.previous) and \
                        merged_buffer[-1].deletion == "":
                        merged_buffer[-1].insertion += item.insertion
                        merged_buffer[-1].time = item.time
                    else:
                        merged_buffer.append(item)
            else:
                merged_buffer.append(item)

        self.buffer = merged_buffer

    def create_fixes(self, from_text: str, to_text: str, previous: str, next: str) -> InputFix:
        fix_key = self.get_key(from_text, to_text)

        if previous != "" and next != "":
            return [
                InputFix(fix_key, from_text, to_text, 0, previous, next),
                InputFix(fix_key, from_text, to_text, 0, "", next),
                InputFix(fix_key, from_text, to_text, 0, previous, ""),
                InputFix(fix_key, from_text, to_text, 0, "", "")
            ]
        elif previous == "" and next != "":
            return [
                InputFix(fix_key, from_text, to_text, 0, "", next),
                InputFix(fix_key, from_text, to_text, 0, "", "")
            ]
        elif previous != "" and next == "":
            return [
                InputFix(fix_key, from_text, to_text, 0, previous, ""),
                InputFix(fix_key, from_text, to_text, 0, "", "")
            ]
        else:
            return [InputFix(fix_key, from_text, to_text, 0, "", "")]
        
    def add_fix(self, from_text: str, to_text: str, previous: str, next: str, weight: int = 1):
        fix_key = self.get_key(from_text, to_text)
        if self.verbose:
            actions.user.hud_add_log("warning", "TRACKING FIX: " + from_text + " -> " + to_text)

        # Add fixes for every type of context
        if not fix_key in self.done_fixes:
            new_fixes = self.create_fixes(from_text, to_text, previous, next)
            self.done_fixes[fix_key] = new_fixes

        for done_fix in self.done_fixes[fix_key]:
            if (done_fix.previous == previous and done_fix.next == next) or \
                (done_fix.previous == "" and done_fix.next == next) or (done_fix.previous == previous and done_fix.next == "") or \
                (done_fix.previous == "" and done_fix.next == ""):
                done_fix.amount += weight

        # Check if we can persist the fixes
        for done_fix in self.done_fixes[fix_key]:
            if self.can_activate_fix(done_fix):
                self.flush_done_fixes()
                break

    def find_fix(self, text: str, previous: str, next: str) -> InputFix:
        found_fix = None
        letters_only_text = re.sub(r"[^\w\s]", '', text).lower()
        if letters_only_text in self.known_fixes:
            known_fixes = self.known_fixes[letters_only_text]

            # The more context is available, the higher the weight of the fix
            context_fixes = []
            for fix in known_fixes:
                if fix.previous == previous and fix.next == next:
                    context_fixes.append(fix)
            if context_fixes:
                found_fix = self.find_most_likely_fix(context_fixes, next, previous)

            # If the current most likely fix is usable, use it, otherwise reduce context and try again
            if found_fix is None or not self.can_activate_fix(found_fix):
                single_context_fixes = []
                for fix in known_fixes:
                    if fix.previous == previous and fix.next == "" or fix.previous == "" and fix.next == next:
                        single_context_fixes.append(fix)
                if single_context_fixes:
                    found_fix = self.find_most_likely_fix(single_context_fixes, next, previous)

                # If the current most likely fix is usable, use it, otherwise use no context at all
                if found_fix is None or not self.can_activate_fix(found_fix):
                    no_context_fixes = []
                    for fix in known_fixes:
                        if fix.previous == "" and fix.next == "":
                            no_context_fixes.append(fix)
                    if no_context_fixes:
                        found_fix = self.find_most_likely_fix(no_context_fixes, next, previous)

        return None if not found_fix or not self.can_activate_fix(found_fix) else found_fix

    def find_most_likely_fix(self, fixes: List[InputFix], next: str, previous: str ) -> InputFix:
        most_likey_fix = None
        if len(fixes) > 0:
            fix_list = []
            for fix in fixes:
                # Determine the amount of context for the found fix
                fix_context_score = 0
                if ( fix.previous == "" and fix.next == next ) or \
                    ( fix.previous == previous and fix.next == ""):
                    fix_context_score = 1
                elif fix.previous == previous and fix.next == next:
                    fix_context_score = 2

                # Determine the reverse fix count for this correction
                highest_context_opposite_fix = None
                highest_opposite_context_score = -1
                if fix.to_text.lower() in self.known_fixes:
                    opposite_fixes = [opposite_fix for opposite_fix in self.known_fixes[fix.to_text.lower()] if opposite_fix.to_text == fix.from_text]
                    for opposite_fix in opposite_fixes:
                        if opposite_fix.previous == previous and opposite_fix.next == next or \
                            ( opposite_fix.previous == "" and opposite_fix.next == next ) or \
                            ( opposite_fix.previous == previous and opposite_fix.next == "") or \
                            ( opposite_fix.previous == "" and opposite_fix.next == ""):

                            # Use the fix with the highest context
                            opposite_fix_context_score = 0
                            if ( opposite_fix.previous == "" and opposite_fix.next == next ) or \
                                ( opposite_fix.previous == previous and opposite_fix.next == ""):
                                opposite_fix_context_score = 1
                            elif opposite_fix.previous == previous and opposite_fix.next == next:
                                opposite_fix_context_score = 2

                            if opposite_fix_context_score > highest_opposite_context_score:
                                highest_context_opposite_fix = opposite_fix
                                highest_opposite_context_score = opposite_fix_context_score

                            elif highest_context_opposite_fix is None:
                                highest_context_opposite_fix = opposite_fix

                # A fix can be used if the fix is more likely that the opposite fix
                if highest_context_opposite_fix:
                    # If the fix has less matching context than the opposite, use the opposite
                    if fix_context_score < highest_opposite_context_score:
                        fix_list.append(0)

                    # If the fix has more matching context than the opposite, use it
                    elif fix_context_score > highest_opposite_context_score:
                        fix_list.append(fix.amount)

                    # If the context is equal, determine if the fix should be used if it is more likely than the opposite
                    else:
                        fix_list.append( fix.amount if fix.amount / (fix.amount + highest_context_opposite_fix.amount ) > 0.5 else 0)
                else:
                    fix_list.append(fix.amount)
                
            # Get the highest scoring fix as it is the most likely to do
            highest_amount = max(fix_list)
            for fix in fixes:
                if fix.amount == highest_amount and self.can_activate_fix(fix):
                    most_likey_fix = fix
                    break

        return most_likey_fix

    def flush_done_fixes(self):
        if self.verbose:
            actions.user.hud_add_log("success", "Flushing fixes!")
        new_keys = []

        for new_fix_list in self.done_fixes.values():
            for new_fix in new_fix_list:
                should_append = True
                if new_fix.from_text in self.known_fixes:
                    known_fixes = self.known_fixes[new_fix.from_text]
                    for index, known_fix in enumerate(known_fixes):
                        if new_fix.previous == known_fix.previous and new_fix.next == known_fix.next:
                            self.known_fixes[new_fix.from_text][index].amount += new_fix.amount
                            should_append = False
                            break

                # Add a new fix to the known fix list
                if should_append:
                    if new_fix.from_text not in self.known_fixes:
                        new_keys.append(new_fix.key)
                        self.known_fixes[new_fix.from_text.lower()] = []

                    if self.can_activate_fix(new_fix):
                        self.known_fixes[new_fix.from_text.lower()].append(new_fix)

        # Clear the currently done fixes that have exceeded the automatic threshold
        keys_to_remove = []
        for key in self.done_fixes:
            fix_count = len(self.done_fixes[key])
            fixes_to_remove = []
            for index, fix in enumerate(self.done_fixes[key]):
                if self.can_activate_fix(fix) or (fix.key in self.known_fixes and fix.key not in new_keys):
                    fixes_to_remove.append(index)

            if fix_count == len(fixes_to_remove):
                keys_to_remove.append(key)
            else:
                while len(fixes_to_remove) > 0:
                    del self.done_fixes[key][fixes_to_remove[-1]]
                    del fixes_to_remove[-1]
        for key in keys_to_remove:
            del self.done_fixes[key]
        
        if self.path_prefix:
            rows = []
            for fix_list in self.known_fixes.values():
                for fix in fix_list:
                    row = {}
                    for f in fields(InputFix):
                        if f.name != "key":
                            row[f.name] = getattr(fix, f.name)
                    rows.append(row)

            with open(self.get_current_fix_file_path(), 'w') as output_file:
                csv_writer = csv.DictWriter(output_file, rows[0].keys(), delimiter=";", lineterminator="\n", quoting=csv.QUOTE_ALL)
                csv_writer.writeheader()
                csv_writer.writerows(rows)

    def get_key(self, from_text: str, to_text: str) -> str:
        return str(from_text).lower() + "-->" + str(to_text).lower()

    def track_fix(self, from_text: str, to_text: str, previous: str, next: str):
        # Fix tracking isn't allowed - skip tracking
        if not self.is_fixing_allowed():
            return

        previous_word = "" if previous == "" else previous.strip().split()[-1]
        next_word = "" if next == "" else next.strip().split()[0]
        
        from_words = from_text.split()
        to_words = to_text.split()
        self.track_fix_list(from_words, to_words, previous_word, next_word)

    def find_fixes_in_mutation(self, from_words: List[str], to_words: List[str], previous: str, next: str) -> List:
        found_fixes = []
        to_words_index = 0

        first_previous_word = "" if previous == "" else re.sub(r"[^\w]", '', previous.strip().split()[-1]).lower()
        first_next_word = "" if next == "" else re.sub(r"[^\w]", '', next.strip().split()[0]).lower()
        used_from_indices = []
        for index, from_word in enumerate(from_words):
            # Skip over words we have already used for detecting fixes
            if index in used_from_indices:
                continue
            else:
                used_from_indices.append(index)

            # No more replacements can be found
            if to_words_index >= len(to_words):
                break
            else:
                # Single word replacements
                to_word = to_words[to_words_index].strip()

                no_format_from_word = re.sub(r"[^\w]", '', from_word).lower()
                no_format_to_word = re.sub(r"[^\w]", '', to_word).lower()
                one_to_one_similarity_score = self.phonetic_search.phonetic_similarity_score(no_format_from_word, no_format_to_word)
                
                # If the letters are the same even if there is different punctuation or capitalization, we do not need to track changes
                if one_to_one_similarity_score == EXACT_MATCH:
                    to_words_index += 1
                    continue
                else:
                    # Determine whether we need to replace 2 words with 1, 1 word with 2, or 1 word with 1 word
                    two_to_one_similarity_score = 0
                    one_to_two_similarity_score = 0
                    if index + 1 < len(from_words):
                        no_format_two_words = no_format_from_word + " " + re.sub(r"[^\w]", '', from_words[index + 1]).lower()
                        two_to_one_similarity_score = self.phonetic_search.phonetic_similarity_score(no_format_two_words, to_word)
                    if to_words_index + 1 < len(to_words):
                        two_to_words = to_word + " " + to_words[to_words_index + 1]
                        no_format_to_two_words = no_format_to_word + " " + re.sub(r"[^\w]", '', to_words[to_words_index + 1]).lower()
                        one_to_two_similarity_score = self.phonetic_search.phonetic_similarity_score(no_format_from_word, no_format_to_two_words)

                    biggest_score = max(one_to_one_similarity_score, two_to_one_similarity_score, one_to_two_similarity_score)

                    # Determine if we have hit a similarity threshold that we can determine a possible fix from
                    # Words that are too dissimilar aren't misinterpretations of the speech engine, but rather the user replacing one word for another
                    if biggest_score < EXACT_MATCH and biggest_score >= CORRECTION_THRESHOLD:

                        # Automatically find and persist homophones as similarties
                        if (one_to_one_similarity_score >= 1 and one_to_one_similarity_score <= 2) and to_word.lower() not in self.phonetic_search.find_homophones(from_word):
                            self.phonetic_search.add_phonetic_similarity(from_word.lower(), to_word.lower())
                        
                        # If one to one word replacement is more likely, add a fix for that
                        if one_to_one_similarity_score >= two_to_one_similarity_score and one_to_one_similarity_score >= one_to_two_similarity_score:
                            if one_to_one_similarity_score >= min(CORRECTION_THRESHOLD, 1 - (1 / len(to_word))):
                                previous_word = first_previous_word if to_words_index == 0 else to_words[to_words_index - 1]
                                next_word = first_next_word if to_words_index + 1 >= len(to_words) else to_words[to_words_index + 1]
                                found_fixes.append((no_format_from_word, to_word, previous_word, next_word))
                        
                        # If the two to one word replacement is more likely, add a fix for that
                        elif two_to_one_similarity_score >= one_to_one_similarity_score and two_to_one_similarity_score >= one_to_two_similarity_score:

                            if two_to_one_similarity_score >= min(CORRECTION_THRESHOLD, 1 - (1 / len(to_word))):
                                # Skip the next from word checking
                                used_from_indices.append(index + 1)

                                previous_word = first_previous_word if to_words_index == 0 else to_words[to_words_index - 1]
                                next_word = first_next_word if to_words_index + 1 >= len(to_words) else to_words[to_words_index + 1]
                                found_fixes.append((no_format_two_words, to_word, previous_word, next_word))

                        # If the one to two word replacement is more likely, add a fix for that
                        elif one_to_two_similarity_score >= one_to_one_similarity_score and one_to_two_similarity_score >= two_to_one_similarity_score:

                            if one_to_two_similarity_score >= min(CORRECTION_THRESHOLD, 1 - (1 / len(no_format_to_two_words))):
                                previous_word = first_previous_word if to_words_index == 0 else to_words[to_words_index - 1]
                                next_word = first_next_word if to_words_index + 2 >= len(to_words) else to_words[to_words_index + 2]
                                found_fixes.append((no_format_from_word, two_to_words, previous_word, next_word))
                                to_words_index += 1
                    to_words_index += 1
        return found_fixes

    def track_fix_list(self, from_words: List[str], to_words: List[str], previous: str, next: str):
        fixes = self.find_fixes_in_mutation(from_words, to_words, previous, next)
        for fix in fixes:
            self.add_fix(fix[0], fix[1], fix[2], fix[3])

    def can_activate_fix(self, fix: InputFix, amount = None) -> bool:
        context_threshold = CONTEXT_THRESHOLD_NONE
        if fix.previous != "" and fix.next != "":
            context_threshold = CONTEXT_THRESHOLD_MOST
        elif fix.previous != "" or fix.next != "":
            context_threshold = CONTEXT_THRESHOLD_SINGLE
        
        amount = amount if amount is not None else fix.amount
        return amount >= context_threshold
    
    def get_current_fix_file_path(self) -> Path:
        return self.path_prefix + os.sep + "context_" + self.language + "_" + self.engine + ".csv"

    def is_fixing_allowed(self) -> bool:
        return settings.get("user.marithime_auto_fixing_enabled") >= 1 or self.testing