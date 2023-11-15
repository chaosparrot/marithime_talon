mode: dictation
-
^command$:
    user.enable_single_mode("command")
    user.virtual_buffer_set_formatter("")

^command <phrase>$:
    user.enable_single_mode("command")
    user.rephrase(phrase, 0, 400)
    user.enable_single_mode("dictation")
    user.virtual_buffer_set_formatter("")