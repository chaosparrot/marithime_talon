from talon import Context, Module

mod = Module()
ctx = Context()

mod.tag("marithyme_available", desc="Check that the Marithyme package is available for a user")
mod.tag("marithyme_dictation", desc="Overrides the dictation insert with the marithyme one")

ctx.tags = ["user.marithyme_available"]