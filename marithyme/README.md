
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

### Privacy statement

Because most software isn't accessible, this package relies on a couple of ways to understand what is inside a text field, and where the caret inside of it is. One of these methods is **locally tracking keystrokes that happen through Talon voice**.
If you are uncomfortable with that, simply delete the `main_context_overrides.py` file, but know that you might not get as well of a performance.

Words that have been inserted that really sound like one another ( Homophones ) are automatically detected and saved in `phonetics/lists/homophones.csv`. 

The auto fixing functionality, that functions like an auto-correct, also saves CSV files containing fixes and the context around it within the `settings/cache` directory. You can disable this feature by setting `user.marithyme_auto_fixing_enabled` to 0 inside `marithyme_settings.talon`.
By default the `settings` directory is kept outside of git so any corrections won't be accidentally commited to an external repository by you.

Note that this package does not have any external website, servers or telemetry. All the functionality happens locally. This privacy statement is to make sure you understand what is going on underneath the hood that might impact you privacy wise. I just wanted to make something that worked smoothly, and unfortunately because of the accessibility APIs across OSes, applications and websites are fractured and / or badly implemented, I had to resort to some of these methods.

### Testing

If you don't intend to run any unit tests, deleting the `/tests` folder might speed up your Talon voice start up time.

This package has a test suite inside of `/tests` that can run if you turn on the `user.marithyme_testing` value to 1. It will print successful and broken test amounts inside of the Talon log, which can be viewed through the **Talon menu** -> **View log**.

If you want to highlight a specific set of tests, go inside of the specific tests file and add, for example `suite.run()` to the end of the file. This will verbosely print tests inside of the Talon log.

### Contributing and features to potentially build

#### Documentation

[ ] - Create a usage and installation video
Videos seem to speak to people more than written text does, so accompany this with a video as well

[ ] - Extension possibilities for other packages
There's a ton of ways other packages can make use of our captures, settings and detections, but we will need to document them so they are easier to reuse as well.

#### Dictation

[ ] - Similarity matching by meaning 
This boils down to matching `an` and `the` to be similar despite them being phonetically different.
We can add something configurable so its easy for users to extend.

[ ] - Terminator words
Right now the word `quill` is used, instead of the word `over`, to terminate a command. We probably want to extend this a bit, though we need to take into account that they need to not only be used in commands, but filtered out in other ways.

[ ] - Making automatic fixing work
This feature has been implemented but it hasn't been tested very well. There's probably a lot of research left to be done.

[ ] - Incremental text field updates
Right now, indexing a text field causes it to lose all meaning with regards to formatters used. This causes problems with trying to re-use a formatter that was used.

[ ] - Repeater noises - Looping through selections and corrections
Most of this architecture is already built, but since there has been a refactoring this functionality would probably loop between two values right now rather than go through the list like a 

[ ] - Repeater noises - Looping through homophones
We know the homophones, we just need to find a way to replace a selected word with a known homophone and have it work with a repeater noise. I dislike the `phones` menu as it forces you to pick one, but it's much faster to just mindlessly flick through them with a noise since the list often only has like 2 to 3 choices anyway.

[ ] - Remove noise - Enable remove text contextually
This is mostly supported, but it needs to be tested in terminals as well. We could probably have a noise file to configure noises.

[ ] - Remove noise - Remove character contextually
If you're spelling letters one by one, you probably do not want to remove an entire word like it usually does right now. In that case, we should remove only a single character per noise.

[ ] - Continue noise
We could already create a noise that immediately skips to the end of the sentence. 

[ ] - Previous / next paragraph / sentence
We could make it easier to loop through sentences since we already have the buffer anyway, but I'm hesitant to just add new features that require more commands. Perhaps we could find a middle with with commented out commands for advanced usages.

[ ] - Implement flow for digits
Right now, you still need to say `numb zero` every time between commands. We can detect if we should allow digits, periods and other kinds of formatters as single words if we can be very certain that the next character will be 

#### Programs

[ ] - Terminal support
Right now terminals have a ton of issues because they do not allow for text selection, have painful accessibility support, and use a ton of custom key binds that don't correlate with other document builders.

[ ] - Single line detection / support
Some fields, like name fields, do not have the possibility to add multiple lines. In that case, we probably want to either clear the buffer or simply not allow the enter to change the field. We should probably do a refresh if we are in an accessible field, and a clear in a terminal.

[ ] - Virtual machine support
I haven't tested this on usages where you have a virtual machine with a different operating system inside of that VM. I'm not sure if the accessibility APIs work as well, as well as the clip board or the other detections in there. Because of the complexity if this doesn't properly work, I'm unlikely to take a lot of time into it.

[ ] - Accessiblity input tags
We can detect a field type, like email, phone number etc from the accessibility APIs. That means we could expose that information for other packages to use as well, so you can say `Homer` to input `homer@odyssey.com` for example.

[ ] - Combobox support
This one is going to be a pretty complex one without a lot of pay off, because it requires looking through the accessibility tree, and comboboxes tend to be implemented in all kinds of gnarly ways across programs and the web.

#### Code creation

[ ] - Automatic formatter detection / selection
This feature has been implemented but still has plenty of room for improvement

[ ] - Formatter commands
Because the formatters haven't been implemented as well, the commands to select them haven't been created.

[ ] - Formatter prediction
Essentially, allowing a specific formatter to be used if it detects that we are about to create a variable, parameter or function name. Every language has their own rules about snake case, camel case and pascal case that we could automatically use.

[ ] - Operator formatter
There are a lot of things we can do to make creating operators simpler. For example, if we say `plus` we most likely want ` + ` to appear, but if we follow it up with `equals`, we want it to change to ` += ` instead.

[ ] - Codebase indexation
This is partially implemented for the current text area, but we could do it for more of a code base somehow. This will most likely bring memory challenges with it, so I'm not sure how this doable this is in an efficient way, perhaps it needs to be IDE depedant. But I really don't feel like putting a lot of time into this right now due to its complexity.