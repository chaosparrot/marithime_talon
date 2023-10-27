import unicodedata

# Does a very coarse - unprecise transformation to some sort of phonetic normalization
# A lot of assumptions are made here that don't equate to all methods
def homophone_normalize(text: str, strict = False) -> str:
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