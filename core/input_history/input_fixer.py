from .input_history_typing import InputFix
import re
from typing import List, Dict
from ..user_settings import SETTINGS_DIR
import os
import csv
from pathlib import Path
from dataclasses import fields
from ..phonetics.actions import PhoneticSearch, phonetic_search
from talon import actions

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

    def __init__(self, language: str = "en", engine: str = "", path_prefix: str = str(Path(SETTINGS_DIR) / "cache"), verbose = False):
        self.language = language
        self.engine = engine
        self.path_prefix = path_prefix
        self.done_fixes = {}
        self.known_fixes = {}
        self.phonetic_search = phonetic_search
        self.verbose = verbose
        self.load_fixes(language, engine)

    def load_fixes(self, language: str, engine: str):
        if language and engine and self.path_prefix:
            self.language = language
            self.engine = engine
            self.known_fixes = {}

            fix_file_path = self.get_current_fix_file_path()

            # Create an initial fix file if it does not exist for the engine / language combination yet
            if not os.path.exists( fix_file_path ):
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
                        known_fix = InputFix(self.get_key(row["from_text"], row["to_text"]), row["from_text"], row["to_text"], row["amount"], row["previous"], row["next"])
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
        fix = self.find_fix(text, previous, next)
        if fix:
            # Use the fix but do not keep track of the automatic fixes as it would give too much weight over time
            return fix.to_text
        # No known fixes - Keep the same
        else:
            return text
        
    def add_fix(self, from_text: str, to_text: str, previous: str, next: str, weight: int = 1):
        fix_key = self.get_key(from_text, to_text)
        if self.verbose:
            actions.user.hud_add_log("warning", "TRACKING FIX: " + from_text + " -> " + to_text)

        # Add fixes for every type of context
        if not fix_key in self.done_fixes:
            if previous != "" and next != "":
                self.done_fixes[fix_key] = [
                    InputFix(fix_key, from_text, to_text, 0, previous, next),
                    InputFix(fix_key, from_text, to_text, 0, "", next),
                    InputFix(fix_key, from_text, to_text, 0, previous, ""),
                    InputFix(fix_key, from_text, to_text, 0, "", "")
                ]
            elif previous == "" and next != "":
                self.done_fixes[fix_key] = [
                    InputFix(fix_key, from_text, to_text, 0, "", next),
                    InputFix(fix_key, from_text, to_text, 0, "", "")
                ]
            elif previous != "" and next == "":
                self.done_fixes[fix_key] = [
                    InputFix(fix_key, from_text, to_text, 0, previous, ""),
                    InputFix(fix_key, from_text, to_text, 0, "", "")
                ]
            else:
                self.done_fixes[fix_key] = [InputFix(fix_key, from_text, to_text, 0, "", "")]

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
        return from_text.lower() + "-->" + to_text.lower()

    def track_fix(self, from_text: str, to_text: str, previous: str, next: str):
        previous_word = "" if previous == "" else previous.strip().split()[-1]
        next_word = "" if next == "" else next.strip().split()[0]
        
        from_words = from_text.split()
        to_words = to_text.split()
        self.track_fix_list(from_words, to_words, previous_word, next_word)

    def track_fix_list(self, from_words: List[str], to_words: List[str], previous: str, next: str):
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
                to_word = to_words[to_words_index]

                no_format_from_word = re.sub(r"[^\w]", '', from_word).lower()
                no_format_to_word = re.sub(r"[^\w]", '', to_word).lower()
                one_to_one_similarity_score = self.phonetic_search.phonetic_similarity_score(no_format_from_word, no_format_to_word)
                
                # If the letters are the same even if there is different punctuation or capitalization, we do not need to track changes
                if one_to_one_similarity_score == 3:
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
                    if biggest_score < 3 and biggest_score >= 0.5:

                        # Automatically find and persist homophones
                        if (one_to_one_similarity_score >= 1 and one_to_one_similarity_score <= 2) and to_word.lower() not in self.phonetic_search.find_homophones(from_word):
                            self.phonetic_search.add_homophone(from_word.lower(), to_word.lower())
                        
                        # If one to one word replacement is more likely, add a fix for that
                        if one_to_one_similarity_score >= two_to_one_similarity_score and one_to_one_similarity_score >= one_to_two_similarity_score:
                            if one_to_one_similarity_score >= min(0.5, 1 - (1 / len(to_word))):
                                previous_word = first_previous_word if to_words_index == 0 else to_words[to_words_index - 1]
                                next_word = first_next_word if to_words_index + 1 >= len(to_words) else to_words[to_words_index + 1]
                                self.add_fix(no_format_from_word, to_word, previous_word, next_word)
                        
                        # If the two to one word replacement is more likely, add a fix for that
                        elif two_to_one_similarity_score >= one_to_one_similarity_score and two_to_one_similarity_score >= one_to_two_similarity_score:

                            if two_to_one_similarity_score >= min(0.5, 1 - (1 / len(to_word))):
                                # Skip the next from word checking
                                used_from_indices.append(index + 1)

                                previous_word = first_previous_word if to_words_index == 0 else to_words[to_words_index - 1]
                                next_word = first_next_word if to_words_index + 1 >= len(to_words) else to_words[to_words_index + 1]
                                self.add_fix(no_format_two_words, to_word, previous_word, next_word)

                        # If the one to two word replacement is more likely, add a fix for that
                        elif one_to_two_similarity_score >= one_to_one_similarity_score and one_to_two_similarity_score >= two_to_one_similarity_score:

                            if one_to_two_similarity_score >= min(0.5, 1 - (1 / len(no_format_to_two_words))):
                                previous_word = first_previous_word if to_words_index == 0 else to_words[to_words_index - 1]
                                next_word = first_next_word if to_words_index + 2 >= len(to_words) else to_words[to_words_index + 2]
                                self.add_fix(no_format_from_word, two_to_words, previous_word, next_word)
                                to_words_index += 1
                    to_words_index += 1

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