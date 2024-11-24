from talon import Module, Context, actions

mod = Module()

ctx_vscode = Context()
ctx_vscode.matches = """
app: vscode
"""

ctx_browser = Context()
ctx_browser.matches = """
tag: browser
"""

@mod.action_class
class Actions:

    def toggle_hats():
        """Toggle hats depending on the application selected"""
        pass

@ctx_browser.action_class("user")
class RangoToggleActions:

    def toggle_hats():
        """Toggle hats depending on the application selected"""
        actions.user.rango_command_without_target("toggleHints")


@ctx_vscode.action_class("user")
class VscodeToggleActions:

    def toggle_hats():
        """Toggle hats depending on the application selected"""
        actions.key("ctrl-shift-p")
        actions.insert("Cursorless toggle")
        actions.key("enter")

