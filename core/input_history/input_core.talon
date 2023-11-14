before <user.fuzzy_indexed_word>:
    user.input_core_move_cursor(fuzzy_indexed_word, 0)
after <user.fuzzy_indexed_word>:
    user.input_core_move_cursor(fuzzy_indexed_word, -1)

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
^correction word <user.fuzzy_indexed_word> <user.word> [quill]:
    user.input_core_select(fuzzy_indexed_word)
    user.input_core_insert(word)

# Context managing
^clear context$:
    user.input_core_forget()
^dump context$:
    user.input_core_dump()
^document index:
    user.input_core_index_textarea()