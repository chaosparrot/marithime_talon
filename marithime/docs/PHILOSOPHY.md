# Philosophy

There are a couple of things that keep voice control from being as fast as it could be:
- Adding extra commands in between to get to the right result
- Finding the right commands to do the thing you want
- (Mis)remembering commands before saying them
- Punishing error correction

This command set aims to remove in-between steps, lower the cognitive load of commands and reduce the impact of errors. By doing so, it gets out of the way of what you are doing. If it requires more computer processing to understand the intent behind a command, then so be it. 

## Impact on cognitive load

Human memory is a resource that is pretty limited. While we can make an infinite set of commands that does everything we can imagine, there is no possible way to remember every command.
During voice control, the faster we remember a command, the faster we can say that command, the sooner we get to our desired end result. We need to make sure commands are easy to remember so we can aid this process.  

This command set aims to reduce the amount of commands needed to know, every command added must be carefully weighed to see if it's functionality can't just be added to existing commands instead.
It also aims to re-use existing mental models, which is another way of saying "What you read is what you say". No need to calculate how many words we should go right, or do other tasks that we wouldn't think of while using a keyboard either.

## Impact on flow

An ideal command is one that can be used in the flow. Meaning we don't need to either repeat or arbitrarily interupt ourselves because that is just the way the command is formatted. There should be no functional difference in me saying `format bold the best thing` and `format bold`, followed by a pause, and then `the best thing`, after I have thought about what I want to bold. I've already gone through the effort of saying the words, the program should just remember I've said them.

## Impact of errors

Humans will make errors, statistical models will make errors interpreting humans. Errors are here to stay, whether we want to or not. 
Every time we make an error, we need to correct it. At the very least that means acknowledging the error ( ~200ms reaction time ), thinking of the right command, saying the command ( ~400ms, depending on the words ).  
Let's simplify and just use that 600ms delay, and given that we can also make an error in the error correction command, we can be stuck fixing an error for multiple frustrating seconds, before continuing on our way once more.
This frustration leads to further mispronunciations and more errors, leading to more frustration.  

Every command made needs to have thought about the impacts on errors. 
- Can this mistake be avoided?
- Can I easily recover from a mistake in this command?
- Does executing a potentially mistaken command leave me worse of then just ignoring the command altogether?

The easiest fix for a mispronunciation is to just repeat the same command, but better this time. It is intuitive and doesn't require fixing the mistakes that have been made.  
Although it might take longer to repeat the phrase, it still takes less time than thinking about and fixing a mistake.