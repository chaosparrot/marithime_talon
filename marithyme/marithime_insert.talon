mode: dictation
tag: user.marithime_dictation
-
^<user.marithime_raw_prose> [{user.marithime_terminator_words}]: user.virtual_buffer_self_repair_insert(marithime_raw_prose)
^[{user.marithime_terminator_words}] <user.marithime_fuzzy_indexed_word>$:
    user.virtual_buffer_insert(marithime_fuzzy_indexed_word)