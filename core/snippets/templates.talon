create ticks: user.template_insert("backticks")
wrap ticks: user.template_wrap_selection("backticks")


wrap ticks before: user.template_wrap_selection("backticks", 1)
wrap ticks after: user.template_wrap_selection("backticks", -2)