from talon import Module, grammar, actions
mod = Module()

# Taken partially from https://github.com/talonhub/community/blob/main/core/text/text_and_dictation.py
# So this repository could be used standalone
@mod.capture(
    rule="({user.vocabulary} | <phrase>)+"
)
def marithime_raw_prose(m) -> str:
    """Mixed additional words and phrases intended to be processed by marithime formatting later on"""
    result = ""
    total_words = []
    for item in m:
        words = (
            actions.dictate.replace_words(actions.dictate.parse_words(item))
            if isinstance(item, grammar.vm.Phrase)
            else [item]
        )

        for word in words:
            total_words.append(word)

    return " ".join(total_words)
