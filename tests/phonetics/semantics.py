from ...phonetics.phonetics import PhoneticSearch
from ..test import create_test_suite

homophone_contents = "where,wear,ware"
phonetic_contents = ""
semantics_content = "when,where,what"

def test_detect_fixes(assertion):
    phonetic_search = PhoneticSearch()
    phonetic_search.set_homophones(homophone_contents)
    phonetic_search.set_phonetic_similiarities(phonetic_contents)
    phonetic_search.set_semantic_similarities(semantics_content)

    assertion("Phonetic search with a given set of homophones and semantic similarities")
    phonetic_search.add_semantic_similarity('that', 'this')
    assertion("    should be able to add 'that', and 'this', and find it", phonetic_search.find_semantic_similarities("that") == ['this'])
    assertion("    should be able to find homophones for 'this' as well", phonetic_search.find_semantic_similarities("this") == ['that'])
    assertion("    should not be able to find 'there' yet", phonetic_search.find_semantic_similarities("there") == [])
    phonetic_search.add_semantic_similarity('this', 'there')
    assertion("    After adding semantic similarities 'there', they should be found with 'this'", phonetic_search.find_semantic_similarities("this") == ['that', 'there'])
    assertion("    After adding semantic similarities 'there', 'this' should be found with 'there'", phonetic_search.find_semantic_similarities("there") == ['that', 'this'])

def test_semantic_similarity_scores(assertion):
    phonetic_search = PhoneticSearch()
    phonetic_search.set_homophones(homophone_contents)
    phonetic_search.set_phonetic_similiarities(phonetic_contents)
    phonetic_search.set_semantic_similarities(semantics_content)
    assertion("Semantic scores")
    assertion("    should give a score of 1 for 'when' and 'what' ( matching semantics )", round(phonetic_search.phonetic_similarity_score("when", "what") * 10) / 10 == 1.0)
    assertion("    should give a score of 1 for 'what' and 'when' ( matching semantics )", round(phonetic_search.phonetic_similarity_score("what", "when") * 10) / 10 == 1.0)
    assertion("    should not give a score of 1 for 'what' and 'which' ( matching semantics )", round(phonetic_search.phonetic_similarity_score("what", "which") * 10) / 10 != 1.0)
    assertion("    should not give a score of 1 for 'where's' and 'where' ( no semantic similarity )", round(phonetic_search.phonetic_similarity_score("where", "wheres") * 10) / 10 != 1.0)

suite = create_test_suite("Phonetic semantic similarity state")
suite.add_test(test_detect_fixes)
suite.add_test(test_semantic_similarity_scores)