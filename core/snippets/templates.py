from talon import Module, actions, settings, clip
from typing import List, Callable

template_types = {
    'backticks': '`$CURSOR`',
    'quads': '"$CURSOR"',
    'singles': "'$CURSOR'",
    'squares': "[$CURSOR]",
    'diamonds': '<$CURSOR>',
    'closing': '</$CURSOR>',
    'parens': '($CURSOR)',
    'brackets': '{$CURSOR}',
    'block': '{\n$CURSOR\n}',
    'comment': '// $CURSOR',
    'void': ' $CURSOR '
}

# The cursor positions for the templates - Default is the given position
CURSOR_POSTION_BEFORE_ALL = -2
CURSOR_POSTION_BEFORE_CONTENT = -1
CURSOR_POSITION_GIVEN = 0
CURSOR_POSITION_AFTER_ALL = 1

def parse_template(template_content: str, cursor_position: int = CURSOR_POSITION_GIVEN, content: str = None, arguments: List[str] = None) -> List[str]:
    split_tokens = template_content.split("$CURSOR")
    before_cursor = split_tokens[0]
    after_cursor = split_tokens[1]

    token_list = [before_cursor]

    if content is not None:
        token_list.append(content)
    
    token_list.append(after_cursor)
    if cursor_position == CURSOR_POSITION_GIVEN:
        token_list.append('$SET_CURSOR_POSITION:-' + str(len(after_cursor)))
    elif cursor_position == CURSOR_POSTION_BEFORE_ALL:
        token_list.append('$SET_CURSOR_POSITION:-' + str(len("" if content is None else content) + len(before_cursor) + len(after_cursor)))
    elif cursor_position == CURSOR_POSTION_BEFORE_CONTENT:
        token_list.append('$SET_CURSOR_POSITION:-' + str(len("" if content is None else content) + len(after_cursor)))

    return [i for i in token_list if i]

def execute_template_tokens(tokens: List[str]):
    inserts_to_execute = []
    for token in tokens:
        if token.startswith('$SET_CURSOR_POSITION:'):
            if len(inserts_to_execute) > 0:
                actions.insert("".join(inserts_to_execute))
            inserts_to_execute = []
            cursor_position_count = int(token.replace('$SET_CURSOR_POSITION:', ""))
            if cursor_position_count < 0:
                actions.key('left:' + str(abs(cursor_position_count)))
        else:
            inserts_to_execute.append(token)
    
    if len(inserts_to_execute) > 0:
        actions.insert("".join(inserts_to_execute))
        inserts_to_execute = []

# '$WORDS'
# '${format:$WORDS}'
# '$CURSOR',
# '$|',
# '${keypress: blank($WORDS)}

mod = Module()
@mod.action_class
class Actions:

    def template_insert(template_type: str):
        """Insert a template of a specific type"""
        if template_type in template_types:
            template = template_types[template_type]
            execute_template_tokens(parse_template(template, CURSOR_POSITION_GIVEN))

    def template_wrap_selection(template_type: str, cursor_position: int = CURSOR_POSITION_GIVEN):
        """Wraps a template around the currently selected"""
        if template_type in template_types:
            content = actions.edit.selected_text()
            actions.key("backspace")
            template = template_types[template_type]
            execute_template_tokens(parse_template(template, cursor_position, content))
