# .blueprints/glossary-bootstrap/bootstrap.md

The run's working state, for the agent. It holds only what is not answered yet: approved entries are in the
glossary and the ADRs, and leave this file. The Current line is the way back in after a compaction or in a new
session. The file is deleted at the end of the run.

```
# Glossary bootstrap

Current: <Area>, group <n>: <state, and what it waits for>.

## Plan

Scope: <the areas>. Confirmed by the user on <date>.
Size: <small | large>, mined <inline | by one subagent per area>.
Glossary: <file>, <existing, in its own format | new>. ADRs: <folder>.

## Areas

1. <Area> (<paths>): <not mined | mined | group <n> proposed | done>.

## Proposed

<the group as it was shown to the user: each entry numbered and as it will be written, each question with its
number, its options and the recommendation>

## Candidates

<one section per mined area, in the shape of `../mining.md`, without the candidates already proposed>

## Rename candidates

- <Term>: the code's `<Name>`.
```

- Areas are listed in the plan's order. An area's state changes in the turn it changes.
- Proposed holds the group exactly as shown, so an answer by number is read right after a compaction. Once the
  answer is written, the next group replaces it.
- A candidate leaves the file when it is answered: written, dropped, or merged into another term.
- Rename candidates collect every term written with an `_In the code_` line, for the last message.
