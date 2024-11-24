from talon import Context, Module

mod = Module()
ctx = Context()
mod.list("marithime_terminator_word", desc="A list of all the end-of-command terminator words used within dictation and other commands")

mod.tag("marithime_available", desc="Check that the Marithime package is available for a user")
mod.tag("marithime_dictation", desc="Overrides the dictation insert with the marithime one")
mod.tag("marithime_context_disable_shift_selection", desc="Disables shift selection for the current context")
mod.tag("marithime_context_disable_word_wrap", desc="Disables word wrap detection for the current context")

mod.setting("marithime_auto_fixing_enabled", type=int, default=0, desc="Whether to allow auto-fixing ( auto correct ) based on earlier corrections")
mod.setting("marithime_context_remove_undo", type=str, default="ctrl-z", desc="The key combination to undo a paste action")
mod.setting("marithime_context_remove_word", type=str, default="ctrl-backspace", desc="The key combination to clear a word to the left of the caret")
mod.setting("marithime_context_remove_letter", type=str, default="backspace", desc="The key combination to clear a single letter to the left of the caret")
mod.setting("marithime_context_remove_forward_word", type=str, default="ctrl-delete", desc="The key combination to clear a word to the right of the caret")
mod.setting("marithime_context_remove_forward_letter", type=str, default="delete", desc="The key combination to clear a single letter to the right of the caret")

ctx.tags = ["user.marithime_available"]
ctx.lists["user.marithime_terminator_word"] = ["quill", "quilt"]