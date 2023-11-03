from ..phonetics import PhoneticSearch
from ...utils.test import create_test_suite

homophone_contents = "where,wear,ware"
phonetic_contents = "where,we're,were"

def test_detect_fixes(assertion):
    phonetic_search = PhoneticSearch()
    phonetic_search.set_homophones(homophone_contents)
    phonetic_search.set_phonetic_similiarities(phonetic_contents)

    assertion("Phonetic search with a given set of homophones and phonetic similarities") 
    where_list = phonetic_search.get_known_fixes("where")
    wear_list = phonetic_search.get_known_fixes("wear")
    assertion("    should find an ordered list of most common fixes for the word 'where'", where_list == ["wear", "ware", "we're", "were"])
    assertion("    should find an ordered list of most common fixes for the word 'wear'", wear_list == ["where", "ware", "we're", "were"])
    assertion("    should be able to find 'where' regardless of casing", phonetic_search.get_known_fixes("WHERE") == where_list)
    assertion("    should be able to find 'wear' regardless of casing", phonetic_search.get_known_fixes("WEaR") == wear_list)
    assertion("    should be not able to find 'too'", phonetic_search.get_known_fixes("too") == [])
    assertion("    should be not able to find 'two'", phonetic_search.get_known_fixes("two") == [])
    assertion("    should be not able to find 'to'", phonetic_search.get_known_fixes("to") == [])

    assertion("Phonetic search with a given set of homophones and phonetic similarities")
    phonetic_search.add_homophone('to', 'too')
    assertion("    should be able to add 'to', and 'too', and find it", phonetic_search.get_known_fixes("to") == ['too'])
    assertion("    should be able to find homophones for 'too' as well", phonetic_search.get_known_fixes("too") == ['to'])
    assertion("    should not be able to find 'two' yet", phonetic_search.get_known_fixes("two") == [])
    phonetic_search.add_phonetic_similarity('to', 'through')
    phonetic_search.add_phonetic_similarity('to', 'blue')
    assertion("    After adding phonetic similarities 'through' and 'blue', they should be found with 'to'", phonetic_search.get_known_fixes("to") == ['too', 'through', 'blue'])
    phonetic_search.add_homophone('too', 'two')
    assertion("    After adding two, it should be able to find it before the phonetic similarities", phonetic_search.get_known_fixes("two") == ['to', 'too', 'through', 'blue'])

def test_updating_fixes(assertion):
    assertion("Phonetic search with a new given set of homophones and phonetic similarities")
    phonetic_search = PhoneticSearch()
    phonetic_search.set_homophones(homophone_contents)
    phonetic_search.set_phonetic_similiarities(phonetic_contents)
    phonetic_search.update_fix('ad', 'add')
    assertion("    should be able to add 'add', and 'ad' as a homophone", phonetic_search.find_homophones("ad") == ['add'])
    assertion("    should be able to find homophones for 'add' as well", phonetic_search.find_homophones("add") == ['ad'])
    phonetic_search.update_fix('add', 'at')
    phonetic_search.update_fix('ad', 'at')
    phonetic_search.update_fix('ad', 'blue')
    assertion("    After fixing a couple of words ( add -> at, ad -> at, add -> blue), should find only at as a similarity", phonetic_search.get_known_fixes("ad") == ['add', 'at'])

def test_similarity_scores(assertion):
    phonetic_search = PhoneticSearch()
    phonetic_search.set_homophones(homophone_contents)
    assertion("Phonetic scores")
    assertion("    should give a score of 0.8 for 'that's' and 'that' ( 1 less character in 5 letter word )", round(phonetic_search.phonetic_similarity_score("that", "thats") * 10) / 10 == 0.8)
    assertion("    should give a score of 0.75 for 'do' and 'to' as a similar word ( average of 1 missing from 2 letter word and 1 complete match )", phonetic_search.phonetic_similarity_score("do", "to") == 0.75)
    assertion("    should give a score of 0.75 for 'word' and 'work' ( 1 differing character in 4 letter word )", phonetic_search.phonetic_similarity_score("word", "work") == 0.75)
    assertion("    should give a score of 0.8 for 'though' and 'dough' ( 1 differing character in 5 letter word)", round(phonetic_search.phonetic_similarity_score("dough", "though") * 10) / 10 == 0.8)
    assertion("    should give a score of 0.5 for 'a' and 'an' ( 1 less character from 2 letter word )", round(phonetic_search.phonetic_similarity_score("a", "an") * 10) / 10 == 0.5)
    assertion("    should give a score of 0.67 for 'an' and 'and' ( 1 less character from 3 letter word )", round(phonetic_search.phonetic_similarity_score("an", "and") * 100) / 100 == 0.67)
    assertion("    should give a score lower than 0.5 for 'crab' and 'nack' ( too dissimilar )", round(phonetic_search.phonetic_similarity_score("crab", "nack") * 10) / 10 < 0.5)
    assertion("    should give a score higher than 0.5 for 'ensemble' and 'assemble' ( very similar )", round(phonetic_search.phonetic_similarity_score("ensemble", "assemble") * 10) / 10 > 0.5)
    assertion("    should give a score lower than 0.5 for 'egg' and 'tremble' ( too dissimilar )", round(phonetic_search.phonetic_similarity_score("egg", "tremble") * 10) / 10 < 0.5)
    assertion( phonetic_search.phonetic_similarity_score("that", "dad"))

suite = create_test_suite("Phonetic similarity state")
suite.add_test(test_detect_fixes)
suite.add_test(test_updating_fixes)
suite.add_test(test_similarity_scores)