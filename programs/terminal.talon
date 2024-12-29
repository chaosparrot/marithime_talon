os: macos
os: windows
os: linux
tag: terminal
# TODO - Windows Powershell supports shift selection?!
-
settings():
    user.marithime_indexing_strategy = "disabled"
    user.marithime_context_multiline_supported = 0
    user.marithime_context_shift_selection = 0
    user.marithime_context_end_line_key = "ctrl-e"
    user.marithime_context_start_line_key = "ctrl-a"
    user.marithime_context_remove_line = "ctrl-u"
    user.marithime_context_remove_word = "ctrl-w"    
    user.marithime_context_clear_key = "enter"