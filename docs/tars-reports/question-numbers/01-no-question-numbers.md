# TARS Blueprint Record: question numbers in TARS files: no question numbers

The code is the source of truth: check anything here against the code before relying on it.

State: done on main.

## Why
TARS's grill numbers its questions in the chat so the user can answer by number. Agents also copied those
numbers into the files TARS writes, after a decision ("Decided by the user on <date> (Q<n>).") and twice into code
comments. In a file the number leads nowhere: the question and its answer live only in one session's transcript on
one machine, and numbering starts over, so one blueprint can hold two different questions under one number. This
pipeline puts a rule next to each kind of writing, so that no file TARS writes carries a question number, and adds a
test that a workshop-forge run writes none.

## Planning decisions
- The rule covers every file TARS writes: blueprints, TARS Blueprint Records, and code comments written in a TARS
  session.
  Why: the numbers that reached code were copied from a blueprint, and no teammate can look them up.
  Rules out: blueprints and records only.
- No question numbers in those files. A decision keeps its text, its why and what it rules out, with the user's own
  words quoted; a reference to another decision names it by what it says. The one exception is the line of a
  pipeline's `iterations.md` that says where the work stands, while a question is still open: it names the question
  with its number and title, so that an answer by number still lands after a compaction.
  Why: the decision already carries what was decided, so a number adds nothing a reader can follow, and numbers kept
  out of the blueprint have nowhere to leak from.
  Rules out: numbers allowed in the git-ignored blueprint and banned from committed files, with or without a log of
  every question; numbers made unique per pipeline.
  Known cost: the jump from a decision to its question in the session transcript is gone.
- Question numbers count once per session: Q1 at the start, on through every round and every mini grill, after a
  compaction too; a new session starts at Q1.
  Why: the user answers in the chat, so a number only has to be unique there, and no file has to keep a counter.
  Rules out: starting over at each mini grill; one count per blueprint.
- Each rule sits next to the writing it governs: the blueprint's layout format, the coding skill's comment rule, the
  record's format and the ADR format.
  Why: a rule read right before the writing holds, as the record's ban did.
  Rules out: the rule in the grill only; the same rule kept in three places.
- Of the numbers already written, only the mod hook's comment is rewritten here.
  Why: the other files belong to other tasks, and the coding rule stops further copies.
  Rules out: a pass over the existing blueprints.

## Not in this task
- The question numbers already in other repositories' blueprints and code. Why: they belong to those tasks.
- The developer's own notes kept next to TARS. Why: they are not files TARS writes.
- A check that flags question numbers in a diff, as a hook or a doctor check. Why: the rules are read right before
  the writing, like the record's ban, which held.
- A version bump and the Codex reinstall. Why: a separate step of the skill set's release.

## What was built
- A workshop-forge test case, `tagged-decisions` in `evals/workshop-forge/`: on a blueprint whose knowledge gives
  every decision a question number (the `tagged` fixture), the user answers a numbered mini grill question, and the
  run must write the answer as a decision in the knowledge and as a code comment, neither with a question number,
  and must leave the numbers already in the knowledge as they are.
  The chat first shows an earlier mini grill whose answers are already in the knowledge with their numbers, as a
  real session leaves them, so that the run sees its own session's numbers and the count goes on.
- Blueprint files carry no question numbers (`skills/workshop-craft/formats/layout.md`): a decision says what was
  decided, quoting the user when its why rests on their words, and a reference names the other decision by what it
  says. The Current line keeps the number and title of a question still open, and a number already in a file stays
  as it is.
- Code comments carry no question number or other label from the chat, in any session
  (`skills/sttp-software-coding/SKILL.md`).
- A decision that becomes an ADR leaves any question number behind (`skills/workshop-glossary/formats/adr.md`).
- workshop-grill and workshop-glossary-bootstrap count questions once per session, Q1 to start, on through every
  round and after a compaction; the bootstrap's working file keeps no count.
- The mod's status line comment says why dropped rows count on neither side, in words
  (`mods/tars-mod/hooks/tars-mod.js`).

## Build decisions
- The glossary bootstrap counts its questions once per session, like the grill, and keeps no count in its working
  file; the questions still open in that file keep their numbers so that an answer by number still lands after a
  compaction.
  Why: it was the one skill still keeping a count in a file, and a session that ran a grill and then the bootstrap
  would show two first questions with the same number.
  Rules out: the bootstrap keeping its own count across sessions.
- A question number already in a file stays as it is; the rule covers what is written from now on.
  Why: in both test runs with the rule, the agent took the numbers off the decisions already in the blueprint
  without being asked, one of them without a word in its reply, and a change should touch only what it was asked to.
  Rules out: agents clearing old numbers as they pass.
- The workshop-forge test case also checks that the numbers already in the knowledge stay, and is not run again here.
  Why: it passed both test runs that took the old numbers off; with the check, the next workshop-forge test run
  shows whether the rule holds.
  Rules out: running the case again now; the rule with no check.
  Known cost: whether the rule keeps agents from taking old numbers off is not known until that run.

## Traps
- A test run of one short exchange does not copy question numbers: a workshop-forge run wrote none until the chat
  showed its own earlier numbered answers already tagged in the knowledge. A test of the rule needs that history.

## Known issues
- No code review ran on this pipeline's changes: the developer ended the pipeline without one.
- No test run has had the rule that a number already in a file stays as it is. The workshop-forge case
  `tagged-decisions` fails a run that takes one off, so its next run shows whether the rule holds.
- Two test checks fail for reasons outside the run, with the change and without it alike: workshop-glossary's case
  `merge-skipped-no-glossary` flags the reply's file links, because the test folder is named `workshop-glossary`, and
  workshop-grill's case on the fixture `light-decision` flags an `ls -l` line that lists a skill's file as another
  skill loaded.
