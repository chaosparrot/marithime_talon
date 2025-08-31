from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens, can_merge_tokens
from ...virtual_buffer.typing import VirtualBufferToken
from ..test import create_test_suite
from ...virtual_buffer.settings import VirtualBufferSettings

def test_detect_text_formatter(assertion):
    assertion( "Detecting default merge strategies for merging tokens" )
    previous_token = VirtualBufferToken("a", "a", "")
    current_token = VirtualBufferToken(" ", "", "")
    assertion( "    Should allow 'a' and ' ' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("Sugg", "sugg", "")
    current_token = VirtualBufferToken("abolition ", "abolition", "")
    assertion( "    Should allow 'Sugg' and 'abolition ' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("ending", "ending", "")
    current_token = VirtualBufferToken(" with", "with", "")
    assertion( "    Should not allow 'ending' and ' with' to be merged", can_merge_tokens(previous_token, current_token, 0) == False)

def test_detect_snakecase_formatter(assertion):
    assertion( "Detecting snakecase merge strategies for merging tokens" )
    previous_token = VirtualBufferToken("case", "case", "snakecase")
    current_token = VirtualBufferToken("_", "", "snakecase")
    assertion( "    Should allow 'case' and '_' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("case_", "case", "snakecase")
    current_token = VirtualBufferToken("test", "", "snakecase")
    assertion( "    Should not allow 'case_' and 'test ' to be merged", can_merge_tokens(previous_token, current_token, 0) == False)
    previous_token = VirtualBufferToken("case", "case", "snakecase")
    current_token = VirtualBufferToken("test_", "test", "snakecase")
    assertion( "    Should allow 'case' and 'test_' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("case", "case", "snakecase")
    current_token = VirtualBufferToken("_test", "test", "snakecase")
    assertion( "    Should allow not 'case' and '_test' to be merged", can_merge_tokens(previous_token, current_token, 0) == False)

def test_detect_kebabcase_formatter(assertion):
    assertion( "Detecting kebabcase merge strategies for merging tokens" )
    previous_token = VirtualBufferToken("case", "case", "kebabcase")
    current_token = VirtualBufferToken("-", "", "kebabcase")
    assertion( "    Should allow 'case' and '-' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("case-", "case", "kebabcase")
    current_token = VirtualBufferToken("test", "", "kebabcase")
    assertion( "    Should not allow 'case_' and 'test ' to be merged", can_merge_tokens(previous_token, current_token, 0) == False)
    previous_token = VirtualBufferToken("case", "case", "kebabcase")
    current_token = VirtualBufferToken("test-", "test", "kebabcase")
    assertion( "    Should allow 'case' and 'test-' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("case", "case", "kebabcase")
    current_token = VirtualBufferToken("-test", "test", "kebabcase")
    assertion( "    Should allow not 'case' and '-test' to be merged", can_merge_tokens(previous_token, current_token, 0) == False)

def test_detect_constant_formatter(assertion):
    assertion( "Detecting constant merge strategies for merging tokens" )
    previous_token = VirtualBufferToken("CASE", "case", "constant")
    current_token = VirtualBufferToken("_", "", "constant")
    assertion( "    Should allow 'CASE' and '_' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("CASE_", "case", "constant")
    current_token = VirtualBufferToken("TEST", "", "constant")
    assertion( "    Should not allow 'CASE_' and 'TEST' to be merged", can_merge_tokens(previous_token, current_token, 0) == False)
    previous_token = VirtualBufferToken("CASE", "case", "constant")
    current_token = VirtualBufferToken("TEST-", "test", "constant")
    assertion( "    Should allow 'CASE' and 'TEST-' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("CASE", "case", "constant")
    current_token = VirtualBufferToken("_TEST", "test", "constant")
    assertion( "    Should allow not 'CASE' and '_TEST' to be merged", can_merge_tokens(previous_token, current_token, 0) == False)

def test_detect_camelcase_formatter(assertion):
    assertion( "Detecting pascal case merge strategies for merging tokens" )
    previous_token = VirtualBufferToken("case", "case", "camelcase")
    current_token = VirtualBufferToken("_", "", "camelcase")
    assertion( "    Should allow 'case' and '_' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("case", "case", "camelcase")
    current_token = VirtualBufferToken("Test", "", "camelcase")
    assertion( "    Should not allow 'case' and 'Test' to be merged", can_merge_tokens(previous_token, current_token, 0) == False)
    previous_token = VirtualBufferToken("case", "case", "camelcase")
    current_token = VirtualBufferToken("test-", "test", "camelcase")
    assertion( "    Should allow 'case' and 'test-' to be merged", can_merge_tokens(previous_token, current_token, 0))

def test_detect_pascalcase_formatter(assertion):
    assertion( "Detecting pascal case merge strategies for merging tokens" )
    previous_token = VirtualBufferToken("case", "case", "pascalcase")
    current_token = VirtualBufferToken("_", "", "pascalcase")
    assertion( "    Should allow 'case' and '_' to be merged", can_merge_tokens(previous_token, current_token, 0))
    previous_token = VirtualBufferToken("Case", "case", "pascalcase")
    current_token = VirtualBufferToken("Test", "", "pascalcase")
    assertion( "    Should not allow 'Case' and 'Test' to be merged", can_merge_tokens(previous_token, current_token, 0) == False)
    previous_token = VirtualBufferToken("case", "case", "pascalcase")
    current_token = VirtualBufferToken("test-", "test", "pascalcase")
    assertion( "    Should allow 'Case' and 'test-' to be merged", can_merge_tokens(previous_token, current_token, 0))


suite = create_test_suite("Merge detection for formatters")
suite.add_test(test_detect_text_formatter)
suite.add_test(test_detect_snakecase_formatter)
suite.add_test(test_detect_kebabcase_formatter)
suite.add_test(test_detect_constant_formatter)
suite.add_test(test_detect_camelcase_formatter)
suite.add_test(test_detect_pascalcase_formatter)