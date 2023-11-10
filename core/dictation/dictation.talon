mode: dictation
-
<user.raw_prose>: user.input_core_self_repair_insert(raw_prose)
^quill <user.word>$:
    user.input_core_insert(word)
^quill <user.word> <user.raw_prose>:
    user.input_core_insert(word + " " + raw_prose)

^before {user.indexed_words} [quill]:
    user.input_core_move_cursor(indexed_words, 0)

^after {user.indexed_words} [quill]:
    user.input_core_move_cursor(indexed_words, -1)

# Spelling
^<user.direct_spelling>:
    user.input_core_insert(direct_spelling)