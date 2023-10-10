# Zoom
zoom in: edit.zoom_in()
zoom out: edit.zoom_out()
zoom reset: edit.zoom_reset()

# Searching
find it: edit.find()
next one: edit.find_next()

# Navigation

# The reason for these spoken forms is that "page up" and "page down" are globally defined as keys.
scroll up: edit.page_up()
scroll down: edit.page_down()

word left: edit.word_left()
word right: edit.word_right()

go left: edit.left()
go right: edit.right()
line up: edit.up()
line down: edit.down()

line start: edit.line_start()
line end: edit.line_end()

go way left:
    edit.line_start()
    edit.line_start()
go way right: edit.line_end()
go way up: edit.file_start()
go way down: edit.file_end()

go top: edit.file_start()
go bottom: edit.file_end()

go page up: edit.page_up()
go page down: edit.page_down()

# Selecting
document select [all]: edit.select_all()
line select: edit.select_line()
line select start: user.select_line_start()
line select end: user.select_line_end()

line select left: edit.extend_left()
line select right: edit.extend_right()
line select up: edit.extend_line_up()
line select down: edit.extend_line_down()

word select: edit.select_word()
word select left: edit.extend_word_left()
word select right: edit.extend_word_right()

document select left: edit.extend_line_start()
document select right: edit.extend_line_end()
document select start: edit.extend_file_start()
document select end: edit.extend_file_end()

# Indentation
indent [more]: edit.indent_more()
(indent less | out dent): edit.indent_less()


# Copy
selection copy: edit.copy()
document copy: user.copy_all()
line copy: user.copy_line()
line copy start: user.copy_line_start()
line copy end: user.copy_line_end()
word copy: user.copy_word()
word copy left: user.copy_word_left()
word copy right: user.copy_word_right()

# Cut
selection cut: edit.cut()
document cut: user.cut_all()
line cut: user.cut_line()
line cut start: user.cut_line_start()
line cut end: user.cut_line_end()
word cut: user.cut_word()
word cut left: user.cut_word_left()
word cut right: user.cut_word_right()

# Paste
(pace | paste) that: edit.paste()
(pace | paste) enter:
    edit.paste()
    key(enter)
paste match: edit.paste_match_style()
document (pace | paste): user.paste_all()
line (pace | paste): user.paste_line()
line (pace | paste) start: user.paste_line_start()
line (pace | paste) end: user.paste_line_end()

# Duplication
selection clone: edit.selection_clone()
line clone: edit.line_clone()

# Insert new line
new line above: edit.line_insert_up()
new line below | slap: edit.line_insert_down()

# Insert padding with optional symbols
(pad | padding): user.insert_between(" ", " ")
(pad | padding) <user.symbol_key>+:
    insert(" ")
    user.insert_many(symbol_key_list)
    insert(" ")

# Undo/redo
undo that: edit.undo()
redo that: edit.redo()

# Save
document save: edit.save()
document save all: edit.save_all()
