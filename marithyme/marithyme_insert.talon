mode: dictation
tag: user.marithyme_dictation
-
^<user.marithyme_raw_prose> [{user.marithyme_terminator_words}]: user.virtual_buffer_self_repair_insert(marithyme_raw_prose)
^[{user.marithyme_terminator_words}] <user.marithyme_fuzzy_indexed_word>$:
    user.virtual_buffer_insert(marithyme_fuzzy_indexed_word)