from talon import Module, actions, ui, settings

previous_insertions = []
def clear_previous_insertions(_ = None):
    global previous_insertions
    previous_insertions = []

ui.register("win_focus", clear_previous_insertions)

mod = Module()
mod.setting("context_correct_undo", type=str, default="ctrl-z", desc="The key combination to undo a paste action")
mod.setting("context_correct_word", type=str, default="ctrl-backspace", desc="The key combination to clear a word to the left of the cursor")
mod.setting("context_correct_letter", type=str, default="backspace", desc="The key combination to clear a single letter to the left of the cursor")
@mod.action_class
class Actions:

    def contextual_clear_insert(text: str):
        """The text to add to the previous insertions history"""
        global previous_insertions
        previous_insertions.append( text )

    def contextual_clear_letter(clear_history: bool = True):
        """Press the clear letter key"""
        actions.key(settings.get("user.context_correct_letter"))
        if clear_history:
            clear_previous_insertions()

    def contextual_clear_word(clear_history: bool = True):
        """Press the clear word keys"""
        actions.key(settings.get("user.context_correct_word"))
        if clear_history:
            clear_previous_insertions()

    def contextual_clear_undo(clear_history: bool = True):
        """Press the undo keys"""
        actions.key(settings.get("user.context_correct_undo"))
        if clear_history:
            clear_previous_insertions()

    def contextual_clear():
        """Clear the previously inserted letter or word depending on the previous insertion"""
        global previous_insertions
        if len(previous_insertions) > 0:
            previous = previous_insertions.pop()
            if len(previous) <= 1:
                actions.user.contextual_clear_letter(False)
                return
            elif previous == "ctrl-v":
                actions.user.contextual_clear_undo(False)
                return
            else:
                actions.key(settings.get("user.context_correct_letter") + ":" + str(len(previous)))
                return
        actions.user.contextual_clear_word(False)