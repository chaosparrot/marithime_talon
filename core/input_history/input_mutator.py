from talon import Module, Context
from .input_history import InputHistoryManager
mod = Module()
ctx = Context()

mod.list("input_history_words", desc="A list of words that correspond to inserted text and their cursor positions for quick navigation in text")
ctx.lists["user.input_history_words"] = []

# Class to manage all the talon bindings and key presses for input history
class InputMutator:
    manager: InputHistoryManager

    def __init__(self):
        self.manager = InputHistoryManager()