from talon import Context, Module

mod = Module()
ctx = Context()
mod.list("marithime_terminator_word", desc="A list of all the end-of-command terminator words used within dictation and other commands")
mod.tag("marithime_available", desc="Check that the Marithime package is available for a user")
mod.tag("marithime_dictation", desc="Overrides the dictation insert with the marithime one")
mod.tag("marithime_input_field_text", desc="Set when a single line text input field is focused")

mod.setting("marithime_auto_fixing_enabled", type=int, default=0, desc="Whether to allow auto-fixing ( auto correct ) based on earlier corrections")

# Settings that handle multi-line
mod.setting("marithime_context_shift_selection", type=int, default=1, desc="Enables or disables the use of shift press selection for the current context")
mod.setting("marithime_context_multiline_supported", type=int, default=1, desc="Enables or disables the use of multiple lines through the enter key")
mod.setting("marithime_context_word_wrap_width", type=int, default=-1, desc="Sets the width of the current input element for word wrapping, negative for disabled")

# Key tracking
mod.setting("marithime_context_clear_key", type=str, default="", desc="When this key is pressed, the context is cleared - For example, enter presses clearing the terminal")
mod.setting("marithime_context_remove_undo", type=str, default="ctrl-z", desc="The key combination to undo a paste action")
mod.setting("marithime_context_remove_word", type=str, default="ctrl-backspace", desc="The key combination to clear a word to the left of the caret")
mod.setting("marithime_context_remove_letter", type=str, default="backspace", desc="The key combination to clear a single letter to the left of the caret")
mod.setting("marithime_context_remove_forward_word", type=str, default="ctrl-delete", desc="The key combination to clear a word to the right of the caret")
mod.setting("marithime_context_remove_forward_letter", type=str, default="delete", desc="The key combination to clear a single letter to the right of the caret")
mod.setting("marithime_context_remove_line", type=str, default="", desc="The key to remove an entire line from the current text")
mod.setting("marithime_context_start_line_key", type=str, default="home", desc="The key to move to the start of the line")
mod.setting("marithime_context_end_line_key", type=str, default="end", desc="The key to move to the end of the line")

# Options - "" (default) - Whenever the confidence that it has lost the location in the file, re-index
#         - aggressive - After every marithime command that requires context, we re-index
#         - disabled - Disable indexing altogether, so no shift-select, clipboard, file or accessibility indexing
mod.setting("marithime_indexing_strategy", type=str, default="", desc="Determine what strategy we should use to begin reindexing documents")

ctx.tags = ["user.marithime_available"]
ctx.lists["user.marithime_terminator_word"] = [
#    "over",
    "quill",
    "quilt"
]