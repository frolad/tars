# TARS Blueprint Record: the TARS Blueprint Record: skills and tests

The code is the source of truth: check anything here against the code before relying on it.

State: done on worktree-task-records.

## Why
TARS keeps a task's working notes, its blueprint, in `.blueprints/`, which git ignores: they stay on one developer's
disk, with the task's decisions, traps and known bugs. Ten real blueprints, and the
session transcripts that used them, showed later tasks working out the same facts two or three times, a rework losing
seven of the first attempt's known bugs, and twelve decisions losing their reasons to ADRs that were never committed.
This task gives every TARS task a committed record of why its code is the way it is and where its pipelines stand.
The agent writes it; copying the blueprint's sections would bring stale text, task labels and sensitive lines with
them. This pipeline built all of it: the skills' rules and their tests.

## Planning decisions
- A committed record per task, not ADRs.
  Why: most task decisions fail the ADR tests (hard to reverse, surprising, a real trade-off), and every task reads
  the ADRs of its area, so task decisions there would fill every session's context.
  Rules out: storing every task decision as an ADR.
- The record keeps why the code is the way it is and where the work stands, for anyone with the repository, and reads
  without the blueprint.
  Why: later debugging needs the reasons; teammates need the live state and have only the repository.
  Rules out: decisions only; a status page only; labels and question numbers only a blueprint or a chat explains.
- Only the record is committed; `.blueprints/` stays ignored by git as a whole.
  Why: searches of the code stay clean, and the working notes stay private.
  Rules out: committing the knowledge files through a `.gitignore` whitelist; a `.ignore` file for ripgrep.
- The agent writes the record; it is never a copy of the blueprint's sections.
  Why: later work needed reasons, reversals, traps and open bugs, and never read iteration lines, work maps, Done when
  lists, blockers, terms or recons; copied sections bring drift, stale text, labels and sensitive lines.
  Rules out: copying sections; generating the record with a script; a full status table.
- Planning decisions and build decisions are separate sections, and a planning decision the build changes moves to
  Tried and dropped with why.
  Why: the decision sections show only what holds now; replaced decisions left in place read as current.
  Rules out: one Decisions section; editing a decision in place with a Changed line.
- No names and no dates on entries.
  Why: `git blame` answers who and when.
  Rules out: "Decided by <name> on <date>".
- Traps are facts of any kind the code does not make obvious.
  Why: what later tasks worked out again shared that, wherever it lived: in a library, a service, the data or the
  repository's own code.
  Rules out: only facts about outside tools; all facts.
- Known issues and Postponed are separate, and there is no section for what was checked and found not affected.
  Why: someone debugging and someone picking up later work ask different questions; the decisions that rest on those
  checks are recorded anyway.
  Rules out: one section for both; a "checked and not affected" section.
- Never in a record: secrets and where they are kept, names of customers and people, production ids and data, home
  paths, hostnames; a security hole only as "a fix in <area>" until its fix is merged. The exception is what the task
  centres on.
  Why: a pushed branch is readable by everyone with the repository, and real blueprints held all of these.
  Rules out: leaving it to the developer's review of the diff; describing a hole before its fix ships.
- The record is on in every git repository TARS runs in; off where git ignores its folder, and off for one blueprint
  with a `Record: off` line, which deletes a record already written.
  Why: no one has to remember to turn it on; an ignored file is never committed anyway; the line survives compactions
  and new sessions; a record nobody updates goes stale.
  Rules out: only repositories where the folder exists; a command for the switch; no switch.
- The skills call it the TARS Blueprint Record.
  Why: "report" already means workshop-forge's message at the end of each iteration.
  Rules out: calling it the report.
- The record's rules live in one format file, read before the first record is written; the skills say only when to
  write it.
  Why: one place to change, read like every other blueprint file's format.
  Rules out: the rules written into each skill.

## Not in this task
- Records for existing blueprints. Why: running ones get theirs on their next workshop-forge run; a finished task's
  record costs a session, so only when asked.
- A version bump and the Codex reinstall. Why: a separate step in the skill set's plan.
- A record for workshop-glossary-bootstrap. Why: it builds a project's glossary, not a task.
- The record in /tars-doctor or the mod's status line. Why: the record is for readers of the repository, not for the
  running session.
- Problems found in other repositories' blueprints while studying them. Why: they belong to those tasks.

## What was built
- The record's format and rules: `skills/workshop-craft/formats/record.md`, with where it lives and how it is turned
  off in `skills/workshop-craft/formats/layout.md`.
- workshop-craft searches `docs/tars-reports/` for leads before its recon and picks a blueprint name no other task's
  record has; it writes no record.
- workshop-forge keeps its pipeline's file current in the turn something changes, writes it when the checkout has
  none, sets it to built once every iteration is done, then to done or abandoned.
- workshop-glossary's merge keeps a decision that became an ADR in the pipeline's file.
- sttp-software-engineering tells every session to search `docs/tars-reports/` whenever a record can help, and to
  check what it says against the code.
- The README describes the record and how to turn it off.
- The workshop-forge tests let the record's files through as the ones written outside `.blueprints`, and never count
  them as changed code; the workshop-craft tests fail on any record, since it writes none. New cases check that
  workshop-forge adds a decision and a trap to its pipeline's file in the same turn, writes that file in a pipeline
  started from a session without a customer's name or a home path from the session, sets it to built when every
  iteration is done, and to done at the end of the pipeline. A file the tests' `diff` cannot read fails the check that
  nothing outside `.blueprints` changed, with diff's message.

## Build decisions
- The record is never behind: the skills change it in the same turn as an iteration done, a decision, a trap, a known
  issue, a postponed item or a State; nothing checks it from outside.
  Why: any commit, mid-task included, carries the record so far; the skills' test runs kept the record current
  without a check; a check of the blueprint's file times would also fire on knowledge edits the record leaves out.
  Rules out: updates only at review stops or at the end of a pipeline; a reminder from the prompt hook.
- The code is always the source of truth, never a record. Records are useful, and the agent searches them at any
  point they can help, knowing a record can be out of date or behind the code; workshop-craft also searches them for
  the task's area before its recon.
  Why: no session found an earlier blueprint on its own; a record can only be out of date, and the code cannot.
  Rules out: reading every record before work, as the glossary and ADRs are read; a search rule in every grill.
- The record is a folder per task with one file per pipeline, written only by that pipeline's workshop-forge. Each
  file reads on its own: the task's Why, the planning decisions its pipeline's work rests on and what was left out
  are copied in, even when another pipeline's file holds the same. The task has no file and no State of its own.
  Why: no two branches edit the same file, so merges never conflict over records, and no branch needs to know it
  holds the last pipeline; a folder is the task, with no name prefix shared with another task.
  Rules out: one file per task; flat names with the pipeline in them; a task's file; a task State.
- A pipeline's State is in progress from its first iteration, built once every iteration is done, while the end of
  the pipeline runs (the Done when check, the glossary merge, the review), done after it, or abandoned. An iteration
  the end of the pipeline adds puts it back to in progress until that iteration is done.
  Why: a pipeline whose iterations were all built and committed read as unfinished while its end steps waited.
  Rules out: in progress until the end of the pipeline; done as soon as the last iteration is.
- A decision that becomes an ADR stays in full, with an `ADR:` line, in the file of the pipeline that ran the merge,
  a planning decision included.
  Why: the reason survives when the ADR file is lost or renumbered, and only that pipeline's workshop-forge writes
  its file.
  Rules out: moving it to the ADR and leaving a pointer.
- workshop-forge writes its pipeline's file from the first iteration, also in a checkout that has none, from the
  blueprint; workshop-craft writes no record.
  Why: never behind; a worktree made after the pipeline started gets no untracked files; a file only its pipeline
  writes needs no commit before the pipelines branch.
  Rules out: workshop-craft writing a file the developer commits before the pipelines start.
- A pipeline is abandoned only when the developer says it or its task is dropped.
  Why: the agent cannot tell a paused task from a dropped one, and a wrong "abandoned" misleads every reader.
  Rules out: workshop-craft asking about an earlier record of the same work still in progress.
- Every record starts with its heading and the line saying the code is the source of truth, and the rule is also in
  sttp-software-engineering, which every session has from its start.
  Why: the agent knows the rule before it opens any record; the line in the file carries it to readers without TARS.
  Rules out: the rule only in the files; repeating it in workshop-craft and workshop-forge, which already apply
  sttp-software-engineering.
- In a pipeline started from a session, without workshop-craft, the decisions the session took before the build are
  planning decisions, in the pipeline's file, with the task's Why and Not in this task.
  Why: a reader sees what was planned apart from what the build changed, as for a crafted task.
  Rules out: every decision of such a pipeline under Build decisions.
- The record lives in `docs/tars-reports/` at the repository's root, only in a git repository. A blueprint whose
  name another task's record folder has gets another name.
  Why: one known place in every project makes records findable, and a folder of TARS's own keeps other reports out of
  it; each task keeps its own record.
  Rules out: `docs/blueprints/`, `docs/snapshots/`, `docs/history/`, `docs/tasks/`, `docs/tars-records/`; following
  the repository's docs folder; a record outside git; two tasks sharing one record.
- workshop-forge's test of same-turn updates gets its decision and its trap from the user's message.
  Why: every run gets the same input, so a miss means the record fell behind, not that the trap went unnoticed.
  Rules out: a quirk planted in the test repository's code for the run to find.
- That test passes when the record holds the trap in any section, next to the decision it explains or under Traps.
  Why: a reader finds it either way; the test checks that nothing reaches the record late.
  Rules out: the trap under Traps only.
- The older test cases' repositories have no record.
  Why: a run on the new skills then writes it from the blueprint, as a task already running does on its next
  workshop-forge run.
  Rules out: a record in every test repository state.
- `.gitignore` ignores `.claude/worktrees/`.
  Why: Claude Code's worktree tool puts worktrees inside the checkout, where every clone should ignore them.
  Rules out: each developer's own `.git/info/exclude`.

## Tried and dropped
- Records searched only for "why" questions and while debugging, and never read before ordinary work. Dropped
  because: records are useful at any point; the risk is only that one is out of date, which checking against the code
  covers.
- The record outside a git repository, under the folder the session started in. Dropped because: no task outside git
  has needed one, and no test could cover it, since the cases outside git stop before writing any file.
- Suggesting a pull request that puts an abandoned task's record folder alone on the repository's main branch.
  Dropped because: no task has needed it yet, and the developer can still open one.
- The prompt hook reminding on each prompt while the blueprint's knowledge, `postponed.md` or scope is newer than the
  record. Dropped because: the skills' test runs kept the record current without it, and the knowledge files also
  change for facts the record leaves out, so it would fire on edits that need no update.
- The records in `docs/reports/`. Dropped because: other projects keep other reports there, and every session in
  every project is told to search the folder.
- One record file per task, with one State line per pipeline, set to done by the task's last pipeline. Dropped
  because: every pipeline's branch added or edited the same file, so merges conflicted, also on neighbouring lines,
  and pipelines running side by side cannot tell which one finishes last.
- A decision that became an ADR kept in the task's one record file. Dropped because: the record became a folder of
  pipeline files.
- A task's file, `00-task.md`, written only by workshop-craft, with the task's Why, planning decisions and Not in this
  task, and a State of planning, planned or abandoned, never done. Dropped because: on a finished task it still said
  planned, which read as not built yet, and a reader of a pipeline needed two files.

## Traps
- Claude Code's Grep tool skips files git ignores, so it never finds anything under `.blueprints/`; its Glob tool
  does find them.
- When Claude Code reads TARS through a link to a checkout of this repository, an edit in that checkout reaches every
  running session at once. Change the skills and the hooks in a worktree.
- A new git worktree gets none of the main checkout's untracked or ignored files, so a blueprint or a record not yet
  committed stays behind; removing a worktree deletes the ignored files in it, a blueprint included.
- A session that entered a worktree through Claude Code's worktree tool cannot write files in the main checkout.

## Known issues
- workshop-forge's test repository's knowledge says the pages show amounts through `format_eur`; they use an `eur`
  template filter. workshop-craft's test repository had the same line and now says what the code does.
- workshop-glossary's test of the approval turn runs its own `diff` and reads only its output, so a file diff cannot
  read counts as unchanged there.
- Unchecked: that workshop-forge's `SKILL.md` must stay under 5,000 tokens to be re-attached whole after a compaction.
