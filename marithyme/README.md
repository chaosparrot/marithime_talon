
# Marithyme Talon

Marithyme [ ˈmerētīm ] is a command set meant to keep you in the flow while dictating and creating text.
The name is an intentional mispronunciation of maritime, as this package mostly relies on embracing and fixing mistakes.

### How to install

Place this inside of your talon user folder. It should work out of the box, you might need a refresh.

### Voice Command examples

In a text area with the following text: `The quick brown fox jumped over the lazy dog`... 

- `continue` will move the cursor to the back of the text, so just past `dog`, so you can continue dictating.
- `select the quick fox` will select `The quick brown fox`.
- `select the brown ox` will also select `The quick brown fox`.
- `correction the fast brown fox` will select `The quick brown fox` and replace it with `The fast brown fox`.
- `correction skipped over the lazy dog` will select `jumped over the lazy dog` and replace it with `skipped over the lazy dog`.
- At the end of the sentence, saying `over the hazy dog` will select `over the lazy dog` and replace it with `over the hazy dog`.
- At the end of the sentence, saying `the lazy hog` will select `the lazy dog` and replace it with `the lazy hog`.

### Turning off marithyme dictation

If you do not want marithyme dictation, but instead only want to use the selection and correction features, remove the line in `marithyme_settings.talon` that says `tag(): user.marithyme_dictation` and save the file.

You can always say `marithyme` followed by a phrase to use it if you do not want to override the regular dictation insert.

### Testing

If you don't intend to run any unit tests, deleting the `/tests` folder might speed up your Talon voice start up time.

This package has a test suite inside of `/tests` that can run if you turn on the `user.marithyme_testing` value to 1. It will print successful and broken test amounts inside of the Talon log, which can be viewed through the **Talon menu** -> **View log**.

If you want to highlight a specific set of tests, go inside of the specific tests file and add, for example `suite.run()` to the end of the file. This will verbosely print tests inside of the Talon log.

### Privacy statement

Because most software isn't accessible, this package relies on a couple of ways to understand what is inside a text field, and where the caret inside of it is. One of these methods is **locally tracking keystrokes that happen through Talon voice**.
If you are uncomfortable with that, simply delete the `main_context_overrides.py` file, but know that you might not get as well of a performance.

Words that have been inserted that really sound like one another ( Homophones ) are automatically detected and saved in `phonetics/lists/homophones.csv`. 

The auto fixing functionality, that functions like an auto-correct, also saves CSV files containing fixes and the context around it within the `settings/cache` directory. You can disable this feature by setting `user.marithyme_auto_fixing_enabled` to 0 inside `marithyme_settings.talon`.
By default the `settings` directory is kept outside of git so any corrections won't be accidentally commited to an external repository by you.

Note that this package does not have any external website, servers or telemetry. All the functionality happens locally. This privacy statement is to make sure you understand what is going on underneath the hood that might impact you privacy wise. I just wanted to make something that worked smoothly, and unfortunately because of the accessibility APIs across OSes, applications and websites are fractured and / or badly implemented, I had to resort to some of these methods.

TODOs
[ ] - Matrix renaming
[X] - Documentation
[X] - Philosophy
[X] - Refactoring accessibility APIs
[X] - Fixing context keys depending on OS
[X] - Adding integration with tracking
[X] - Adding context for test turning on
[ ] - Testing new APIs
[ ] - Test nested contexts ( Virtual Machine )
[X] - Quill list
[X] - Command pruning
[X] - Prose / phrase capture
[X] - Actions
[X] - Tags
[X] - Lists
[X] - Settings cache