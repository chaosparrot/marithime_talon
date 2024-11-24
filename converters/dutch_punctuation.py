from typing import List
from .text_converter import TextConverter

# Class that is used to transform the content of text to another text
class PunctuationConverter(TextConverter):

    punctuation = {
        "punt": ".",
        "komma": ",",
        "puntkomma": ";",
        "koma": ",",
        "spatie": " ",
        "vraagteken": "?",
        "uitroepteken": "!",
        "vraag teken": "?",
        "uitroep teken": "!"
    }

    # Some cases in which it is illegal to make a punctuation because they occupy words
    unformatted_prefix_words = ["een", "de", "het", "dat", "dit", "deze", "mijn",  "je", "jouw", "zijn", "haar", "ons", "hun"]
    unformatted_postfix_words = []

    def match_words(self, words: List[str], previous: str = "", next: str = "") -> bool:
        word_string = " ".join(words).lower()
        for key in self.punctuation:
            if key in word_string:
                return True

        return False

    def convert_words(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        keys = list(self.punctuation.keys())
        matching_tokens = []
        for key in keys:
            matching_tokens.extend(key.split())
        
        converted_words = []
        matching_token_words = []
        for index, word in enumerate(words):
            previous_word = words[index - 1] if index > 0 else "" if previous == "" else previous.split()[-1]
            next_word = words[index + 1] if index + 1 < len(words) else "" if next == "" else next.split()[0]
            
            # For stuff like 'een punt' we do not want to convert punt to '.'
            if ( word in self.punctuation and ( previous_word in self.unformatted_prefix_words or next_word in self.unformatted_postfix_words) ):
                converted_words.extend(matching_token_words)
                matching_token_words = []

                converted_words.append( word )

            # Do a complete replacement if the word is contained within the punctuation
            elif word in self.punctuation:
                converted_words.extend(matching_token_words)
                matching_token_words = []

                converted_words.append(self.convert_text(word))
            
            # Build matching tokens ( for 'uitroep teken' and 'vraag teken' keys )
            elif word in matching_tokens:
                matching_token_words.append(word)
                combined_word = " ".join(matching_token_words)
                if len(matching_token_words) > 1:
                    if combined_word in self.punctuation:
                        converted_words.append(self.convert_text(combined_word))
                        matching_token_words = []
                    else:
                        converted_words.append(matching_token_words.pop(0))
            
            # No match - Don't replace word
            else:
                converted_words.extend(matching_token_words)
                matching_token_words = []

                converted_words.append(word)

        # Clean up kept matching tokens
        converted_words.extend(matching_token_words)

        return converted_words

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
        return text in self.punctuation or text in self.punctuation.values()
    
    def convert_text(self, text: str) -> str:
        return self.punctuation[text]