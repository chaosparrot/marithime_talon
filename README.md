# Marithime Talon

Marithime [ ˈmerētīm ] is a command set meant to keep you in the flow while dictating and creating text.
The name is an intentional misspelling of maritime, as this package mostly relies on embracing and fixing mistakes.

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

### Parrot noise examples

In `marithime_noise.talon` a bunch of noises have been commented out like cluck repeater noises and the pop noise to remove text contextually. You can enable them one by one by removing the `#` character in front of them, and of course match them with your own parrot noises to make them work.

### Turning off marithime dictation

If you do not want marithime dictation, but instead only want to use the selection and correction features, remove the line in `settings.talon` that says `tag(): user.marithime_dictation` and save the file.

You can always say `marithime` followed by a phrase to use it if you do not want to override the regular dictation insert.

### Removing stutters or repetitions

If you happen to stutter sometimes, or your speech has a lot of repetition, you might want to turn on the remove stutter feature. Change the 0 to a 1 in the following line in the `settings.talon` file.
```
    user.marithime_remove_stutters_in_same_phrase = 0
```

### List of supported programs

Generally this package tries to support all kinds of programs through the accessibility APIs. Though in order to properly know whether they work, the programs are tested manually for support. [The list of supported programs is documented here](programs/SUPPORTED.md)

### Privacy statement

Because most software isn't accessible, this package relies on a couple of ways to understand what is inside a text field, and where the caret inside of it is. One of these methods is **locally tracking keystrokes that happen through Talon voice**.
If you are uncomfortable with that, simply delete the `main_context_overrides.py` file, but know that you might not get as well of a performance.

Words that have been inserted that really sound like one another ( Homophones ) are automatically detected and saved in `phonetics/lists/phonetic_similarities.csv`. 

The auto fixing functionality, that functions like an auto-correct, also saves CSV files containing fixes and the context around it within the `settings/cache` directory. You can disable this feature by setting `user.marithime_auto_fixing_enabled` to 0 inside `settings.talon`.
By default the `settings` directory is kept outside of git so any corrections won't be accidentally commited to an external repository by you.

Note that this package does not have any external website, servers or telemetry. All the functionality happens locally. This privacy statement is to make sure you understand what is going on underneath the hood that might impact you privacy wise. I just wanted to make something that worked smoothly, and unfortunately because of the accessibility APIs across OSes, applications and websites are fractured and / or badly implemented, I had to resort to some of these methods.

### Testing

If you don't intend to run any unit tests, deleting the `/tests` folder might speed up your Talon Voice start up time.

This package has a test suite inside of `/tests` that can run if you turn on the `user.marithime_testing` value to 1. It will print successful and broken test amounts inside of the Talon log, which can be viewed through the **Talon menu** -> **View log**.

If you want to highlight a specific set of tests, go inside of the specific tests file and add, for example `suite.run()` to the end of the file. This will verbosely print tests inside of the Talon log.

### Contributing and features to potentially build

#### Documentation

[] - Create a usage and installation video  
Videos seem to speak to people more than written text does, so accompany this with a video as well

[] - Extension possibilities for other packages  
There's a ton of ways other packages can make use of our captures, settings and detections, but we will need to document them so they are easier to reuse as well.

#### Dictation

[~] - Terminator words  
Right now the word `quill` is used, instead onf the word `over`, to terminate a command. We probably want to extend this a bit, though we need to take into account that they need to not only be used in commands, but filtered out in other ways.

[ ] - Making automatic fixing work  
This feature has been implemented but it hasn't been tested very well. There's probably a lot of research left to be done.

[ ] - Incremental text field updates  
Right now, indexing a text field causes it to lose all meaning with regards to formatters used. This causes problems with trying to re-use a formatter that was used.

[ ] - Zero width space indexation selection fix  
When a zero width space indexation is used, it is possible that a current selection is removed. We can fix that selection afterwards so we don't have issues where content is removed unnecessarily

[x] - Repeater noises - Looping through selections and corrections  
Most of this architecture is already built, but since there has been a refactoring this functionality would probably loop between two values right now rather than go through the list like a 

[ ] - Cycle through corrections with phonetic combinations  
There are some words, like 'a fix' and 'affix' that could be cycled through, but currently it only cycles through words that are single matches instead. It should cycle through these fixes as well, but for that we need to cycle through combinations properly.

[x] - Remove noise - Enable remove text contextually  
This is mostly supported, but it needs to be tested in terminals as well. We could probably have a noise file to configure noises.

[x] - Remove noise - Remove character contextually  
If you're spelling letters one by one, you probably do not want to remove an entire word like it usually does right now. In that case, we should remove only a single character per noise.

[x] - Continue noise  
We could already create a noise that immediately skips to the end of the sentence. 

[ ] - Implement flow for digits  
Right now, you still need to say `numb zero` every time between commands. We can detect if we should allow digits, periods and other kinds of formatters as single words if we can be very certain that the next character will be 

[ ] - Word wrap detection  
We need to find a way to deal with word wrap, meaning things being on a single line, but visually ( and most importantly, keyboard relatively ) they are on multiple lines. Our current Up and Down arrow key pressing does not deal with that.

[x] - Add clipboard pasting insert support
Right now it isn't possible to use clipboard pasting as a way to insert things rather than typing out the characters one by one. This makes the insertion slower than it could be. This can be done with 'Ctrl+C' and 'Ctrl+V', or 'Ctrl+Shift+C' and 'Ctrl+Shift+V' in terminals. Though we probably want to use `action.edit.paste()` to make it compatible with other packages. We do need to be aware that in terminals there is a possibility that `Remove trailing white-space when pasting` is turned on, which might cause desyncs.

[x] - Refactor last action type into state machine
Technically the repetition flow is an implicit state machine that doesn't quite belong in either the InputFixer or the VirtualBuffer. Ideally this gets moved to its own class so it can be unit tested like the rest. Now it will just have to be manually tested like some other context related stuff. With it, tackle the following known bugs:
- Formatting isn't taken into account properly - should use the same formatting if it is mixed
- Skipping a correction does not move to the next best match but instead to the current match, this is hard to fix because we don't want to skip over elements twice
- Skipping to a next correction starts with the initial correction if it was a direct match
- Repeating a self repair should fix like a correction should - With the text first
- Skipping a self repair cycle should append the value instead
- Selections do not work when repeating the same correction, but having another correction be a closer match - Expected is it selecting the first correction instead TOKEN-WISE

[ ] - Known bug: SKIP_SELF_REPAIR target is off by one sometimes

[ ] - Improve outside events and extend events with selection  
While making the state machine, I found out that while a lot of fix events ARE covered by the flows, doing manual selections with 'press shift left ten times' is not, neither is extending the select, because it doesn't follow the select flow. While I think this workflow won't be done often, for completeness sake it should be added to ensure the InputFixer can properly track what changes were made for automatic fixes later.

#### Programs

[ ] - Improved MacOS support  
While there's programs where it nails the accessibility API pretty well, others just don't connect properly with finding the right focused element. We'll need to address these one by one unfortunately, because accessibility APIs are all over the place from program to program.

[ ] - Text editor support  
This means we should be able to support vim, nano and other keybindings. This runs into the same issues as using a terminal does however, namely poor accessibility support and hard to detect when something is inside of a text editor in the first place. Another is no line wrapping when reaching the start or end of the line and key-pressing beyond that boundary.

[x] - Single line detection  
Some fields, like name fields, do not have the possibility to add multiple lines. In that case, we probably want to either clear the buffer or simply not allow the enter to change the field. We should probably do a refresh if we are in an accessible field, and a clear in a terminal. 

[ ] - Accessiblity input tags  
We can detect a field type, like email, phone number etc from the accessibility APIs. That means we could expose that information for other packages to use as well, so you can say `Homer` to input `homer@odyssey.com` for example.

[ ] - Combobox support  
This one is going to be a pretty complex one without a lot of pay off, because it requires looking through the accessibility tree, and comboboxes tend to be implemented in all kinds of gnarly ways across programs and the web.

[ ] - Virtual machine support  
I haven't tested this on usages where you have a virtual machine with a different operating system inside of that VM. I'm not sure if the accessibility APIs work as well, as well as the clip board or the other detections in there. Because of the complexity if this doesn't properly work, I'm unlikely to take a lot of time into it.

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

### Acknowledgements

This repository started off as a clone from the [talon community repository](https://github.com/talonhub/community), but as time went on and my changes became less and less specialized for my own needs, I decided to start making a package of its own.  
A lot of inspiration was gained from the community repository, like formatters, but I've tried to make this repository stand on its own as much as possible. As such, I've only included the history of that previous repository from the start of my fork on July 27th, 2023, as I hadn't done any updating of my community talon files since then because of potential merge conflicts.

Any remnants of code that maybe accidentally left over from the original community repository, has been made by [the contributors of that repository](https://github.com/talonhub/community/graphs/contributors).