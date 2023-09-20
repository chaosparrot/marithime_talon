import re
import unicodedata
import os

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

# Does a very coarse - unprecise transformation to some sort of phonetic normalization
# A lot of assumptions are made here that don't equate to all methods
def english_homophone_normalize(text: str, strict = False) -> str:
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")

    # One to one phoneme connection
    text = text.replace("ph", "f")
    text = text.replace("lve", "lf").replace("ce", "se")
    text = text.replace("cks", "x").replace("ks", "x")
    text = text.replace("wh", "w")
    text = text.replace("wr", "r")

    # Very rough normalization ( unvoiced to voiced, slurred etc. )
    if not strict:
        text = text.replace("xth", "xf").replace("th", "t")
        text = text.replace("dth", "tt").replace("dd", "t").replace("d", "t")
        text = text.replace("fth", "f").replace("v", "f").replace("lth", "lf")
        text = text.replace("b", "p")
        text = text.replace("ch", "k").replace("qu", "k").replace("ck", "k")
        text = text.replace("cr", "kr").replace("kh", "k").replace("mm", "n").replace("m", "n").replace("ng", "n").replace("g", "k")
        text = text.replace("sh", "s").replace("zh", "s").replace("z", "s").replace("c", "k").replace("nce", "ns")

    # Deduplication
    text = text.replace("dd", "d").replace("pp", "p").replace("cc", "k").replace("tt", "t").replace("ss", "s").replace("gg", "g") \
        .replace("ck", "k").replace("kk", "k").replace("ff", "f").replace("ll", "l").replace("bb", "b")

    return text

def get_phonetic_distance(a: str, b:str, strict = True) -> int:
    normalized_a = english_homophone_normalize(a, strict)
    normalized_b = english_homophone_normalize(b, strict)

    return levenshtein(normalized_a, normalized_b)

# Detects whether or not a change is possibly an added word or a homophone, or just a regular fix
def detect_phonetic_fix_type(a: str, b:str) -> str:
    strict_dist = get_phonetic_distance(normalize_text(a), normalize_text(b), True)

    if strict_dist == 0:
        return "homophone"
    else:
        dist = get_phonetic_distance(normalize_text(a), normalize_text(b), False)
        if dist <= len(b) / 4:
            return "phonetic"
    
    return ""