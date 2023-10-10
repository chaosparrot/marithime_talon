-
focus talon log$: menu.open_log()
focus debug view$: menu.open_debug_window()
focus browser$: user.switcher_launch_or_focus("Firefox")
focus browser private$: user.switcher_launch_or_focus("Firefox-privénavigatie")
focus spreadsheets$: user.switcher_launch_or_focus("Excel")
focus documents$: user.switcher_launch_or_focus("Word")
focus editor$: user.switcher_launch_or_focus("Visual Studio Code")
focus terminal$: user.switcher_launch_or_focus("Git Bash")
focus explorer$: user.switcher_launch_or_focus_explorer()
focus task manager$: user.switcher_launch_or_focus("Task Manager")
focus notepad$: user.switcher_launch_or_focus("Notepad++")
focus calculator$: user.switcher_launch_or_focus("Calculator")
focus audacity$: user.switcher_launch_or_focus("Audacity")

# Alt tab with delays
focus next: user.alt_tab_start(false)
focus previous: user.alt_shift_tab_start(false)

# Continuous phrases
^browser <phrase>$:
    user.switcher_launch_or_focus("Firefox")
    user.rephrase(phrase, true)
^browser private <phrase>$:
    user.switcher_launch_or_focus("Firefox-privénavigatie")
    user.rephrase(phrase, true)
^spreadsheets <phrase>$:
    user.switcher_launch_or_focus("Excel")
    user.rephrase(phrase, true)
^editor <phrase>$:
    user.switcher_launch_or_focus("Visual Studio Code")
    user.rephrase(phrase, true)
^terminal <phrase>$:
    user.switcher_launch_or_focus("Git Bash")
    user.rephrase(phrase, true)
^explorer <phrase>$:
    user.switcher_launch_or_focus_explorer()
    user.rephrase(phrase, true)