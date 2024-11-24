tag: terminal
-
# tags should be activated for each specific terminal in the respective talon file
el es: user.terminal_list_directories()
el es all: user.terminal_list_all_directories()

(cee dee|switching): user.terminal_change_directory("")
(cee dee|switch) <user.text>: user.terminal_change_directory(text)
(cee dee|switch) root: user.terminal_change_directory_root()

clean up: user.terminal_clear_screen()

history run: user.terminal_run_last()
history <user.text>: user.terminal_rerun_search(text or "")

kill all: user.terminal_kill_all()
