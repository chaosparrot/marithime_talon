mode: command
mode: dictation
-
# Caret movement
^[marithime] before <user.marithime_fuzzy_indexed_word>:
    user.marithime_move_caret(marithime_fuzzy_indexed_word, 0)
^[marithime] after <user.marithime_fuzzy_indexed_word>:
    user.marithime_move_caret(marithime_fuzzy_indexed_word, -1)
^[marithime] continue:
    user.marithime_continue()

# Text selection
^[marithime] select word <user.marithime_fuzzy_indexed_word>:
    user.marithime_select(marithime_fuzzy_indexed_word)
^[marithime] select <user.marithime_fuzzy_indexed_word>+:
    user.marithime_select(marithime_fuzzy_indexed_word_list)

# Direct correction
^[marithime] correction <user.marithime_word>+:
    user.marithime_correction(marithime_word_list)
^[marithime] correction <user.marithime_word>+ {user.marithime_terminator_word} <user.marithime_raw_prose>$:
    user.marithime_correction(marithime_word_list)
    user.marithime_insert(user.marithime_raw_prose)