import re
from .languages import english, dutch, german

# Levenshtein text distance
def levenshtein(a: str, b: str) -> int:
    a_len = len(a)
    b_len = len(b)
    if a_len == 0 or b_len == 0:
        return a_len + b_len
    
    matrix = []
    # increment along the first column of each row
    for i in range(0, b_len + 1):
        matrix.append([i])
        
    # increment each column in the first row
    for j in range(1, a_len + 1):
        matrix[0].append(j)

    # Fill in the rest of the matrix
    for i in range(1, b_len + 1):
        matrix[i].extend([0] * (a_len))
        for j in range(1, a_len + 1):
            substitution_cost = 0 if b[i - 1] == a[j - 1] else 1
            matrix[i][j] = min(
                matrix[i-1][j-1] + substitution_cost, # substitution                
                matrix[i][j-1] + 1, # insertion
                matrix[i-1][j] + 1  # deletion
            )

    return matrix[b_len][a_len]

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", '', text).replace("\n", "")

PHONETIC_NORMALIZE_METHODS = {
    'en': english.homophone_normalize,
    'nl': dutch.homophone_normalize,
    'de': german.homophone_normalize,
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