# The blueprint: layout and rules

Where it lives: `.blueprints/` at the root of the git repository the work is in, used without asking. The user may
name another folder. Outside a git repository, suggest a folder, for example the project's own, and ask before
writing the first file. Inside a git repository the blueprint folder should be ignored by git: if it is not, say so
in one line and change nothing.

The task also has a TARS Blueprint Record, the folder `docs/tars-reports/<slug>/`, in `record.md`'s format: at the
root of the git repository, where its files are the ones of the task the developer commits. The slug is one no
other task's record has: when `docs/tars-reports/<slug>/` exists and `.blueprints/<slug>/` does not, pick another,
such as one with the ticket or one more word. The record is off outside a git repository, and in one whose git
ignores `docs/tars-reports/` (`git check-ignore -q docs/tars-reports/`).
The developer can turn it off for one blueprint: a `Record: off` line in the scope's header, or in `iterations.md`'s
header for a pipeline without a scope, as a paragraph of its own with a blank line before it, and a record already
written for it is deleted in the same turn.

The md files are the agent's working state; the user works in chat. The exception is `02-scope.md`, which both
read. Every file can change at any point of the work and shows the current state, not the first plan.

```
.blueprints/
  <slug>/                  "<ticket>-<name>" when there is a ticket, else "<name>"
    00-knowledge.md        facts and decisions used by two or more pipelines, or by the scope
    01-blockers.md         only while a scope blocker is open
    02-scope.md            always
    03-workmap.md          only with more than one pipeline
    postponed.md           only once something is postponed
    recons/                only once a subagent did a recon
      <topic>.md           its report
    pipelines/
      01-<name>/
        knowledge.md       only once the pipeline has facts of its own
        iterations.md      the state of the pipeline
```

- A file is created when it first has content; there are no empty placeholder files. Each file keeps its fixed
  place, so workshop-forge knows where to look.
- A task with one pipeline still uses `pipelines/01-<name>/`.
- A recon done by a subagent, in workshop-craft or workshop-forge, is saved without asking the user: the main agent
  writes the subagent's report to `recons/<topic>.md`, with the date it came back at the top. A report that comes
  back before the blueprint's folder is settled is written once it is. A recon file is not kept up to date: the
  facts the work uses go to the knowledge files as before, and those hold the current version. For what the
  knowledge does not cover, search `recons/` (grep or the harness's search tool) and read only the parts that match.
- Three kinds of blocked, each in its own place:
  - a pipeline waiting for another pipeline, or for one iteration of it: the work map;
  - a question that blocks an iteration: that pipeline's `iterations.md`;
  - a question that blocks the scope: `01-blockers.md`.
- Wording: full words, "pipeline 1", "Converter, iteration 1.2", "Blocker 1". No abbreviations:
  the files are read after a compaction, without the chat around them. In chat the user may write "p2" or "i3".
- No question numbers. A question number (Q12) lives in the chat, where the user answers by it; a file says what the
  answer decided. A decision quotes the user's own words when its why rests on them, and a reference to another
  decision names it by what it says: "since the CSV has no total row", not "since Q12". The one exception is the
  Current line while a question is open: it names the question with its number and title, "waiting on the user (Q12,
  the total row)", so that an answer by number still lands after a compaction; the line is rewritten once the user
  answers. A number already in a file stays as it is: the rule is for what you write, and old lines are not
  rewritten for it.

The format of each file is next to this one: `scope.md`, `knowledge.md`, `blockers.md`, `workmap.md`,
`iterations.md`, `postponed.md`, and the record's, `record.md`.
