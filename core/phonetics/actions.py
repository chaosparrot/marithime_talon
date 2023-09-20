import os
from talon import Context, Module, fs
from .phonetics import PhoneticSearch

cwd = os.path.dirname(os.path.realpath(__file__))
homophones_file = os.path.join(cwd, "lists", "homophones_en.csv")
phonetics_file = os.path.join(cwd, "lists", "phonetic_close_en.csv")

ctx = Context()
mod = Module()

phonetic_search = PhoneticSearch()

def update_homophones(name, flags):
    if name != homophones_file:
        return

    phones = {}
    with open(homophones_file) as f:
        for line in f:
            words = line.rstrip().split(",")
            merged_words = set(words)
            for word in words:
                old_words = phones.get(word.lower(), [])
                merged_words.update(old_words)
            merged_words = sorted(merged_words)
            for word in merged_words:
                phones[word.lower()] = merged_words

    global all_homophones
    all_homophones = phones

def update_phonetics_close(name, flags):
    if name != phonetics_file:
        return

    phonetics_close = {}
    with open(phonetics_file) as f:
        for line in f:
            words = line.rstrip().split(",")
            merged_words = set(words)
            for word in words:
                old_words = phonetics_close.get(word.lower(), [])
                merged_words.update(old_words)
            merged_words = sorted(merged_words)
            for word in merged_words:
                phonetics_close[word.lower()] = merged_words

    global all_phonetic_close
    all_phonetic_close = phonetics_close

def update_files(name, flags):
    if name == homophones_file:
        update_homophones(name, flags)
    elif name == phonetics_file:
        update_phonetics_close(name, flags)
    else:
        return

update_homophones(homophones_file, None)
update_phonetics_close(phonetics_file, None)
fs.watch(cwd, update_files)

@mod.action_class
class Actions:

    def homophones_add(word: str, replaced_word: str):
        """Update the homophones file with a new addition"""
        global phonetic_search
        phonetic_search.add_homophone(word, replaced_word)

    def phonetics_close_add(word: str, replaced_word: str):
        """Update the phonetics file with a new addition"""
        global phonetic_search
        phonetic_search.add_close_phonetic(word, replaced_word)

    def phonetics_close_get(word: str) -> [str] or None:
        """Get phonetic close words for the given word"""
        global phonetic_search
        phonetic_search.find_close_phonetic(word)

    def homophones_get(word: str) -> [str] or None:
        """Get homophones for the given word"""
        global phonetic_search
        phonetic_search.find_close_phonetic(word)