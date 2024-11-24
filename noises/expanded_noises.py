from talon import Module, Context, actions, cron
import time

mod = Module()
mod.tag("expanded_noises", desc="Enables expanded noises to be recognized by adding a tag")
ctx = Context()

expanded_noise_cleared_at = time.perf_counter()
expanded_noises_cron = None
expanded_noises_enabled = False
def enable_expanded_noises():
    global expanded_noises_enabled

    if not expanded_noises_enabled:    
        expanded_noises_enabled = True
        ctx.tags = ["user.expanded_noises"]
        actions.user.hud_add_status_icon("expanded_noises", "noise_control")

def disable_expanded_noises():
    global expanded_noises_enabled
    global expanded_noise_cleared_at

    cron.cancel(expanded_noises_cron)
    if expanded_noises_enabled:
        expanded_noises_enabled = False
        expanded_noise_cleared_at = time.perf_counter()
        ctx.tags = []
        actions.user.hud_remove_status_icon("expanded_noises")

def debounce_expanded_noises(debounce_timeout_ms: int = 500):
    global expanded_noise_cleared_at
    global expanded_noises_cron

    new_expanded_noise_clear_time = time.perf_counter() + (debounce_timeout_ms / 1000)
    if new_expanded_noise_clear_time > expanded_noise_cleared_at:
        expanded_noise_cleared_at = new_expanded_noise_clear_time

        cron.cancel(expanded_noises_cron)
        expanded_noises_cron = cron.after(str(debounce_timeout_ms) + "ms", disable_expanded_noises)

mod = Module()
@mod.action_class
class Actions:

    def expanded_noises_debounce(debounce_timeout_ms: int = 500):
        """Enable the expanded noises flag"""
        debounce_expanded_noises(debounce_timeout_ms)

    def expanded_noises_enable():
        """Enable the expanded noises flag"""
        enable_expanded_noises()
        actions.user.expanded_noises_debounce()

    def expanded_noises_disable():
        """Disable the expanded noises flag"""
        disable_expanded_noises()