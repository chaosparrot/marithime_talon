mode: dictation
-
^document index:
    user.virtual_buffer_index_textarea()

# Caret movement
^cursor before <user.fuzzy_indexed_word>+ [quill]:
    user.virtual_buffer_move_caret(fuzzy_indexed_word_list, 0)
^cursor after <user.fuzzy_indexed_word>+ [quill]:
    user.virtual_buffer_move_caret(fuzzy_indexed_word_list, -1)
^[cursor] continue:
    user.virtual_buffer_continue()

# Text selection
^select [word] <user.fuzzy_indexed_word>:
    user.virtual_buffer_select(fuzzy_indexed_word)
^select <user.fuzzy_indexed_word>+:
    user.virtual_buffer_select(fuzzy_indexed_word_list)

# Direct correction
^correction <user.word>+:
    user.virtual_buffer_correction(word_list)
^correction <user.word>+ quill <user.raw_prose>$:
    user.virtual_buffer_correction(word_list)
    user.virtual_buffer_insert(raw_prose)
^correction word <user.fuzzy_indexed_word> <user.word> [quill]:
    user.virtual_buffer_select(fuzzy_indexed_word)
    user.virtual_buffer_insert(word)