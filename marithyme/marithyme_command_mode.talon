before <user.marithyme_fuzzy_indexed_word>:
    user.marithyme_move_caret(marithyme_fuzzy_indexed_word, 0)
after <user.marithyme_fuzzy_indexed_word>:
    user.marithyme_move_caret(marithyme_fuzzy_indexed_word, -1)

^[cursor] continue:
    user.marithyme_continue()    

# Text selection
^select [word] <user.marithyme_fuzzy_indexed_word>:
    user.marithyme_select(marithyme_fuzzy_indexed_word)
^select <user.marithyme_fuzzy_indexed_word>+:
    user.marithyme_select(marithyme_fuzzy_indexed_word_list)

# Direct correction
^correction <user.word>+:
    user.marithyme_correction(word_list)
^correction <user.word>+ quill <user.raw_prose>$:
    user.marithyme_correction(word_list)
    user.marithyme_insert(raw_prose)
^correction word <user.marithyme_fuzzy_indexed_word> <user.word> [quill]:
    user.marithyme_select(marithyme_fuzzy_indexed_word)
    user.marithyme_insert(word)

# Context managing
^marithyme clear context$:
    user.marithyme_forget_context()
^marithyme dump context$:
    user.marithyme_dump_context()
^marithyme index:
    user.marithyme_index_textarea()