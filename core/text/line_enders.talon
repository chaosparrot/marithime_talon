-
(line end enter | pending): 
    edit.line_end()
    key(enter)
(comma pending | commending): 
    edit.line_end()
    insert(",")
    key(enter)
(dot pending | depending):
    edit.line_end()
    insert(".")
    key(enter)
prepending:
    edit.line_start()
    key(enter)
(semi pending | sending):
    edit.line_end()
    insert(";")
    key(enter)
piping:
    edit.line_end()
    insert(" | ")