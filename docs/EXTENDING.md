# Extending and reusing marithime functionality

You can reuse actions, lists and settings from the marithime package into your own user scripts as well. You can also extend them a need be. All marithime actions, lists and settings are prefixed with `marithime_` so they do not conflict with other packages.

There are exceptions, like [user.phrase_ender](#2-phrase-ender), which extend the file known within the [talonhub/community packages(https://github.com/talonhub/community).

## Lists

### 1. Getting all the known words in the current context / document

By using the list `user.marithime_indexed_words` you can re-use any tokens that have been added to the document. These will include their formatting, so snakecase words for phrases like `change place` will be output as change_place.

If you want to index a lot of things, you might want to use the action [marthime_index_document](#2-set-the-currently-indexed-content).

### 2. Phrase ender

The list `user.phrase_ender` is used to gather all the words that are used to escape a current phrase. By default, `over`, `quil` and `quilt` are phrase ending words, but you can also disable and add additional ones. I like to disable the `over` entry as it can trigger a lot during dictation. Using `user.phrase_ender` in your own voice commands instead of regular `[over]` blocks will help out integrating this across your own scripts.

### 3. Formatters

The list of known formatters is kept within `user.marithime_formatter` in the formatters folder. It is kept in sync with all the formatters available in the standard talonhub/community package, so they all keep the same name.

## Actions

### 1. Re-index the current textarea / opened file

Using `actions.user.marithime_index_textarea()` you can trigger a re-indexation of the current accessible node.

### 2. Set the currently indexed content

Using `actions.user.marithime_index_document('text here')` you can set the entire current context, including the words used in `user.marithime_indexed_words`. In general you shouldn't need this, but if you have a better integration outside of the accessibility checks through some other connection with an IDE or a text editor, this is your best bet as a starting point.

### 3. Set the cursor position

If you have a deeper integration within the software for detecting the current text caret, for example in a text editor, you might want to use `actions.user.marithime_set_caret_position(1, 2)`, where the first argument is the line, and the second argument is the character on that line. In this case, it would be the third character on the second line of the known indexed content.

You might want to pair this with [set the currently indexed content](#2-set-the-currently-indexed-content) first if you have more context.

NOTE that only a single selection is possible at the same time, so multi-cursor usage is not supported.

### 4. Set the selection cursor

If you have a deeper integration within the software for detecting the current text caret, you might want to use `actions.user.marithime_set_caret_selection_position(1, 2, 3, 4)`, where the first argument is the line, and the second argument is the character on that line of the left caret, and the last two arguments are the same but for the right caret. In this case, it would place the selection starting from the third character on the second line of the known indexed content, until the fifth character on the fourth line.

You might want to pair this with [set the currently indexed content](#2-set-the-currently-indexed-content) first if you have more context to ensure everything is kept in sync.

NOTE that only a single selection is possible at the same time, so multi-cursor usage is not supported.

### 5. Estimate the spoken language

Using `actions.user.marithime_estimate_language(text)` and giving it a text value, you can get an estimation of the texts' spoken language, if it is properly supported to be detected. It will default to `english`.

All known languages are available within formatters/dictation_formatter.py

### 6. Estimate formatter based on text

Using `actions.user.marithime_estimate_formatter(text)` and giving it a text value, you can get an estimation of the texts' spoken language, if it is properly supported to be detected. If it cannot figure it out, it will default to 'default'.

All known languages are available within formatters/formatters.py

### 7. Get current selected words

By using `actions.user.marithime_get_selection_text()` you can get access to the currently selected text as it is indexed. Note, if there is no indexed selection, this will return an empty string. So you might want to [reindex the current textarea](#1-re-index-the-current-textarea--opened-file) if you encounter that scenario.

### 8. Get current formatter

By using `actions.user.marithime_get_formatter()` you can get the name of the formatter where the cursor is currently at. The name of this value corresponds to a formatter within formatters/formatters.py, so make sure to make a translation if you wish to use that.

### 9. Set the formatter ( and reformat the current selection )

Using `actions.user.marithime_set_formatter(marithime_formatter)`, where the marithime_formatter is a name of a formatter within formatters/formatters.py, you can set the current formatter and, if a selection is active, automatically reformat the currently selected text to be in that formatter.