^input state show$: user.input_core_print()
before {user.input_history_words}:
    user.input_core_move_cursor(input_history_words, 0)
before <user.word>:
    user.input_core_move_cursor(word, 0)

after {user.input_history_words}:
    user.input_core_move_cursor(input_history_words, -1)
after <user.word>:
    user.input_core_move_cursor(word, -1)

select {user.input_history_words}:
    user.input_core_select(input_history_words)
select <user.word>:
    user.input_core_select(word)
^line index:
    user.input_core_index_line()