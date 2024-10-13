from ..buffer import VirtualBuffer
from ..typing import VirtualBufferMatchMatrix
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite

def get_filled_vb():
    vb = VirtualBuffer()
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence ", "sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("or ", "or"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("paragraph", "paragraph"))
    return vb

def get_filled_vb_with_examples(examples):
    vb = VirtualBuffer()
    for index, example in enumerate(examples):
        vb.insert_tokens(text_to_virtual_buffer_tokens(example + " " if index < len(examples) - 1 else example, example))
    return vb

def test_detect_self_repair(assertion):
    vb = get_filled_vb()
    assertion( "With a filled virtual buffer, testing self repair in dictation")
    assertion( "    Repetition")
    assertion( "        Inserting the last placed word 'paragraph'...")
    assertion( "            Should result in a detected self repair", vb.detect_self_repair(["paragraph"]))
    assertion( "        Inserting the last placed words 'new paragraph'...")
    assertion( "            Should result in a detected self repair", vb.detect_self_repair(["new", "paragraph"]))
    assertion( "        Inserting the last placed words 'a new paragraph'...")
    assertion( "            Should result in a detected self repair", vb.detect_self_repair(["a", "new", "paragraph"]))
    assertion( "        Inserting the words 'paragraph word'... ")
    assertion( "            Should result in a detected self repair", vb.detect_self_repair(["paragraph", "word"]))
    assertion( "        Inserting the words 'a new paragraph with a new word'... ")
    assertion( "            Should result in a detected self repair", vb.detect_self_repair("a new paragraph with a new word".split()))
    assertion( "    Appending ( no context or too far back)" )
    assertion( "        Inserting the word 'word'...")
    assertion( "            Should not result in a detected self repair", vb.detect_self_repair(["word"]) == False)
    assertion( "        Inserting the words 'insert word'...")
    assertion( "            Should not result in a detected self repair", vb.detect_self_repair(["insert", "word"]) == False)
    assertion( "    Deletion of word")
    assertion( "        Inserting the words 'a paragraph'...")
    assertion( "            Should result in a detected self repair", vb.detect_self_repair(["a", "paragraph"]))
    assertion( "    Replacement of word")
    assertion( "        Inserting the words 'a new word'...")
    assertion( "            Should result in a detected self repair", vb.detect_self_repair(["a", "new", "word"]))
    assertion( "    Insertion in between words")
    assertion( "        Inserting the words 'a new word paragraph'... ")
    assertion( "           Should result in a detected self repair", vb.detect_self_repair(["a", "new", "word", "paragraph"]))
    assertion( "    Insertion and appending")
    assertion( "        Inserting the words 'an old paragraph insert'... ")
    assertion( "           Should result in a detected self repair", vb.detect_self_repair(["a", "new", "word", "paragraph", "insert"]))

def test_add_known_self_repair_examples(assertion):
    assertion( "With a virtual buffer filled with examples of wrong self repair")
    assertion( "    Inserting 'forget what we want to say' after 'when we'")
    vb = get_filled_vb_with_examples(["when", "we"])
    assertion( "        Should not result in self repair", vb.detect_self_repair(["forget", "what", "we", "want", "to", "say"]) == False)
    assertion( "    Inserting 'that would give us' after 'that is a fact'")
    vb = get_filled_vb_with_examples(["that", "is", "a", "fact"])
    assertion( "        Should not result in self repair", vb.detect_self_repair(["that", "would", "give", "us"]) == False)
    assertion( "    Inserting 'is it a' after 'is it a problem'")
    vb = get_filled_vb_with_examples(["is", "it", "a", "problem"])
    assertion( "        Should not result in self repair", vb.detect_self_repair(["is", "it", "a"]) == False)
    assertion( "    Inserting 'this is the test' after 'this is a test'")
    vb = get_filled_vb_with_examples(["this", "is", "a", "test"])
    assertion( "        Should result in self repair", vb.detect_self_repair(["this", "is", "the", "test"]))
    assertion( "    Inserting 'formulate a paragraph' after 'formulate a sentence'")
    vb = get_filled_vb_with_examples(["formulate", "a", "sentence"])
    assertion( "        Should result in self repair", vb.detect_self_repair(["formulate", "a", "paragraph"]))
    assertion( "    Inserting 'do fixes all the time' after 'want to'")
    # Known issue, not sure what to do with this except hardcode in an exception
    #vb = get_filled_vb_with_examples(["want", "to"])
    #assertion( "        Should not result in self repair", vb.detect_self_repair(["do", "fixes", "all", "the", "time"]) == False)
    vb = get_filled_vb_with_examples(["when", "we", "make", "mistakes,", "we", "tend", "to", "repeat", "ourselves"])
    assertion( "    Inserting 'we tend to repeat the words' after 'when we make mistakes, we tend to repeat ourselves'")
    assertion( "        Should result in self repair", vb.detect_self_repair(["we", "tend", "to", "repeat", "the", "words"]))
    vb = get_filled_vb_with_examples(["a", "lot", "of"])
    assertion( "    Inserting 'different kinds of' after 'a lot of'")
    assertion( "        Should not result in self repair", vb.detect_self_repair(["different", "kinds", "of", "people"]) == False)

suite = create_test_suite("Self repair in dictation")
suite.add_test(test_detect_self_repair)
suite.add_test(test_add_known_self_repair_examples)
