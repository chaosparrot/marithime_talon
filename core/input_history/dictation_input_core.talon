mode: dictation
-

# Cursor movement
^cursor before <user.fuzzy_indexed_word>+ [quill]:
    user.input_core_move_cursor(fuzzy_indexed_word_list, 0)
^cursor after <user.fuzzy_indexed_word>+ [quill]:
    user.input_core_move_cursor(input_history_word_list, -1)
^[cursor] continue:
    user.input_core_continue()

# Text selection
^select [word] <user.fuzzy_indexed_word>:
    user.input_core_select(fuzzy_indexed_word)
^select <user.fuzzy_indexed_word>+:
    user.input_core_select(fuzzy_indexed_word_list)

# Direct correction
^correction <user.word>+:
    user.input_core_correction(word_list)
^correction <user.word>+ quill <user.raw_prose>$:
    user.input_core_correction(word_list)
    user.input_core_insert(raw_prose)
    user.input_core_continue()
^correction word <user.fuzzy_indexed_word> <user.word> [quill]:
    user.input_core_select(fuzzy_indexed_word)
    user.input_core_insert(word)
    user.input_core_continue()

# Text removal
^remove <user.fuzzy_indexed_word>:
    user.input_core_clear_phrase(fuzzy_indexed_word)
    user.input_core_continue()