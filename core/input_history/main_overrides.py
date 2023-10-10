from talon import Context, Module, actions

mod = Module()
ctx = Context()
ctx_override = Context()
ctx_override.matches = """
tag: user.input_core_tracking
"""

mod.tag("input_core_tracking", desc="Overrides the general insert and key statement to enable analytics and contextual clues for inserting")
ctx.tags = ["user.input_core_tracking"]

@ctx_override.action_class("main")
class MainOverrideActions:

    def key(key: str):
        """Overrides the key to trace it properly"""
        actions.next(key)
        actions.user.input_core_track_key(key)
        actions.user.append_keystroke_to_analytics(key)

    def insert(text: str):
        """Overrides the insert action to trace it properly"""
        actions.user.append_insert_to_analytics(text)
        actions.user.input_core_track_insert(text)
        actions.user.input_core_disable_tracking()
        actions.next(text)
        actions.user.input_core_enable_tracking()