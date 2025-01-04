from talon import settings

# Class that keeps the context for what kind of key behavior the current program and input field has
# Kept in a single class to make sure it doesn't get out of sync or new empty input contexts get created
class VirtualBufferSettings:

    # Whether to use live talon checking
    # Disabled during testing to make sure we don't invoke the talon context system during start up
    live_checking = True

    shift_selection = True
    multiline_supported = True

    # Cursor navigation keys
    end_of_line_key:str = "end"
    start_of_line_key:str = "home"

    # Content clearing keys
    clear_key:str = ""
    clear_line_key:str = ""
    remove_letter_key:str = "backspace"
    remove_forward_letter_key:str = "delete"
    remove_word_key:str = "ctrl-backspace"
    remove_forward_word_key:str = "ctrl-delete"

    def __init__(self, live_checking=False):
        self.live_checking = live_checking

    def has_shift_selection(self):
        if self.live_checking:
            self.shift_selection = settings.get("user.marithime_context_shift_selection") > 0
        return self.shift_selection
    
    def has_multiline_support(self):
        if self.live_checking:
            self.multiline_supported = settings.get("user.marithime_context_multiline_supported") > 0
        return self.multiline_supported
    
    def get_clear_key(self):
        if self.live_checking:
            self.clear_key = settings.get("user.marithime_context_clear_key")
        return self.clear_key
    
    def get_end_of_line_key(self):
        if self.live_checking:
            self.end_of_line_key = settings.get("user.marithime_context_end_line_key")
        return self.end_of_line_key
    
    def get_start_of_line_key(self):
        if self.live_checking:
            self.start_of_line_key = settings.get("user.marithime_context_start_line_key")
        return self.start_of_line_key

    def get_remove_line_key(self):
        if self.live_checking:
            self.remove_line_key = settings.get("user.marithime_context_remove_line_key")
        return self.remove_line_key
    
    def get_remove_character_left_key(self):
        if self.live_checking:
            self.remove_letter_key = settings.get("user.marithime_context_remove_letter")
        return self.remove_letter_key
    
    def get_remove_character_right_key(self):
        if self.live_checking:
            self.remove_forward_letter_key = settings.get("user.marithime_context_remove_forward_letter")
        return self.remove_forward_letter_key
    
    def get_remove_word_left_key(self):
        if self.live_checking:
            self.remove_word_key = settings.get("user.marithime_context_remove_word")
        return self.remove_word_key

    def get_remove_word_right_key(self):
        if self.live_checking:
            self.remove_word_forward_key = settings.get("user.marithime_context_remove_forward_word")
        return self.remove_word_forward_key

virtual_buffer_settings = VirtualBufferSettings(True)