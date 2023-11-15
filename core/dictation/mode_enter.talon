mode: command
-
dictate$:
    user.enable_single_mode("dictation")
    user.virtual_buffer_set_formatter("DICTATION_EN")
dictate <user.raw_prose>$:
    user.enable_single_mode("dictation")
    user.virtual_buffer_set_formatter("DICTATION_EN")
    user.virtual_buffer_insert(raw_prose)
dictate <user.prose> quilt: 
    user.virtual_buffer_set_formatter("DICTATION_EN")
    user.virtual_buffer_insert(raw_prose)
    user.virtual_buffer_set_formatter("")