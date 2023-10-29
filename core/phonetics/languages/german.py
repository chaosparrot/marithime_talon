import unicodedata

# Does a very coarse - unprecise transformation to some sort of phonetic normalization
# A lot of assumptions are made here that don't equate to all methods
def homophone_normalize(text: str, strict = False) -> str:
    # One to one phoneme connection
    text = text.replace("ph", "f").replace("pf", "f")
    text = text.replace("ck", "k").replace("ks", "x")
    text = text.replace("sch", "sj").replace("sh", "sj")
    text = text.replace("äu", "eu").replace("oi", "eu")
    text = text.replace("üh", "y").replace("ü", "ue").replace("ä", "ae")
    text = text.replace("öh", "u").replace("ö", "oe")

    text = text.replace("ou", "au")
    text = text.replace("ai", "ei").replace("ay", "ei").replace("ou", "au")
    text = text.replace("ß", "ss")
    text = text.replace("tz", "z")
    if text.startswith("ch"):
        text[0] = "t"
        text[1] = "j"
    if text.startswith("v"):
        text[0] = "f"

    # Very rough normalization ( unvoiced to voiced, slurred etc. )
    if not strict:
        text = text.replace("xth", "xf").replace("th", "t")
        text = text.replace("dth", "tt").replace("d", "t")

        text = text.replace("fth", "f").replace("v", "f").replace("lth", "lf")
        text = text.replace("b", "p")
        text = text.replace("ih", "i").replace("ah", "a").replace("oh", "o").replace("uh", "u").replace("ie", "i").replace("eh", "e")

        text = text.replace("ch", "g").replace("qu", "kw")
        text = text.replace("cr", "kr").replace("kh", "k").replace("m", "n").replace("m", "n").replace("ng", "n")
        text = text.replace("zh", "sj").replace("z", "ts").replace("nce", "ns")

    # Deduplication
    text = text.replace("dd", "d").replace("pp", "p").replace("cc", "k").replace("tt", "t").replace("ss", "s").replace("gg", "g") \
        .replace("kk", "k").replace("ff", "f").replace("ll", "l").replace("bb", "b").replace("nn", "n") \
        .replace("mm", "m").replace("zz", "z")

    return text
