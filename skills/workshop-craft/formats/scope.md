# 02-scope.md

For the user and the agent. Written in prose, readable without the code. File and line references live in the
knowledge; the scope names a file only when the user needs it to decide. In scope and Out of scope are approved by
the user in chat; the user reads the other sections in workshop-craft's review, which confirms the whole blueprint.

```
# Scope: <task>

Current: <what workshop-craft is doing and what waits on the user>      while workshop-craft runs
Confirmed on: <date>                                            once the user confirms the review

## Task
<what we build and why, one paragraph>

## Current state
<how it works today, what already exists>

## Goal
<the outcome, in one or two sentences>

## Done when
1. <one checkable item>
2. <...>

## In scope
- <...>

## Out of scope
- <what is not in the task>. Decided by <who> on <date>.

## Approach
- <an architecture decision that shapes everything else>

## Who reads what we write
- <reader>: <what it reads>. <covered | not covered | not checked>.

## Constraints
- <a technical limit of this task>

## Risks
- <what could make Done when fail>. How we would notice: <...>.

## Sources
- <ticket, branch, documents, people>

## Changes
- <date>: <change to the scope or to the split>. Found by <the user | pipeline N, Category, iteration M>.
```

| Section | What it answers | Filled by | Changes |
|---|---|---|---|
| Task | What we build and why | The user gives the why, the agent words it | Rarely |
| Current state | How it works today, what exists | The agent from the code; the user corrects it | When a pipeline contradicts it |
| Goal | The outcome | The user | Rarely |
| Done when | Numbered checks that end the task | The user sets them, the agent makes each checkable | Only with the user's OK |
| In scope, Out of scope | What is in and what is explicitly not, with who decided and when | The user decides, the agent proposes | Only with the user's OK |
| Approach | The architecture decisions that shape everything else | Both | Only with the user's OK |
| Who reads what we write | Every reader of the data the task changes, and whether it is covered | The agent, by finding the readers of each table, column or file; the user adds what the code does not show | As pipelines find readers |
| Constraints | Technical limits of this task; standing rules stay in skills and memory | Mostly the user | Rarely |
| Risks | What could make Done when fail, and how we would notice | The agent; the user confirms | As found |
| Sources | Ticket, branch, documents, people | Both | As added |

- The Current line is workshop-craft's status: what it is doing and what waits on the user, as its last message said.
  It is kept up to date without an approval, and gives way to Confirmed on when workshop-craft ends.
- `Record: off`, when the developer turns the task's record off (`layout.md`), is a paragraph of its own after the
  Current or Confirmed on line, with a blank line before it, so that whatever reads the Current line reads it alone.
- Who reads what we write appears only when the task changes data that other parts of the product read.
- Pipelines point back to Done when by number: `Done when: scope 2, 3`.
- Approach is the readable version of the top decisions; the knowledge keeps them with their source and what
  they rule out.
- Changes: one dated line per change to the scope or to the split (a pipeline added or removed, a category
  split, the scope moved), and what found it. It starts once the scope is confirmed; writing the sections the
  first time is not a change. `.blueprints` has no other history.
