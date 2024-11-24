# to disable command cancellation, comment out this entire file.
# you may also wish to adjust the commands in misc/cancel.talon.
from talon import Module, actions, speech_system
import time

# To change the phrase used to cancel commands, you must also adjust misc/cancel.talon
cancel_phrase = "cancel cancel".split()

canceled_time = time.perf_counter()
def pre_phrase(d):
    global canceled_time
    n = len(cancel_phrase)

    if "text" in d and "parsed" in d:
        before, after = d["text"][:-n], d["text"][-n:]

        if after != cancel_phrase and (canceled_time is None or "_ts" in d and float(d["_ts"]) > canceled_time):
            canceled_time = None
            return

        # cancel the command
        d["parsed"]._sequence = []
        if after != cancel_phrase:
            actions.user.hud_add_log("warning", "Canceled '" + " ".join(d["text"]) + "'")

mod = Module()
@mod.action_class
class Actions:

    def cancel_current_phrase():
        """Cancel the current phrase initiated using a noise"""
        global canceled_time
        canceled_time = time.perf_counter()

speech_system.register("pre:phrase", pre_phrase)
