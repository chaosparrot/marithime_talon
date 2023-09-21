import os
from talon import Context, Module, fs, settings
from .phonetics import PhoneticSearch
from .detection import levenshtein

cwd = os.path.dirname(os.path.realpath(__file__))

ctx = Context()
mod = Module()
current_language = None

phonetic_search = PhoneticSearch()

def update_language(language: str):
    global current_language
    if language is not None:
        language = language.lower().split("_")[0]

    if not language:
        language = "en"
    
    if language is not current_language:
        current_language = language
        global homophones_file
        global phonetics_file
        global phonetic_search

        homophones_file = os.path.join(cwd, "lists", "homophones_" + language + ".csv")
        phonetics_file = os.path.join(cwd, "lists", "phonetic_similarties_" + language + ".csv")

        homophones_content = ""
        if os.path.exists(homophones_file):
            with open(homophones_file) as f:
                homophones_content = f.read()
        
        phonetics_content = ""
        if os.path.exists(phonetics_file):
            with open(phonetics_file) as f:
                phonetics_content = f.read()
            
        phonetic_search.set_homophones(homophones_content, lambda content, file_location=homophones_file: write_file(file_location, content))
        phonetic_search.set_phonetic_similiarities(phonetics_content, lambda content, file_location=phonetics_file: write_file(file_location, content))
        phonetic_search.set_language(language)
        print( phonetic_search.homophones['to'] )

settings.register("speech.language", update_language)
update_language( settings.get("speech.language") )

def write_file(file_location: str, content: str):
    # Only write the file if it is inside of the phonetics directory for security reasons
    if file_location.startswith(cwd):
        with open(file_location, "w") as file:
            file.write(content)

def reload_homophones(name, flags):
    if name != homophones_file:
        return

    contents = ""
    if os.path.exists(homophones_file):
        with open(homophones_file) as f:
            contents = f.read()

    global phonetic_search
    phonetic_search.set_homophones(contents)

def reload_phonetic_similarties(name, flags):
    if name != phonetics_file:
        return

    contents = ""
    if os.path.exists(phonetics_file):
        with open(phonetics_file) as f:
            contents = f.read()

    global phonetic_search
    phonetic_search.set_phonetic_similiarities(contents)

def reload_files(name, flags):
    if name is not None:
        if name == homophones_file:
            reload_homophones(name, flags)
        elif name == phonetics_file:
            reload_phonetic_similarties(name, flags)

fs.watch(cwd, reload_files)

@mod.action_class
class Actions:

    def homophones_add(word: str, replaced_word: str):
        """Update the homophones file with a new addition"""
        global phonetic_search
        phonetic_search.add_homophone(word, replaced_word)

    def homophones_get(word: str) -> [str] or None:
        """Get homophones for the given word"""
        global phonetic_search
        phonetic_search.find_homophones(word)

    def phonetic_similarities_add(word: str, replaced_word: str):
        """Update the phonetics file with a new addition"""
        global phonetic_search
        phonetic_search.add_phonetic_similarity(word, replaced_word)

    def phonetic_similarities_get(word: str) -> [str] or None:
        """Get phonetic similarties for the given word"""
        global phonetic_search
        phonetic_search.find_phonetic_similarities(word)
    
    def phonetic_similarity_score(word_a: str, word_b: str) -> int:
        """Test whether or not word a is similar enough to word b to be considered phonetically similar"""
        global phonetic_search
        return phonetic_search.phonetic_similarity_score(word_a, word_b)