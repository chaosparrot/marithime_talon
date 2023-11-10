^input state show$: user.input_core_print()
before <user.fuzzy_indexed_word>:
    user.input_core_move_cursor(fuzzy_indexed_word, 0)
after <user.fuzzy_indexed_word>:
    user.input_core_move_cursor(fuzzy_indexed_word, -1)

select <user.fuzzy_indexed_word>:
    user.input_core_select(fuzzy_indexed_word)
remove <user.fuzzy_indexed_word>:
    user.input_core_clear_phrase(indexed_words)

^document index:
    user.input_core_index_textarea()

^clear context$:
    user.input_core_forget()

^dump context$:
    user.input_core_dump()