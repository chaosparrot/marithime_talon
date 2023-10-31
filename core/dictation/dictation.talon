mode: dictation
-
<user.raw_prose>: user.input_core_self_repair_insert(raw_prose)
^quill <user.word>$:
    user.input_core_insert(word)
^quill <user.word> <user.raw_prose>:
    user.input_core_insert(word)
    user.input_core_insert(raw_prose)

# Spelling
^<user.direct_spelling>:
    user.input_core_insert(direct_spelling)