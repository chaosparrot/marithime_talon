from typing import List
from .detection import detect_phonetic_fix_type

# TODO - REMEMBER PRIORITIZATION SOMEHOW?
class PhoneticSearch:    
    all_homophones = None
    all_phonetic_close = None
    homophones_file = None
    phonetic_close_file = None

    def __init__(self, homophones_file: str, phonetic_close_file: str, all_homophones, all_phonetic_close):
        self.set_files(homophones_file, phonetic_close_file)
        self.set_homophones(all_homophones)
        self.set_close_phonetic(all_phonetic_close)

    def set_files(self, homophones_file: str, phonetic_close_file: str):
        self.homophones_file = homophones_file
        self.phonetic_close_file = phonetic_close_file

    def set_homophones(self, all_homophones):
        self.all_homophones = all_homophones

    def set_close_phonetic(self, all_phonetic_close):
        self.all_phonetic_close = all_phonetic_close

    def add_homophone(self, word: str, replaced_word: str, homophone_):
        check_word = word.lower()
        check_replaced_word = replaced_word.lower()

        if not check_word in self.all_homophones or not check_replaced_word in self.all_homophones:
            with open(self.homophones_file, 'r+') as file:
                lines = file.read().splitlines()
                file.seek(0)
                for line in lines:
                    split_line = line.lower().split(",")
                    if check_word in split_line:
                        file.write(line + "," + replaced_word + "\n")
                    elif check_replaced_word in split_line:
                        file.write(line + "," + word + "\n")
                    else:
                        file.write(line + "\n")

    def add_close_phonetic(self, word: str, replaced_word: str):
        check_word = word.lower()
        check_replaced_word = replaced_word.lower()

        if not check_word in self.all_phonetic_close or not check_replaced_word in self.all_phonetic_close:
            with open(self.phonetic_close_file, 'r+') as file:
                lines = file.read().splitlines()
                file.seek(0)
                for line in lines:
                    split_line = line.lower().split(",")
                    if check_word in split_line:
                        file.write(line + "," + replaced_word + "\n")
                    elif check_replaced_word in split_line:
                        file.write(line + "," + word + "\n")
                    else:
                        file.write(line + "\n")

    def find_homophones(self, word: str) -> List[str]:
        word = word.lower()
        if word in self.all_homophones:
            return self.all_homophones[word]
        return []
    
    def find_close_phonetic(self, word: str) -> List[str]:
        word = word.lower()
        if word in self.all_phonetic_close:
            return self.all_phonetic_close[word]
        return []
    
    def update_fix(self, word: str, replaced_word: str):
        detections = self.get_known_detections(word, replaced_word)
        if len(detections) == 0:
            fix_type = detect_phonetic_fix_type(word, replaced_word)
            if fix_type == "homophone":
                self.add_homophone(word, replaced_word)
            elif fix_type == "phonetic":
                self.add_close_phonetic(word, replaced_word)

    # Get all known detections - Prioritizing homophones over phonetically close fixes
    def get_known_fixes(self, word: str) -> List[str]:
        homophones = self.find_homophones(word)
        close_phonetic = self.find_close_phonetic(word)

        known_fixes = []
        if word in homophones:
            known_fixes.append(word)
            known_fixes.extend([phone for phone in homophones if phone != word])

        if word in known_fixes:
            known_fixes.extend([phone for phone in close_phonetic if phone != word])
        else:
            known_fixes.extend(close_phonetic)
        return known_fixes