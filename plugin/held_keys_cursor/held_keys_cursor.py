from talon import Context, actions

current_cursor_state = {
    "ctrl": False,
    "alt": False,
    "shift": False
}

def update_cursor_state(key: str):
    global current_cursor_state
    current_state = ("ctrl" if current_cursor_state["ctrl"] else "") + ("shift" if current_cursor_state["shift"] else "") +\
        ("alt" if current_cursor_state["alt"] else "")

    # Split the key string into separate keys
    key_elements = key.split(" ")
    if "ctrl:down" in key_elements:
        current_cursor_state["ctrl"] = True
    elif "ctrl" in key:
        current_cursor_state["ctrl"] = False

    if "shift:down" in key_elements:
        current_cursor_state["shift"] = True
    elif "shift" in key:
        current_cursor_state["shift"] = False
    
    if "alt:down" in key_elements:
        current_cursor_state["alt"] = True
    elif "alt" in key:
        current_cursor_state["alt"] = False
    
    new_state = ("ctrl" if current_cursor_state["ctrl"] else "") + ("shift" if current_cursor_state["shift"] else "") +\
        ("alt" if current_cursor_state["alt"] else "")

    # Detect if we have had any changes between states before updating the HUD state
    if current_state != new_state:
        color = "FF" if current_cursor_state["ctrl"] else "00"
        color += "FF" if current_cursor_state["shift"] else "00"
        color += "FF" if current_cursor_state["alt"] else "00"

        if color == "000000":
            actions.user.hud_clear_screen_regions("cursor", "held_keys")
        else:
            full_screen_region = actions.user.hud_create_screen_region("held_keys", "#" + color)
            actions.user.hud_publish_screen_regions("cursor", [full_screen_region], True)


hud_ctx = Context()
hud_ctx.matches = """
tag: user.talon_hud_visible
"""

@hud_ctx.action_class("main")
class HudActions:

    def key(key: str):
        """Overrides the key action to buffer and log it"""
        actions.next(key)
        update_cursor_state(key)