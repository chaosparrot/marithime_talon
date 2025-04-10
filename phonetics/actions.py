import os
from talon import Context, Module, fs, settings, app
from .phonetics import PhoneticSearch

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
        global semantics_file
        global phonetic_search

        postfix = "" if language == "en" else "_" + language
        homophones_file = os.path.join(cwd, "lists", "homophones" + postfix + ".csv")
        phonetics_file = os.path.join(cwd, "lists", "phonetic_similarties" + postfix + ".csv")
        semantics_file = os.path.join(cwd, "lists", "semantics" + postfix + ".csv")        

        homophones_content = ""
        if os.path.exists(homophones_file):
            with open(homophones_file) as f:
                homophones_content = f.read()
        
        phonetics_content = ""
        if os.path.exists(phonetics_file):
            with open(phonetics_file) as f:
                phonetics_content = f.read()

        semantics_content = ""
        if os.path.exists(semantics_file):
            with open(semantics_file) as f:
                semantics_content = f.read()

        phonetic_search.set_homophones(homophones_content, lambda content, file_location=homophones_file: write_file(file_location, content))
        phonetic_search.set_phonetic_similiarities(phonetics_content, lambda content, file_location=phonetics_file: write_file(file_location, content))
        phonetic_search.set_semantic_similarities(semantics_content, lambda content, file_location=semantics_file: write_file(file_location, content))
        phonetic_search.set_language(language)

settings.register("speech.language", update_language)
app.register("ready", lambda: update_language( settings.get("speech.language") ))

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

def reload_phonetic_similarities(name, flags):
    if name != phonetics_file:
        return

    contents = ""
    if os.path.exists(phonetics_file):
        with open(phonetics_file) as f:
            contents = f.read()

    global phonetic_search
    phonetic_search.set_phonetic_similiarities(contents)

def reload_semantic_similarities(name, flags):
    if name != semantics_file:
        return

    contents = ""
    if os.path.exists(semantics_file):
        with open(semantics_file) as f:
            contents = f.read()

    global phonetic_search
    phonetic_search.set_semantic_similarities(contents)


def reload_files(name, flags):
    if name is not None:
        if name == homophones_file:
            reload_homophones(name, flags)
        elif name == phonetics_file:
            reload_phonetic_similarities(name, flags)
        elif name == phonetics_file:
            reload_semantic_similarities(name, flags)

fs.watch(cwd, reload_files)

@mod.action_class
class Actions:

    def marithime_homophones_add(word: str, replaced_word: str):
        """Update the homophones file with a new addition"""
        global phonetic_search
        phonetic_search.add_homophone(word, replaced_word)

    def marithime_homophones_get(word: str) -> [str] or None:
        """Get homophones for the given word"""
        global phonetic_search
        phonetic_search.find_homophones(word)

    def marithime_phonetic_similarities_add(word: str, replaced_word: str):
        """Update the phonetics file with a new addition"""
        global phonetic_search
        phonetic_search.add_phonetic_similarity(word, replaced_word)

    def marithime_phonetic_similarities_get(word: str) -> [str] or None:
        """Get phonetic similarties for the given word"""
        global phonetic_search
        phonetic_search.find_phonetic_similarities(word)

    def marithime_semantic_similarities_add(word: str, replaced_word: str):
        """Update the semantics file with a new addition"""
        global phonetic_search
        phonetic_search.add_semantic_similarity(word, replaced_word)

    def marithime_semantic_similarities_get(word: str) -> [str] or None:
        """Get semantic similarties for the given word"""
        global phonetic_search
        phonetic_search.find_semantic_similarities(word)
    
    def marithime_phonetic_similarity_score(word_a: str, word_b: str) -> int:
        """Test whether or not word a is similar enough to word b to be considered phonetically similar"""
        global phonetic_search
        return phonetic_search.phonetic_similarity_score(word_a, word_b)