mode: command
-
dictate$:
    user.enable_single_mode("dictation")    
dictate <user.raw_prose>$:
    user.dictation_insert(raw_prose)
    user.enable_single_mode("dictation")
dictate <user.prose> quilt: 
    user.dictation_insert(raw_prose)