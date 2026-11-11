<!-- status: draft -->
# Chapter 21: Memory in a box

**Concept:** the frameworks review: the same memory tasks on the lab's own store and on memory libraries, to see what each decides for you.

## The scene

Thursday 6 August, 14:00. Headquarters approve of memory. They have sent a list of libraries
that provide it, and Strand's covering note says any of them would spare the unit the work of
keeping its own.

Varma reads the list as she read the last three. "Which of these run in this building?"

That is the first test and it is not a small one. A memory library that calls a hosted model to
decide what to remember has sent the evidence out of the door.

"And the second test," Okafor says. "Which of them can tell me who wrote an entry."

## The concept

*Draft.* The frameworks review: the same memory tasks on the lab's own store and on memory libraries, to see what each decides for you.

## How it works

*Draft. Planned:*

- The same tasks (store, recall, retract, audit) on the lab's own store and on each library that runs offline.
- What each library decides without asking: what to extract, when to overwrite, what to forget.
- Network calls made by each during the run, counted, and a recommendation.

## The nuances

*Draft. Planned:*

- A library that extracts memories with a model has made the model an author.
- Automatic overwriting of 'outdated' facts is retraction without a record.
- A library surveyed from its documents is not a library run; the review says which is which.

## Run it

```bash
make lesson N=21
```

## What you should see

*Draft.* A real screenshot of the run goes here (`--shot`, then `scripts/svg_to_png.py`), with
notes on what the run showed and what it did not.

## Try this

1. Run one library with the network cable out.
2. Store the eighth entry through each library and ask who wrote it.

## What the evidence now shows

*Draft. Planned, and rewritten from the run once the chapter is built:*

The unit knows which memory libraries run inside the building, what each decided on its behalf, and which it would recommend.

**Next:** [Chapter 22: The case review](../22-common-pitfalls/README.md)
