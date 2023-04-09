Ideally, we would use a fine-tuned model, rather than a convoluted prompt.

I downloaded stackexchange archives that might contain command examples here: https://archive.org/download/stackexchange

The python code here will take a directory name containing the 7zip files and go through finding <code> samples and make a crude attempt at determining what's a command 
example and what's programming code.

Another file feeds the examples to davinci to generate prompts that would produce them (as well as further sus out non-command examaples). I had to cut that somewhere over 
7000 samples as I was blowing through my API budget. I started manually walking through and removing off-the-mark items (examples where it was just a file name, SQL code, 
etc).

I fine tuned using Curie, as Davinci would have been way too expensive.

All this to say, fine tuning didn't go well. Samples looked alright (after running through OpenAI's data cleaning tool), but responses were completely off the rails and not 
at all helpful.
