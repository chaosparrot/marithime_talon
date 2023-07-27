from talon import actions, Module, cron, app
import time

mod = Module()

alt_tab_task = None
alt_tab_timeout = time.perf_counter()

def disable_alt_tab():
    global alt_tab_task
    actions.key("alt:up")
    alt_tab_task = None

@mod.action_class
class Actions:

    def alt_tab_start(prevent_double: bool = True, backwards: bool = False):
        """Start alt tabbing and keep it active for N seconds"""
        global alt_tab_timeout
        global alt_tab_task
        current_time = time.perf_counter()

        cron.cancel(alt_tab_task)
        
        if not prevent_double or current_time - alt_tab_timeout > 0.12:
            if current_time - alt_tab_timeout > 0.75:
                actions.key("alt:down")
                alt_tab_task = cron.after("400ms", disable_alt_tab)
            else:
                alt_tab_task = cron.after("750ms", disable_alt_tab)        

            actions.key("tab" if not backwards else "shift-tab")
            alt_tab_timeout = current_time

    def alt_shift_tab_start(prevent_double: bool = True):
        """Start alt-shift-tabbing and keep it active for N seconds"""
        actions.user.alt_tab_start(prevent_double, True)

def disable_alt_tab_if_running():
    global alt_tab_task
    if alt_tab_task is not None:
        disable_alt_tab()

def register_stop_alt_tab():
    actions.user.cancelable_tasks_append(lambda : actions.user.power_momentum_stop())

app.register("ready", register_stop_alt_tab)
