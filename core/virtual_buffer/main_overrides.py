from talon import Context, Module, actions

mod = Module()
ctx = Context()
ctx_override = Context()
ctx_override.matches = """
tag: user.virtual_buffer_tracking
"""

mod.tag("virtual_buffer_tracking", desc="Overrides the general insert and key statement to enable contextual clues for inserting text")
ctx.tags = ["user.virtual_buffer_tracking"]

@ctx_override.action_class("main")
class MainOverrideActions:

    def key(key: str):
        """Overrides the key to trace it properly"""
        actions.next(key)
        actions.user.virtual_buffer_track_key(key)
        #actions.user.append_keystroke_to_analytics(key)

    def insert(text: str):
        """Overrides the insert action to trace it properly"""
        #actions.user.append_insert_to_analytics(text)
        actions.user.virtual_buffer_track_insert(text)
        actions.user.virtual_buffer_disable_tracking()
        actions.next(text)
        actions.user.virtual_buffer_enable_tracking()