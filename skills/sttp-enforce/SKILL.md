---
name: sttp-enforce
description: Bring the files under a path to sttp's rules. The first turn analyses the files and lists what sttp would change, by kind (prose, repetition, headings, tables, code comments, contradictions), each item numbered with a recommendation; the files are written after the user picks.
disable-model-invocation: true
---

sttp and sttp-software-engineering apply. `/sttp-enforce <path>` (`$sttp-enforce` in Codex) brings the text of the files under a path, a file, a folder or a package, to sttp's rules. What sttp says of an answer holds for a file: the point first, only the subject, every fact kept, nothing the reader can do without. The first turn is the analysis; the files are written after the user picks what to change.

## The files

- The path is a file, or a folder with every file under it that git does not ignore. With no path, ask for one.
- Left out, and named in one line in the analysis: generated files, vendored code, lock files, binaries, licenses and other legal text, and text whose form is set elsewhere, such as test fixtures and data a test reads, or a changelog in a fixed format.
- A file with changes that are not staged is named in the analysis: `git diff` would show them mixed with this run's.
- Outside a git repository there is no diff to review: suggest a folder for copies of the old files, and ask.
- More files than one turn can read in full: say how many, suggest going folder by folder, and ask.

## The analysis: the first turn

Nothing is written in it. Read every file in full, then list what sttp would change, by kind. Each kind is numbered and each item under it too (2.1, 2.2), with where it is (file:line), a short before and after, and a recommendation: apply or leave.

- **Prose**: preamble, filler, hedging, self-narration, speechmaking, closing lines, adjectives where a number or a name fits, a point buried after its setup.
- **Repetition**: one fact or rule stated in two places. Name both, and the one that stays: where the reader needs it. Two files read separately, such as a README and a docs page, may each need it: then recommend leaving it.
- **Headings**: one over a single short paragraph, or one that says nothing the text does not. A heading that another file, a link or the code refers to stays. In an instruction file, a heading or the bold name of a rule or a step is how the reader and other text find it: recommend leaving it.
- **Tables**: one that holds a single list becomes a list. One that compares across two dimensions stays.
- **Lists and decoration**: a list of items that are not parallel becomes prose. Bold, emoji, rules and badges that carry nothing go.
- **Code**: comments that restate the line, section banners, docstrings that repeat the signature, as sttp-software-coding says. The code, and the strings it prints or shows, are behaviour and stay.
- **Descriptions**: the description of a skill, a command or a tool is what triggers it. Tightened only when picked, with every trigger phrase kept.
- **Contradictions**: two places that say different things, such as 400 days in one file and a year in another. A pick never settles one: each is a question with the options and a recommendation, and the user's answer is what gets written.

A pattern repeated across the files, such as 40 lines that open with "Note that", is one item with its count and two examples. Each repetition and each contradiction is an item of its own.

Give the size of each file in tokens (characters / 4), now and after the recommended items. End with the question: which items to apply, such as "all recommended", "1, 3, 4.2" or "all except 2.1".

## Writing: the turn of the answer

Apply what the user picked and nothing else.

- Every fact, number, condition, exception, warning and step stays, in its order. Names, paths, commands, quotes and code stay exact.
- A term the files use as a term keeps its spelling: other files and the code refer to it. The file's language, spelling and line wrapping stay too, so the diff shows only the change.
- In an instruction file, such as a skill, a prompt, CLAUDE.md or AGENTS.md, the reader is a model that acts on every sentence. A why stays when it lets the reader handle a case the rule does not name; a why that only motivates goes.
- With more than five files, write them in parallel, one subagent per file, where the harness has subagents. Give each the file, its picked items, and the paths of sttp's SKILL.md and this file.
- When the analysis is no longer in context, such as after a compaction, run it again and show it instead of writing: the answer's numbers belong to the analysis shown.

## The check

Compare each file written with its old version, by `git diff` or the copy: every fact, rule, number, name, path, command and warning of the old text is in the new one, or was cut as a picked repetition and still stands where the item said. Put back what was lost. In a code file, the diff touches only comments and docstrings.

## The report

The size of each file in tokens, before and after. Then, only when there is one: an item not applied and why, what the check put back, a contradiction still open. No walkthrough; the diff shows the changes. Nothing is staged or committed: the commit is the user's.
