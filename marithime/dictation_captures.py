from talon import Module
mod = Module()

@mod.capture(
    rule="({user.vocabulary} | <phrase>)+"
)
def marithime_raw_prose(m) -> str:
    """Mixed additional words and phrases intended to be processed by marithime formatting later on"""
    return m