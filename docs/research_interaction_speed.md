# Interaction speed

In order to determine when using speech recognition becomes faster than typing, I set up an experiment to know what the minimum time of execution is given no software or hardware delays. In order to test this, I recorded sets of three experiments which took an audio recording of the execution. For typing, the audio recording of the keys pressed is used. For dictating, the raw phrase was said and recorded. For commands, the phrase was altered and recorded. The data shown is in seconds, and denotes the duration between the start and end of the execution. Lower time means faster execution.

Some mistakes were made during typing or dictating, which causes some of the delays shown in the attempts and makes the data slightly more realistic in a real world setting.
Mistakes are annotated with an *, while corrected mistakes are annotated with **

## Data

**Single syllable**
air
( Command: spell air )

|# attempt|Typing|Dictating|Command|
|---|---|---|---|
|1|0.302|0.220|0.395|
|2|0.465*|0.238|0.447|
|3|0.342|0.226|0.464|
|4|0.378|0.226|0.441|
|5|0.371|0.209|0.441|
|6|0.256|0.261|0.453|
|7|0.359|0.233|0.406|
|8|0.285|0.232|0.389|
|9|0.325|0.249|0.430|
|10|0.319|0.215|0.412|
|avg|0.3402|**0.2309**|0.4278|

**Triple syllable word**
manager
( Command: word manager )

|# attempt|Typing|Dictating|Command*|
|---|---|---|---|
|1|0.621|0.424|0.737|
|2|0.726|0.476|0.720|
|3|0.661|0.418|0.726|
|4|0.819**|0.465|0.848|
|5|0.668|0.424|0.790|
|6|0.691|0.505|0.801|
|7|0.603|0.552|0.731|
|8|0.627|0.424|0.813|
|9|0.609|0.465|0.911|
|10|0.638|0.488|0.737|
|avg|0.6663|**0.4641**|0.7814|

**Pangram**
The quick brown fox jumps over the lazy fox.
( Command: Title the over quick brown fox jumps over the lazy dog period )

|# attempt|Typing|Dictating|Command|
|---|---|---|---|
|1|5.570**|2.002|3.541|
|2|4.841*|2.014|3.448|
|3|4.050|2.316|3.303*|
|4|4.384|2.374|3.348|
|5|4.430|2.403|3.495|
|6|3.824|2.015*|3.292|
|7|4.106|2.159|3.222|
|8|4.120*|2.409|3.170|
|9|4.007|2.310|3.118|
|10|4.257|2.107|3.268|
|avg|4.3589|**2.2109**|3.3205|

## Conclusion

Although the number of experiments is small, a trend can easily be recognized.
Under perfect conditions, dictating is faster than typing, and command usage is slower.
The longer the words and phrases become, the more advantageous it is to use speech recognition over typing speed wise.

## Recommendations

Due to the trend that longer commands means more time savings, a command set should be made with encouraging chaining long commands in mind. While the data shown relies on a zero-delay execution, it can be clearly seen that the time margins between speech recogntion and typing become more lenient. Even with a delay of 1s for speech recognition, unrealistically long delay given the fast execution of Talon commands, the pangram experiment performs better for speech recognition than typing.