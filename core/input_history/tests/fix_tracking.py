from ..input_fixer import InputFixer
from ...phonetics.phonetics import PhoneticSearch

def get_input_fixer() -> InputFixer:
    input_fixer = InputFixer("en", "test", None)
    search = PhoneticSearch()
    search.set_homophones("")
    search.set_phonetic_similiarities("")
    input_fixer.phonetic_search = search
    return input_fixer

input_fixer = get_input_fixer()
print( "Using an empty input fixer and phonetic search")
print( "    Tracking a fix for a single word 'the night in shining armour' -> 'the knight in shining armour'")
input_fixer.track_fix("night in shining armour", "knight in shining armour", "the", "")
print( "        Should add the homophone 'night' and 'knight' because of the similarity", len(input_fixer.phonetic_search.find_homophones("night")) >= 0)
print( "        Should track the fix from night and knight in the input fixer", input_fixer.get_key("night", "knight") in input_fixer.done_fixes)
print( "    Tracking a fix for a single word 'the night in black armour' -> 'the knight in black armour'")
input_fixer.track_fix("night in black armour", "knight in black armour", "the", "")
print( "        Should have 'night' saved as a full context fix", "night" in input_fixer.known_fixes)
print( "    Inserting 'the night in dark armour'...")
print( "        Should automatically fix 'night' to 'knight'", input_fixer.automatic_fix("night", "the", "in") == "knight")
print( "    Inserting 'a night in March'...")
print( "        Should not change 'night'", input_fixer.automatic_fix("night", "a", "in") == "night")