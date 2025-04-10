from typing import List, Callable
from .detection import detect_phonetic_fix_type, phonetic_normalize, levenshtein, syllable_count, EXACT_MATCH, HOMOPHONE_MATCH, PHONETIC_MATCH

class PhoneticSearch:

    # The file content and callbacks, - Separated from talon bindings for easier testing
    homophone_content = ""
    phonetic_similarities_content = ""
    semantic_similarities_content = ""
    homophone_update = None
    semantics_update = None
    phonetic_similarities_update = None

    language: str = 'en'

    # The dictionaries containing the mapping for easier finding
    homophones = None
    phonetic_similarities = None
    semantic_similarities = None

    def set_homophones(self, homophone_content: str, update_callback: Callable[[str], None] = None):
        self.homophone_content = homophone_content
        self.homophones = self.parse_contents(homophone_content)
        if update_callback is not None:
            self.homophone_update = update_callback

    def set_semantic_similarities(self, semantic_content: str, update_callback: Callable[[str], None] = None):
        self.semantic_similarities_content = semantic_content
        self.semantic_similarities = self.parse_contents(semantic_content)
        if update_callback is not None:
            self.semantics_update = update_callback

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

            # Merge the words with other similarities, but maintain the order in which they are available in the contents
            merged_words = list(dict.fromkeys(words))
            for word in words:
                old_words = phones.get(word.lower(), [])
                merged_words.extend(old_words)
            merged_words = list(dict.fromkeys(words))            

            for word in merged_words:
                phones[word.lower()] = [merged_word for merged_word in merged_words if merged_word != word]

        return phones

    def add_homophone(self, word: str, replaced_word: str):
        new_contents = self.append_to_contents(word, replaced_word, self.homophone_content)

        if self.homophone_update:
            self.homophone_update(new_contents)
        else:
            self.set_homophones(new_contents)

    def add_phonetic_similarity(self, word: str, replaced_word: str):
        new_contents = self.append_to_contents(word, replaced_word, self.phonetic_similarities_content)

        if self.phonetic_similarities_update:
            self.phonetic_similarities_update(new_contents)
        else:
            self.set_phonetic_similiarities(new_contents)

    def add_semantic_similarity(self, word: str, replaced_word: str):
        new_contents = self.append_to_contents(word, replaced_word, self.semantic_similarities_content)

        if self.semantics_update:
            self.semantics_update(new_contents)
        else:
            self.set_semantic_similarities(new_contents)

    def append_to_contents(self, word: str, replaced_word: str, contents: str) -> str:
        check_word = word.lower()
        check_replaced_word = replaced_word.lower()

        # Update an existing row
        if check_word in contents or check_replaced_word in contents:
            new_contents = ""
            lines = contents.splitlines()
            for line in lines:
                split_line = line.lower().split(",")
                if check_word in split_line:
                    new_contents += line + "," + replaced_word + "\n"
                elif check_replaced_word in split_line:
                    new_contents += line + "," + word + "\n"
                else:
                    new_contents += line + "\n"

        # Add a row to the content
        else:
            new_contents = contents
            if not new_contents.endswith("\n"):
                new_contents += "\n"
            new_contents += word + "," + replaced_word

        return new_contents

    def find_homophones(self, word: str) -> List[str]:
        word = word.lower()
        if word in self.homophones:
            return self.homophones[word]
        return []
    
    def find_semantic_similarities(self, word: str) -> List[str]:
        word = word.lower()
        if word in self.semantic_similarities:
            return self.semantic_similarities[word]
        return []
    
    def find_phonetic_similarities(self, word: str) -> List[str]:
        word = word.lower()
        if word in self.phonetic_similarities:
            return self.phonetic_similarities[word]
        return []
    
    def get_known_fixes(self, word: str, replaced_word: str):
        return self.find_homophones(word)

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
    def phonetic_similarity_score(self, word_a: str, word_b: str) -> float:
        if word_a == word_b:
            return EXACT_MATCH
        else:
            # Match a known homophone
            homophones = self.find_homophones(word_a)
            if word_b.lower() in homophones:
                return HOMOPHONE_MATCH
            
            # Match a known homophone
            semantic_similarities = self.find_semantic_similarities(word_a)
            if word_b.lower() in semantic_similarities:
                return PHONETIC_MATCH

            # Attempt to find an unknown homophone
            homophone_a = phonetic_normalize(word_a, True, self.language)
            homophone_b = phonetic_normalize(word_b, True, self.language)

            if homophone_a == homophone_b:
                return HOMOPHONE_MATCH
            else:
                # Do fuzzy phonetic matching
                phonetic_a = phonetic_normalize(word_a, False, self.language)
                phonetic_b = phonetic_normalize(word_b, False, self.language)
                phonetics_distance = levenshtein(phonetic_a, phonetic_b)
                longest_phonetics_length = max(len(phonetic_a), len(phonetic_b))
                                                   
                homophone_distance = levenshtein(homophone_a, homophone_b)
                longest_homophone_length = max(len(homophone_a), len(homophone_b))

                phonetics_score = 0
                if phonetics_distance < longest_phonetics_length:
                    phonetics_score = (longest_phonetics_length - phonetics_distance) / longest_phonetics_length

                homophone_score = 0
                if homophone_distance < longest_homophone_length:
                    homophone_score = (longest_homophone_length - homophone_distance ) / longest_homophone_length

                if len(word_a) <= 3 and len(word_b) <= 3 and homophone_distance < phonetics_distance:
                    return homophone_score
                else:
                    return (phonetics_score + homophone_score ) / 2

    def syllable_count(self, word_a: str) -> int:
        return syllable_count(word_a, self.language)

    def calculate_syllable_score(self, score: float, word_a: str, word_b: str) -> float:
        word_a_count = syllable_count(word_a, self.language)
        word_b_count = word_a_count if word_a == word_b else syllable_count(word_b, self.language)

        return score * (max(word_a_count, word_b_count))