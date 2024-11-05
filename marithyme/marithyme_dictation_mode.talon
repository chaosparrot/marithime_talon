mode: dictation
-
^marithyme index:
    user.virtual_buffer_index_textarea()

# Caret movement
^cursor before <user.marithyme_fuzzy_indexed_word>+ [quill]:
    user.marithyme_move_caret(marithyme_fuzzy_indexed_word_list, 0)
^cursor after <user.marithyme_fuzzy_indexed_word>+ [quill]:
    user.marithyme_move_caret(marithyme_fuzzy_indexed_word_list, -1)
^[cursor] continue:
    user.marithyme_continue()

# Text selection
^select [word] <user.marithyme_fuzzy_indexed_word>:
    user.marithyme_insert(marithyme_fuzzy_indexed_word)
^select <user.marithyme_fuzzy_indexed_word>+:
    user.marithyme_insert(marithyme_fuzzy_indexed_word_list)

# Direct correction
^correction <user.word>+:
    user.marithyme_correction(word_list)
^correction <user.word>+ quill <user.raw_prose>$:
    user.marithyme_correction(word_list)
    user.marithyme_insert(raw_prose)
^correction word <user.marithyme_fuzzy_indexed_word> <user.word> [quill]:
    user.marithyme_select(marithyme_fuzzy_indexed_word)
    user.marithyme_insert(word)