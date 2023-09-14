mode: dictation
-

# Cursor movement
^before {user.input_history_words}:
    user.input_core_move_cursor(input_history_words, 0)
^before <user.word>:
    user.input_core_move_cursor(word, 0)
^after {user.input_history_words}:
    user.input_core_move_cursor(input_history_words, -1)
^after <user.word>:
    user.input_core_move_cursor(word, -1)

# Text selection
^select {user.input_history_words}:
    user.input_core_select(input_history_words)
^select <user.word>:
    user.input_core_select(word)

# Text removal
^remove {user.input_history_words}:
    user.input_core_clear_phrase(input_history_words)
^remove <user.word>:
    user.input_core_clear_phrase(word)

^continue:
    user.input_core_continue()