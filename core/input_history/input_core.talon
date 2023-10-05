^input state show$: user.input_core_print()
before <user.fuzzy_indexed_word>:
    user.input_core_move_cursor(fuzzy_indexed_word, 0)
after <user.fuzzy_indexed_word>:
    user.input_core_move_cursor(input_history_word, -1)

select <user.fuzzy_indexed_word>:
    user.input_core_select(fuzzy_indexed_word)
remove <user.fuzzy_indexed_word>:
    user.input_core_clear_phrase(indexed_words)

    ^line index:
    user.input_core_index_line()

^clear context$:
    user.input_core_forget()