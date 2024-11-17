from talon import Module
mod = Module()

@mod.capture(
    rule="({user.vocabulary} | <phrase>)+"
)
def marithyme_raw_prose(m) -> str:
    """Mixed additional words and phrases intended to be processed by marithyme formatting later on"""
    return m