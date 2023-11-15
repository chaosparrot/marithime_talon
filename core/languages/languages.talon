^force {user.code_language}$:
    user.code_set_language(code_language)

^clear language$:
    user.code_automatic_language()

^dutch mode$:
    user.enable_single_mode("dictation")
    user.dutch_mode()

