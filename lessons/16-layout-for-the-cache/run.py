"""Chapter 16: The same beginning (draft: scene only)."""

from lantern.ui import chapter, draft

chapter("16", "The same beginning", """
Friday 31 July, 08:45. Varma's first question each morning takes the best part of a minute to
begin answering. The second, straight after, starts almost at once.

"Why is it slow only when I arrive?"

Case file 02 chapter 20 found one cause: a timestamp in the system prompt, new every request,
so that nothing after it could be reused.

The cause this morning is the nightly sync. It rewrites the first lines of the context at
01:58 each night.

"So every morning it reads everything again from the top," Okafor says.

"From the first thing that changed," you say.
""")

draft("16")
