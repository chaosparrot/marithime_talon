auto spell <user.letters>:
  user.autofill(letters)

auto <user.word>:
  user.autofill(word)
  
auto this:
  user.autofill_press_keys()

line dupe:
  key(ctrl-left)
  key(ctrl-shift-right)
  key(ctrl-c)
  key(down)
  key(ctrl-v)	

line copy:
  key(ctrl-left)
  key(ctrl-shift-right)
  key(ctrl-c)

line end:
  key(ctrl-right)

line clear:
  key(ctrl-left)
  key(ctrl-shift-right)
  key(delete)

line move <user.number_string>:
  key(f5)
  sleep(100ms)
  key(A)
  "{number_string}"
  key(enter)
  
(line|cell) move <user.letter> <user.number_string>:
  key(f5)
  sleep(100ms)
  key(letter)
  "{number_string}"
  key(enter)