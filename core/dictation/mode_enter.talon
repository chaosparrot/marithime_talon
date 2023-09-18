mode: command
-
dictate$:
    user.enable_single_mode("dictation")
    user.input_core_set_formatter("DICTATION_EN")
dictate <user.raw_prose>$:
    user.dictation_insert(raw_prose)
    user.enable_single_mode("dictation")
    user.input_core_set_formatter("DICTATION_EN")    
dictate <user.prose> quilt: 
    user.input_core_set_formatter("DICTATION_EN")    
    user.dictation_insert(raw_prose)
    user.input_core_set_formatter("")