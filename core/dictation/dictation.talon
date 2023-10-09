mode: dictation
-
<user.raw_prose>: user.input_core_self_repair_insert(raw_prose)
^quill <user.word>$:
    user.input_core_insert(word)
^quill <user.word> <user.raw_prose>:
    user.input_core_insert(word)
    user.input_core_insert(raw_prose)

# Inflow correction
<user.word> repeat <user.word> <user.word>:
    word_list = user.as_list(word_2, word_3)
    best_match_word = user.input_core_best_match(word_list, 0, word_1)
    user.input_core_insert(best_match_word)

# Spelling
<user.direct_spelling>:
    user.input_core_insert(direct_spelling)