import unicodedata

# Does a very coarse - unprecise transformation to some sort of phonetic normalization
# A lot of assumptions are made here that don't equate to all methods
def homophone_normalize(text: str, strict = False) -> str:
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")

    # One to one phoneme connection
    text = text.replace("ph", "f")
    text = text.replace("cks", "x").replace("ks", "x")
    text = text.replace("schr", "sr").replace("sh", "sj")
    text = text.replace("jou", "zju")
    text = text.replace("au", "ou")
    text = text.replace("ij", "ei")
    text = text.replace("th", "t")

    # Very rough normalization ( unvoiced to voiced, slurred etc. )
    if not strict:
        text = text.replace("xth", "xf").replace("th", "t")
        text = text.replace("dth", "tt").replace("d", "t")

        text = text.replace("fth", "f").replace("v", "f").replace("lth", "lf")
        text = text.replace("b", "p")
        
        # Can be cheat ( tj ), chef ( sj ) or chaos ( gaos ), but ist mostly sj
        if text.startswith("ch"):
            text = text.replace("chao", "gao").replace("ch", "sj")

        text = text.replace("ch", "g").replace("qu", "kw").replace("ck", "k")
        text = text.replace("cr", "kr").replace("kh", "k").replace("m", "n").replace("m", "n").replace("ng", "n")
        text = text.replace("sch", "sg").replace("zh", "sj").replace("z", "s").replace("c", "k").replace("nce", "ns")

    # Deduplication
    text = text.replace("dd", "d").replace("pp", "p").replace("cc", "k").replace("tt", "t").replace("ss", "s").replace("gg", "g") \
        .replace("ck", "k").replace("kk", "k").replace("ff", "f").replace("ll", "l").replace("bb", "b").replace("nn", "n") \
        .replace("mm", "m").replace("zz", "z")

    return text
