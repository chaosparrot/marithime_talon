from typing import List, Callable
from .detection import detect_phonetic_fix_type, phonetic_normalize, levenshtein
from pathlib import Path

class PhoneticSearch:    

    # The file content and callbacks, - Separated from talon bindings for easier testing
    homophone_content = ""
    phonetic_similarities_content = ""
    homophone_update = None
    phonetic_similarities_update = None

    language: str = 'en'

    # The dictionaries containing the mapping for easier finding
    homophones = None
    phonetic_similarities = None

    def set_homophones(self, homophone_content: str, update_callback: Callable[[str], None] = None):
        self.homophone_content = homophone_content
        self.homophones = self.parse_contents(homophone_content)
        if update_callback is not None:
            self.homophone_update = update_callback

    def set_phonetic_similiarities(self, phonetic_similarities_content: str, update_callback: Callable[[str], None] = None):
        self.phonetic_similarities_content = phonetic_similarities_content
        self.phonetic_similarities = self.parse_contents(phonetic_similarities_content)
        if update_callback is not None:
            self.phonetic_similarities_update = update_callback

    def set_language(self, language: str):
        self.language = language

    def parse_contents(self, contents: str):
        phones = {}
        for line in contents.splitlines():
            words = line.rstrip().split(",")

            # Merge the words with other homophones, but maintain the order in which they are available in the contents
            merged_words = list(dict.fromkeys(words))
            for word in words:
                old_words = phones.get(word.lower(), [])
                merged_words.extend(old_words)
            merged_words = list(dict.fromkeys(words))            

            for word in merged_words:
                phones[word.lower()] = [merged_word for merged_word in merged_words if merged_word != word]

        return phones

    def add_homophone(self, word: str, replaced_word: str):
        check_word = word.lower()
        check_replaced_word = replaced_word.lower()

        # Update an existing row
        if check_word in self.homophones or check_replaced_word in self.homophones:
            new_contents = ""
            lines = self.homophone_content.splitlines()
            for line in lines:
                split_line = line.lower().split(",")
                if check_word in split_line:
                    new_contents += line + "," + replaced_word + "\n"
                elif check_replaced_word in split_line:
                    new_contents += line + "," + word + "\n"
                else:
                    new_contents += line + "\n"

        # Add a row to the homophones content
        else:
            new_contents = self.homophone_content
            if not new_contents.endswith("\n"):
                new_contents += "\n"
            new_contents += word + "," + replaced_word

        if self.homophone_update:
            self.homophone_update(new_contents)
        else:
            self.set_homophones(new_contents)

    def add_phonetic_similarity(self, word: str, replaced_word: str):
        check_word = word.lower()
        check_replaced_word = replaced_word.lower()

        # Update an existing row
        if check_word in self.phonetic_similarities or check_replaced_word in self.phonetic_similarities:
            new_contents = ""
            lines = self.phonetic_similarities_content.splitlines()
            for line in lines:
                split_line = line.lower().split(",")
                if check_word in split_line:
                    new_contents += line + "," + replaced_word + "\n"
                elif check_replaced_word in split_line:
                    new_contents += line + "," + word + "\n"
                else:
                    new_contents += line + "\n"

        # Add a row to the phonetic similarities content
        else:
            new_contents = self.homophone_content
            if not new_contents.endswith("\n"):
                new_contents += "\n"
            new_contents += word + "," + replaced_word

        if self.phonetic_similarities_update:
            self.phonetic_similarities_update(new_contents)
        else:
            self.set_phonetic_similiarities(new_contents)

    def find_homophones(self, word: str) -> List[str]:
        word = word.lower()
        if word in self.homophones:
            return self.homophones[word]
        return []
    
    def find_phonetic_similarities(self, word: str) -> List[str]:
        word = word.lower()
        if word in self.phonetic_similarities:
            return self.phonetic_similarities[word]
        return []
    
    def get_known_fixes(self, word: str, replaced_word: str):
        self.find_homophones(word)

    def update_fix(self, word: str, replaced_word: str):
        homophones = self.find_homophones(word)
        phonetic_similarties = self.find_phonetic_similarities(word)        
        for homophone in homophones:
            phonetic_similarties.extend(self.find_phonetic_similarities(homophone))
        
        # If our fix is already known, it does not need to be added
        if not (replaced_word in homophones or replaced_word in phonetic_similarties):
            fix_type = detect_phonetic_fix_type(word, replaced_word, self.language)
            if fix_type == "homophone":
                self.add_homophone(word, replaced_word)
            elif fix_type == "phonetic":
                self.add_phonetic_similarity(word, replaced_word)

    # Get all known detections - Prioritizing homophones over phonetically close fixes
    def get_known_fixes(self, word: str) -> List[str]:
        homophones = self.find_homophones(word)
        phonetic_similarities = self.find_phonetic_similarities(word)

        # Add phonetic similarties from homophones as well at a lower threshold
        for homophone in homophones:
            phonetic_similarities.extend(self.find_phonetic_similarities(homophone))

        known_fixes = []
        known_fixes.extend([phone for phone in homophones if phone != word])
        known_fixes.extend([phone for phone in phonetic_similarities if phone != word])
        known_fixes = list(dict.fromkeys(known_fixes))
        return known_fixes
    
    # Determine a similarity score
    # An exact match is 3
    # An exact phonetic match is a 2
    # A similar phonetic match is a 1 or below
    def phonetic_similarity_score(self, word_a: str, word_b: str) -> float:
        if word_a == word_b:
            return 3
        else:
            # Match a known homophone
            homophones = self.find_homophones(word_a)
            if word_b.lower() in homophones:
                return 2

            # Attempt to find an unknown homophone
            homophone_a = phonetic_normalize(word_a, True, self.language)
            homophone_b = phonetic_normalize(word_b, True, self.language)

            if homophone_a == homophone_b:
                return 2
            else:
                # Do fuzzy phonetic matching
                phonetic_a = phonetic_normalize(word_a, False, self.language)
                phonetic_b = phonetic_normalize(word_b, False, self.language)

                # Compare homophone score to phonetics score
                homophone_levenshtein = levenshtein(homophone_a, homophone_b)
                homophone_dist = 0
                if homophone_levenshtein < len(word_a):
                    homophone_dist = (homophone_levenshtein / len(word_a))

                levenshtein_dist = levenshtein(phonetic_a, phonetic_b)
                phonetics_score = 0
                if levenshtein_dist == 0:
                    phonetics_score = 1
                elif levenshtein_dist < len(word_a):
                    phonetics_score = 1 - (levenshtein_dist / len(word_a))
                elif levenshtein_dist < len(word_b):
                    phonetics_score =  1 - (levenshtein_dist / len(word_b))

                if homophone_dist > 0 and homophone_dist < phonetics_score:
                    return homophone_dist
                else:
                    return phonetics_score