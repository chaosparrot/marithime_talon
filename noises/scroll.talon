mode: noise
and tag: user.expanded_noises
-
# Scroll up
parrot(hiss):
    user.power_momentum_scroll_up()
    user.power_momentum_start(ts, 5.0)
    user.expanded_noises_debounce(1000)
parrot(hiss:repeat):
    user.power_momentum_add(ts, power)
    user.expanded_noises_debounce(1000)
parrot(hiss:stop):
    user.power_momentum_decaying()

# Scroll down
parrot(shush):
    user.power_momentum_scroll_down()
    user.power_momentum_start(ts, 5.0)
    user.expanded_noises_debounce(1000)
parrot(shush:repeat):
    user.power_momentum_add(ts, power)
    user.expanded_noises_debounce(1000)
parrot(shush:stop):
    user.power_momentum_decaying()
