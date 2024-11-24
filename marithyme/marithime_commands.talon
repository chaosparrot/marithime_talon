mode: command
mode: dictation
-
marithime <user.marithime_raw_prose> [{user.marithime_terminator_words}]: user.marithime_self_repair_insert(marithime_raw_prose)

# Caret movement
^[marithime] before <user.marithime_fuzzy_indexed_word>:
    user.marithime_move_caret(marithime_fuzzy_indexed_word, 0)
^[marithime] after <user.marithime_fuzzy_indexed_word>:
    user.marithime_move_caret(marithime_fuzzy_indexed_word, -1)
^[marithime] continue:
    user.marithime_continue()

# Text selection
^select [word] <user.marithime_fuzzy_indexed_word>:
    user.marithime_select(marithime_fuzzy_indexed_word)
^select <user.marithime_fuzzy_indexed_word>+:
    user.marithime_select(marithime_fuzzy_indexed_word_list)

# Direct correction
^correction <user.word>+:
    user.marithime_correction(word_list)
^correction <user.word>+ {user.marithime_terminator_words} <user.marithime_raw_prose>$:
    user.marithime_correction(word_list)
    user.marithime_insert(marithime_raw_prose)