mode: dictation
-

# Cursor movement
^before <user.fuzzy_indexed_word>:
    user.input_core_move_cursor(fuzzy_indexed_word, 0)
^after <user.fuzzy_indexed_word>:
    user.input_core_move_cursor(input_history_word, -1)

# Text selection
^select [word] <user.fuzzy_indexed_word>:
    user.input_core_select(fuzzy_indexed_word)
^select <user.fuzzy_indexed_word>+:
    user.input_core_select(fuzzy_indexed_word_list)

# Direct correction
^correction <user.word>+:
    user.input_core_correction(word_list)
    user.input_core_continue()
^correction <user.fuzzy_indexed_word> with <user.word>:
    user.input_core_select(fuzzy_indexed_word)
    user.input_core_insert(word)
    user.input_core_continue()

# Text removal
^remove <user.fuzzy_indexed_word>:
    user.input_core_clear_phrase(fuzzy_indexed_word)

^continue:
    user.input_core_continue()