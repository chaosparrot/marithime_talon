# Speech recognition

Speech recognition is a  way of interacting with computers. Like keyboards, mouses and touch screens, speech recognition comes with its own set of advantages and disadvantages. Some of these are inherit to all systems, while others are because of design.

Some of the inherit advantages are:
- No screen is needed in order to interact with the computer
- Your body is freed up to relax
- An almost limitless ability to form sentences and thus commands, unlike the limited amount of keys, hotkeys and screen space
- Less in-word spelling mistakes as the models aren't trained on faulty spelled words

Some of the inherit disadvantages are:
- Infinite commands means that a user needs to rely on their memory a lot more than mouse or touch screen users
- The speech quality needs to be good in order for commands to be recognized ( user needs to pronounce well, audio needs to be good )
- Phonetic ambiguity means that words can easily collide with one another ( "ensure" vs "and sure" )
- Correcting mistakes gets messy and complicated
- Words take longer to say than pressing single keypresses

Talon overcomes the final point by allowing for the chaining of commands, which allows for significant speed increases over keyboard usage.

There are, however, a number of design choices that add additional disadvantages
- Needing to say a full command in order for it to properly execute and not accidentally execute another command
- Guessing commands carries a big risk of executing another command by accident
- Having different commands for the same result
- Thus needing to think ( and know ) the full command in order to execute the command
- Relying on invisible state in order to activate or deactivate commands
- Learning commands requires a lot of practice without much guidance
- Needing to use the correct order of words in order to execute the right command ( tab open versus open tab )

For beginners, and for intermediate users that do not regularly use all of the available commands, this slows down their interaction significantly. A lapse in memory, a long pause, or just uncertainty means that the user either:
a ) Looks through the documentation to find the right command, taking them out of their flow for a long duration of time
b ) Guesses a command, knowing that making a wrong guess means making mistakes and slowing down their flow
c ) Stops using the speech recognition and defaults back to other interaction modes (It's me, hi!)

In my opinion, this frustrating experience increases the barrier to entry to any command set, and keeps people from achieving expert level speed increases that elevate the user above keyboard usage. I will attempt to make this command set in a way that is catered towards beginners.

# In the zone

It serves as a reminder that no user, beginner or expert, is using speech recognition as an end. The goal is to execute a task on a computer, anything that comes in between the goal and the user is an obstacle that should ideally be avoided. We want to get out of the way as much as possible. Speech recognition is an interface, and like any good user interface, it needs to be designed with the expectations and limitations of the users in mind.

# Limits on user memory

There are a number of known limitations on peoples memory. For instance, it is generally accepted that short term memory can only hold a certain amount of things ([TODO ADD RESEARCH]) before it is being overwritten by new information. Short term memory is cleared by executing different mental tasks, and the odds of someone doing mental tasks is higher the longer time we wait. 

Long term memory can hold a large amount of information, but it is harder to make things enter long term memory without it being forgotten before. Without repetition, you can forget up to N amount of things you have learned after a single day ([TODO ADD RESEARCH]) . Repetition usually happens a lot when doing voice commands, but it is smart to keep in mind its importance.

When remembering lists of words, which is sort of similar to learning commands, there are two sets of effects we need to account for. The primacy effect, and the recency effect. This basically states that words at the start of lists get more easily remembered, while words in the middle get remembered the least. The words at the end also get remembered well, but only due to short term memory keeping them. If short term memory is cleared, the recency effect is removed ([TODO ADD RESEARCH])

While I have no data on this, I think long term memory keeps a hold of all the known commands, while short term memory is used for remembering state or the previously said words. If the state isn't detectable by senses, it needs to be cleared when the short term memory is cleared in order to reduce errors and reduce unneccesary 'exit' words.

Because of the primacy effect, we need to carefully pick the right starting word of a command in order to make it easier to memorize and guess. 

( TODO: Research remembering verbs, verb nouns, nouns, nouns versus, context nouns, verb context nouns, context noun verbs )

# Performance ( time )

## Execution speed

A lot of the users of talon are temporarily disabled, meaning they suffered an injury which makes typing or using a mouse painful or impossible. These users have remembered their previous workflow and its speed, and get disappointed when they cannot achieve similar speeds with voice. 

## System execution speed

## Speed of memory




# Tasks ( Unprioritized )

