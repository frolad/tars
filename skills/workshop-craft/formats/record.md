# docs/tars-reports/<blueprint name>/: the TARS Blueprint Record

For everyone with the repository: teammates, their sessions and later tasks. It keeps why the task's code is the way
it is and where its pipelines stand, after the blueprint, which stays on one developer's disk, is gone. The agent writes
it from the blueprint, in its own words; it is never a copy of the blueprint's sections. It is never the source of
truth either: the code is. Where it lives and how it is turned off: `layout.md`.

A task's record is a folder with one file per pipeline, named like the pipeline's folder, such as
`01-csv-downloads.md`. Only that pipeline's workshop-forge writes it, so two branches never edit the same file. Each
file reads on its own: what a reader needs from the task's plan is in it, even when another pipeline's file holds the
same.

```
# TARS Blueprint Record: <task, in a few words>: <pipeline, in a few words>

The code is the source of truth: check anything here against the code before relying on it.

State: <in progress | built | done | abandoned> on <branch>.

## Why
<what the task builds and why, and this pipeline's part in it, a few sentences>

## Planning decisions
- <decision>.
  Why: <reason>.
  Rules out: <what this excludes>.

## Not in this task
- <what was left out on purpose>. Why: <reason>.

## What was built
- <behaviour a user or a caller sees, and where it lives>

## Build decisions
- <decision>.
  Why: <reason>.
  Rules out: <what this excludes>.
  ADR: <the ADR's file, once workshop-glossary's merge made the decision one>

## Tried and dropped
- <what was tried or decided first>. Dropped because: <why>.

## Traps
- <behaviour the code does not make obvious, and where it bites>.

## Known issues
- <what is wrong or unchecked in what was built>.

## Postponed
- <work left for later>. Why: <reason>.
```

- The first two lines of each file never change. The line under the heading travels with the file to readers who
  have no TARS.
- State: in progress from the pipeline's first iteration; built once every iteration is done, while the end of the
  pipeline runs (the Done when check, the glossary merge, the review), and in progress again while an iteration it
  adds runs; done at the end of the pipeline; abandoned only when the developer says the pipeline or its task is
  dropped, with why on the same line. It names the branch the file is on. The task has no State of its own.
- Why, Planning decisions and Not in this task come from the task's plan: workshop-craft's scope and knowledge, or
  the session a pipeline was started from. Each holds what a reader needs to read this file: the task's why and this
  pipeline's part in it, the planning decisions this pipeline's work rests on, and what was left out that a reader of
  it would look for.
- Planning decisions are those taken before the build: in workshop-craft, or in the session a pipeline was started
  from. Build decisions are those taken in workshop-forge. Each keeps its Why and Rules out, and a Known cost when it
  has one. A planning decision the build changes moves to Tried and dropped with why it changed; the new one goes
  under Build decisions.
- A decision that workshop-glossary's merge makes an ADR is kept in full, with an `ADR:` line naming its file, in the
  file of the pipeline that ran the merge, a planning decision included.
- Traps are facts of any kind the code does not make obvious: behaviour of a library, a service, the data or the
  repository's own code that someone debugging would trip on.
- Known issues: open bugs, review findings not fixed, checks that never ran, readers of the data nobody checked. A
  problem found and not fixed goes here; Postponed is work left for later, each item with its why.
- Not in this task: entries of the scope's Out of scope, each with its why.
- A section with nothing in it is left out. Every entry is a list item.

## Written when

- In the same turn as the change in the blueprint it reflects: an iteration done, in What was built; a decision, a
  trap, a known issue, a postponed item, a State. Rewrite the entries that changed; never paste the blueprint's text.
- workshop-forge writes its pipeline's file from the first iteration. When the checkout the work runs in has none,
  such as a worktree made after the pipeline started, it writes it there from the blueprint. workshop-craft writes no
  record.
- Nothing in TARS stages or commits a record: the developer commits it with the work.

## Left out

- Question numbers, iteration and pipeline numbers, and any label only the blueprint or a chat explains. A file's
  name is the one exception.
- Decisions about how the work ran: the split, the iteration size, the order.
- How the code works, and file and line references, which drift; a file or folder name may say where something is.
- How runs went, and facts about one machine.
- Status tables, Done when lists, blockers, recons and terms.
- Who decided and when: no names and no dates on entries. `git blame` answers both.

## Never in it

A pushed branch is readable by everyone with the repository.

- Secrets, and where one is kept.
- Names of customers and of people, and handles.
- Production ids, production data and statistics.
- Home paths and hostnames.
- A security hole not fixed yet on the main branch: only "a fix in <area>" until the fix is merged.

The exception is what the task centres on: an id, a GUID, a mention or a customer, such as the default image's GUID,
or the customer whose problem the task debugs.
