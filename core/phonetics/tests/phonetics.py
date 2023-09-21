from ..phonetics import PhoneticSearch

homophone_contents = "where,wear,ware"
phonetic_contents = "where,we're,were"

phonetic_search = PhoneticSearch()
phonetic_search.set_homophones(homophone_contents)
phonetic_search.set_phonetic_similiarities(phonetic_contents)

print("Phonetic search with a given set of homophones and phonetic similarities") 
where_list = phonetic_search.get_known_fixes("where")
wear_list = phonetic_search.get_known_fixes("wear")
print("    should find an ordered list of most common fixes for the word 'where'", where_list == ["wear", "ware", "we're", "were"])
print("    should find an ordered list of most common fixes for the word 'wear'", wear_list == ["where", "ware", "we're", "were"])
print("    should be able to find 'where' regardless of casing", phonetic_search.get_known_fixes("WHERE") == where_list)
print("    should be able to find 'wear' regardless of casing", phonetic_search.get_known_fixes("WEaR") == wear_list)
print("    should be not able to find 'too'", phonetic_search.get_known_fixes("too") == [])
print("    should be not able to find 'two'", phonetic_search.get_known_fixes("two") == [])
print("    should be not able to find 'to'", phonetic_search.get_known_fixes("to") == [])

print("Phonetic search with a given set of homophones and phonetic similarities")
phonetic_search.add_homophone('to', 'too')
print("    should be able to add 'to', and 'too', and find it", phonetic_search.get_known_fixes("to") == ['too'])
print("    should be able to find homophones for 'too' as well", phonetic_search.get_known_fixes("too") == ['to'])
print("    should not be able to find 'two' yet", phonetic_search.get_known_fixes("two") == [])
phonetic_search.add_phonetic_similarity('to', 'through')
phonetic_search.add_phonetic_similarity('to', 'blue')
print("    After adding phonetic similarities 'through' and 'blue', they should be found with 'to'", phonetic_search.get_known_fixes("to") == ['too', 'through', 'blue'])
phonetic_search.add_homophone('too', 'two')
print("    After adding two, it should be able to find it before the phonetic similarities", phonetic_search.get_known_fixes("two") == ['to', 'too', 'through', 'blue'])

print("Phonetic search with a new given set of homophones and phonetic similarities")
phonetic_search = PhoneticSearch()
phonetic_search.set_homophones(homophone_contents)
phonetic_search.set_phonetic_similiarities(phonetic_contents)
phonetic_search.update_fix('ad', 'add')
print("    should be able to add 'add', and 'ad' as a homophone", phonetic_search.find_homophones("ad") == ['add'])
print("    should be able to find homophones for 'add' as well", phonetic_search.find_homophones("add") == ['ad'])
phonetic_search.update_fix('add', 'at')
phonetic_search.update_fix('ad', 'at')
phonetic_search.update_fix('ad', 'blue')
print("    After fixing a couple of words ( add -> at, ad -> at, add -> blue), should find only at as a similarity", phonetic_search.get_known_fixes("ad") == ['add', 'at'])