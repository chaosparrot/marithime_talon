from talon import Context, Module

mod = Module()
ctx = Context()

mod.tag("marithime_available", desc="Check that the Marithime package is available for a user")
mod.tag("marithime_dictation", desc="Overrides the dictation insert with the marithime one")

ctx.tags = ["user.marithime_available"]