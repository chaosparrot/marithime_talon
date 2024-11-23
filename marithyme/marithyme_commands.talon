mode: command
mode: dictation
-
marithyme <user.marithyme_raw_prose> [{user.marithyme_terminator_words}]: user.virtual_buffer_self_repair_insert(marithyme_raw_prose)

# Caret movement
^[marithyme] before <user.marithyme_fuzzy_indexed_word>:
    user.marithyme_move_caret(marithyme_fuzzy_indexed_word, 0)
^[marithyme] after <user.marithyme_fuzzy_indexed_word>:
    user.marithyme_move_caret(marithyme_fuzzy_indexed_word, -1)
^[marithyme] continue:
    user.marithyme_continue()

# Text selection
^select [word] <user.marithyme_fuzzy_indexed_word>:
    user.marithyme_select(marithyme_fuzzy_indexed_word)
^select <user.marithyme_fuzzy_indexed_word>+:
    user.marithyme_select(marithyme_fuzzy_indexed_word_list)

# Direct correction
^correction <user.word>+:
    user.marithyme_correction(word_list)
^correction <user.word>+ {user.marithyme_terminator_words} <user.marithyme_raw_prose>$:
    user.marithyme_correction(word_list)
    user.marithyme_insert(marithyme_raw_prose)