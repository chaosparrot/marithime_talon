from .fix_detection import detect_fix_type

print("Homophone detection")
print("    should not match if we change apples with oranges", detect_fix_type("apples", "oranges") != "homophone")
print("    should not match if we replace apple with apply", detect_fix_type("apple", "apply") != "homophone")
print("    should not match if we replace add with at", detect_fix_type("add", "at") != "homophone")
print("    should not match if we replace bear with pear", detect_fix_type("bear", "pear") != "homophone")
print("    should not match if we replace chase with pace", detect_fix_type("chase", "pace") != "homophone")
print("    should not match if we replace trash with trace", detect_fix_type("thrash", "trace") != "homophone")
print("    should match if we replace add with ad", detect_fix_type("add", "ad") == "homophone")

print("Phonetic similarity detection")
print("    should not match if we change apples with oranges", detect_fix_type("apples", "oranges") != "phonetic")
print("    should match if we replace apple with apply", detect_fix_type("apple", "apply") == "phonetic")
print("    should match if we replace add with at", detect_fix_type("add", "at") == "phonetic")
print("    should match if we replace bear with pear", detect_fix_type("bear", "pear") == "phonetic")
print("    should match if we replace chase with pace", detect_fix_type("chase", "pace") == "phonetic")