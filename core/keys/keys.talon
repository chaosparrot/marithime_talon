<user.arrow_keys>: user.move_cursor(arrow_keys)
spell <user.letters>: user.insert_keys(letters)
(ship | uppercase) <user.letters> [over]:
    user.insert_formatted(letters, "ALL_CAPS")
<user.symbol_key>: user.insert_keys(symbol_key)
<user.function_key>: key(function_key)
<user.special_key>: key(special_key)
<user.modifiers> <user.unmodified_key>: key("{modifiers}-{unmodified_key}")
# for key combos consisting only of modifiers, eg. `press super`.
press <user.modifiers>: key(modifiers)
# for consistency with dictation mode and explicit arrow keys if you need them.
press <user.keys>: user.insert_keys(keys)