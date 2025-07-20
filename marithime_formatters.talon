mode: command
mode: dictation
-
format {user.marithime_formatter}:
    user.marithime_set_formatter(marithime_formatter)
    #user.marithime_reformat_selection(marithime_formatter)
format {user.marithime_formatter} {user.phrase_ender}:
    user.marithime_set_formatter(marithime_formatter)
    #user.marithime_reformat_selection(marithime_formatter)
format {user.marithime_formatter} <user.marithime_raw_prose>:
    user.marithime_set_formatter(marithime_formatter)
    user.marithime_insert(marithime_raw_prose)
format {user.marithime_formatter} <user.marithime_raw_prose> {user.phrase_ender}:
    user.marithime_set_formatter(marithime_formatter)
    user.marithime_insert(marithime_raw_prose)