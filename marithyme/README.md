
# Marithyme Talon

Marithyme [ ˈmerētīm ] is a command set meant to keep you in the flow while dictating and creating text.

## Philosophy

There are a couple of things that keep voice control from being as fast as it could be:
- Punishing error correction
- Finding the right commands to do the thing you want
- (Mis)remembering commands before saying them
- Adding extra commands in between to get to the right result

This command set aims to reduce the impact of errors, lower the cognitive load of commands and remove the in-between steps required. By doing so, it gets out of the way of what you are doing. If it requires more computer processing to understand the intent behind a command, then so be it. 

### Impact of errors

Humans will make errors, statistical models will make errors interpreting humans. Errors are here to stay, whether we want to or not. 
Every time we make an error, we need to correct it. At the very least that means acknowledging the error ( ~200ms reaction time ), thinking of the right command, saying the command ( ~400ms, depending on the words ). Let's simplify and just use that 600ms delay, and given that we can also make an error in the error correction command, we can be stuck fixing an error for multiple frustrating seconds, before continuing on our way once more.

... 

TODOs
[ ] - Matrix renaming
[ ] - Documentation
[ ] - Philosophy
[X] - Refactoring accessibility APIs
[ ] - Test nested contexts ( Virtual Machine )
[X] - Fixing context keys depending on OS
[X] - Adding integration with tracking
[X] - Adding context for test turning on
[ ] - Testing new APIs
[X] - Quill list
[X] - Command pruning
[ ] - Prose / phrase capture?
[X] - Actions
[X] - Tags
[X] - Lists