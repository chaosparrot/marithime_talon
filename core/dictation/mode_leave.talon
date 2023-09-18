mode: dictation
-
^command$:
    user.enable_single_mode("command")
    user.input_core_set_formatter("")

^command <phrase>$:
    user.enable_single_mode("command")
    user.rephrase(phrase, 0, 400)
    user.enable_single_mode("dictation")
    user.input_core_set_formatter("")