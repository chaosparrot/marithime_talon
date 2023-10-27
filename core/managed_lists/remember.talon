-
^remember only as <user.word>+$:
    user.remember_text(word_list)
^remember as <user.word>+$:
    user.remember_text(word_list, 1)
^{user.managed_lists} remember as <user.word>+$:
    user.remember_text(word_list, 1, managed_lists)
^{user.managed_lists} forget <user.word>+$:
    user.forget_text(word_list, managed_lists)