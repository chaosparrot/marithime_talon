from talon import Module, actions, app, speech_system

mod = Module()

modes = {
    "admin": "enable extra administration commands terminal (docker, etc)",
    "debug": "a way to force debugger commands to be loaded",
    "ida": "a way to force ida commands to be loaded",
    "presentation": "a more strict form of sleep where only a more strict wake up command works",
}

for key, value in modes.items():
    mod.mode(key, value)


@mod.action_class
class Actions:
    def talon_mode():
        """For windows and Mac with Dragon, enables Talon commands and Dragon's command mode."""
        actions.speech.enable()

        engine = speech_system.engine.name
        # app.notify(engine)
        if "dragon" in engine:
            if app.platform == "mac":
                actions.user.engine_sleep()
            elif app.platform == "windows":
                actions.user.engine_wake()
                # note: this may not do anything for all versions of Dragon. Requires Pro.
                actions.user.engine_mimic("switch to command mode")
    
    def enable_single_mode(mode: str):
        """Enable a single mode and disable all other modes that are known"""
        default_modes = ["sleep", "command", "dictation"]

        if mode not in default_modes and not mode.startswith("user."):
            mode = "user." + mode
        
        for default_mode in default_modes:
            if default_mode != mode:
                actions.mode.disable(default_mode)
        actions.mode.enable(mode)