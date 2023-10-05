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
^correction word <user.fuzzy_indexed_word> <user.word>:
    user.input_core_select(fuzzy_indexed_word)
    user.input_core_insert(word)
    user.input_core_continue()

# Inflow correction
<user.word> repeat <user.word> <user.word>:
    word_list = user.as_list(word_2, word_3)
    best_match_word = user.input_core_best_match(word_list, 0, word_1)
    user.input_core_insert(best_match_word)

^letter <user.letters>:
    insert(letters)
<user.letter> <user.letters>:
    insert(letter + letters)

^quill <user.raw_prose>:
    user.input_core_insert(raw_prose)

# Text removal
^remove <user.fuzzy_indexed_word>:
    user.input_core_clear_phrase(fuzzy_indexed_word)

^continue:
    user.input_core_continue()