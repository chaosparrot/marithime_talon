mode: dictation
-
# line_enders
punk (line end enter | pending): 
    edit.line_end()
    key(enter)
punk (comma pending | commending): 
    edit.line_end()
    insert(",")
    key(enter)
punk (dot pending | depending):
    edit.line_end()
    insert(".")
    key(enter)
punk prepending:
    edit.line_start()
    key(enter)
punk (semi pending | sending):
    edit.line_end()
    insert(";")
    key(enter)
punk piping:
    edit.line_end()
    insert(" | ")

# space_combinations
punk void: insert(" ")
punk (dot void | dotoid): insert(". ")
punk (comma void | comoid): insert(", ")
punk (dash void | dashoid): insert("- ")
punk (equals void | equoid ): insert("= ")
punk (colon void | coloid ): insert(": ")
punk {self.symbol_key}+: insert(user.list_to_str(symbol_key_list))