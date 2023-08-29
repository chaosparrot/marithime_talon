tag: user.code_comment_line
-
comment: user.code_comment_line_prefix()
comment line:
    #todo: this should probably be a single function once
    #.talon supports implementing actions with parameters?
    edit.line_start()
    user.code_comment_line_prefix()
#adds comment to the start of the line
comment line <user.text> quilt:
    #todo: this should probably be a single function once
    #.talon supports implementing actions with parameters?
    edit.line_start()
    user.code_comment_line_prefix()
    insert(user.text)
    insert(" ")
comment <user.text> quilt:
    #todo: this should probably be a single function once
    #.talon supports implementing actions with parameters?
    user.code_comment_line_prefix()
    insert(user.text)
comment <user.text>$:
    #todo: this should probably be a single function once
    #.talon supports implementing actions with parameters?
    user.code_comment_line_prefix()
    insert(user.text)
(line | inline) comment <user.text> quilt:
    #todo: this should probably be a single function once
    #.talon supports implementing actions with parameters?
    edit.line_end()
    user.code_comment_line_prefix()
    insert(user.text)
(line | inline) comment <user.text>$:
    #todo: this should probably be a single function once
    #.talon supports implementing actions with parameters?
    edit.line_end()
    user.code_comment_line_prefix()
    insert(user.text)
