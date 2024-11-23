from talon import Context, Module, actions

mod = Module()
ctx = Context()
ctx_override = Context()
ctx_override.matches = """
tag: user.marithyme_input_tracking
"""

mod.tag("marithyme_input_tracking", desc="Overrides the general insert and key statement to enable contextual clues for inserting text")
ctx.tags = ["user.marithyme_input_tracking"]

@ctx_override.action_class("main")
class MainOverrideActions:

    def key(key: str):
        """Overrides the key to trace it properly"""
        actions.next(key)
        actions.user.marithyme_track_key(key)

    def insert(text: str):
        """Overrides the insert action to trace it properly"""
        actions.user.marithyme_track_insert(text)
        actions.user.marithyme_disable_input_tracking()
        actions.next(text)
        actions.user.marithyme_enable_input_tracking()