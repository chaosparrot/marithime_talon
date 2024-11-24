from talon import actions, Module, settings

mod = Module()
mod.setting("autofill_keys", type=str, default="tab", desc="The keys used to autofill the text")
mod.setting("autofill_timeout_ms", type=int, default=100, desc="The time required to wait before pressing the keys to autofill text")

@mod.action_class
class Actions:

    def autofill(text: str):
        """Automaticaly complete the text according to the given text"""
        actions.insert(text)
        actions.sleep(str(settings.get("user.autofill_timeout_ms")) + "ms")
        actions.user.autofill_press_keys()

    def autofill_press_keys():
        """Press the autofill keys"""
        actions.key(settings.get("user.autofill_keys"))