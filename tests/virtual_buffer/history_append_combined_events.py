from ...virtual_buffer.input_history import InputHistory, InputEventType
from ...virtual_buffer.typing import VirtualBufferToken
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite

def get_input_history() -> InputHistory:
    return InputHistory()

suite = create_test_suite("Appending events to the history that shouldn't result in more events as they are combined")
# TODO - Make a list of all the transitions and apply them