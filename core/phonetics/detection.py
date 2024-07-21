import re
from .languages import english, dutch, german
from ..utils.levenshtein import levenshtein

# These values have been calculated with some deduction
# And testing using expectations with a set of up to 5 word matches
EXACT_MATCH = 1.2 # Used to be 3
HOMOPHONE_MATCH = 1.16 # Used to be 2
PHONETIC_MATCH = 1

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", '', text).replace("\n", "")

PHONETIC_NORMALIZE_METHODS = {
    'en': english.homophone_normalize,
    'nl': dutch.homophone_normalize,
    'de': german.homophone_normalize,
}

SYLLABLE_COUNT_METHODS = {
    'en': english.syllable_count,
    'nl': dutch.syllable_count,
    'de': german.syllable_count,   
}

def phonetic_normalize(word: str, strict = True, language: str = 'en') -> str:
    normalize_method = PHONETIC_NORMALIZE_METHODS['en']
    if language in PHONETIC_NORMALIZE_METHODS:
        normalize_method = PHONETIC_NORMALIZE_METHODS[language]
    return normalize_method(normalize_text(word), strict)

def get_phonetic_distance(a: str, b:str, strict = True, language: str = 'en') -> int:
    normalized_a = phonetic_normalize(normalize_text(a), strict, language)
    normalized_b = phonetic_normalize(normalize_text(b), strict, language)

    return levenshtein(normalized_a, normalized_b)

# Detects whether or not a change is possibly an added word or a homophone, or just a regular fix
def detect_phonetic_fix_type(a: str, b:str, language: str = 'en') -> str:
    strict_dist = get_phonetic_distance(a, b, True, language)

    if strict_dist == 0:
        return "homophone"
    else:
        dist = get_phonetic_distance(a, b, False, language)
        if dist <= len(b) / 4:
            return "phonetic"
    
    return ""

# Roughly calculate the amount of syllables in a word
def syllable_count(a: str, language: str = 'en') -> int:
    count_method = SYLLABLE_COUNT_METHODS['en']
    if language in SYLLABLE_COUNT_METHODS:
        count_method = SYLLABLE_COUNT_METHODS[language]
    return count_method(a)
