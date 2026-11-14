# TARS Blueprint Record: names for iterations added to a running pipeline: iteration names

The code is the source of truth: check anything here against the code before relying on it.

State: done on main.

## Why
An iteration added to a pipeline while it runs took the next free number of its category: found after 6.7 in a
category planned up to 6.19, it was 6.20, and it ran before 6.8. After a few such iterations a status table read
6.7, 6.20, 6.8: its rows were in the order the work ran, its numbers in the order the iterations were found. This
task changes how TARS's workshop names and places an iteration added after the plan was written, so that a status
table reads top to bottom in the order the work runs. This pipeline is the whole task: everything that reads an
iteration's name reads the new names, the rule goes into the format of `iterations.md` and into workshop-forge's
text, and eval cases show that an agent follows it.

## Planning decisions
- An added iteration sits in the plan where it runs, under a name that reads in order there.
  Why: with the place alone and the next free number kept, the rows are in order and the numbers still jump.
  Rules out: the next free number of the category for an iteration that runs before others already planned.
- The name of an added iteration is a number, a dot and a small letter: 6.7.a, 6.8.b.
  Why: it reads between the two numbers around it, as a section added to a law (12A) or a scene added to a film
  script whose scene numbers are locked (10A) does.
  Rules out: a third level of digits (6.7.1); plans numbered by tens with the gaps filled later.
- Work that an iteration not started needs first splits that iteration: it keeps its row and its name with the
  status SPLIT, and its parts are rows under it in the order they run, 6.8.a and 6.8.b, the new work first and what
  it was planned to do last. A part is split the same way: 6.8.b.a.
  Why: the table reads in order at every step and no row is renamed, so every earlier mention of the iteration
  still points at the right place.
  Rules out: a name after the row above, 6.7.a, for work that 6.8 needs first; a new letter placed above an older
  one, 6.7.b above 6.7.a.
  Known cost: what was planned as 6.8 is built under the name of a part, and names grow by a level with each later
  find inside a part.
- A split iteration is done when all its parts are, so a line that names it, such as a release point or another
  pipeline's wait, is not rewritten.
  Why: no file is rewritten when an iteration is split.
  Rules out: rewriting those lines to name the last part.
- An iteration added at the end of its category takes the next whole number.
  Why: nothing comes after it, so a whole number reads in order there.
  Rules out: a name such as 6.0.a for work before the first iteration of a category, which splits that iteration
  instead.
- One shape of name for everything that reads one: a number, or a number with a category's number before it, then
  any count of a dot and small letters.
  Why: today's numbers are names of that shape, so a file written before the change is read as before.
  Rules out: a second reader for old files.

## Not in this task
- New names for the iterations already in a blueprint. Why: the old numbers are named in reports, knowledge files
  and chats.
- A new name for a planned iteration that moves with nothing new added: it keeps its number, so a table can still
  read out of order after a move. Why: every earlier mention of it still points at it.
- How workshop-craft numbers a new plan: whole numbers in planned order. Why: the task is about iterations added
  after the plan was written.
- Categories: one found while a pipeline runs still takes the next free category number, and an iteration of one
  category that runs between the iterations of another stays where it was put. Why: the task is about the order
  inside one category.

## What was built
- The hook that tells workshop-forge which iteration is next (`hooks/sttp.py`), the mod's status line and pipeline
  pane (`mods/tars-mod/`), and the eval graders of workshop-forge and workshop-craft read a lettered name, such as
  6.7.a or 6.8.b.a. Before, each skipped such a row with no error: the hook named the next plain-numbered open row,
  and the mod neither showed nor counted it.
- A name is read whole: the hook and the graders do not take the line of 6.7.a for the line of 6.7, and the
  workshop-forge grader does not take a Current line on 6.7.a for one still on 6.7.
- The workshop-craft grader has tests of its own, `evals/workshop-craft/test_grade.py`, built like the
  workshop-forge grader's.
- Four workshop-forge eval cases check the name and the place of an added iteration, in `evals/workshop-forge/`: a
  fix of the iteration just finished, run before the next planned one; work the next planned iteration needs first;
  a second find inside an iteration already split; and the last part of a split iteration that is a release point
  for another pipeline. Each checks that the names of the status table read in order from top to bottom and that
  no row the plan had gets another name. Two fixtures hold plans with lettered names, `writer-moved` and
  `access-split`.
- The format of `iterations.md` (`skills/workshop-craft/formats/iterations.md`) says where an added iteration goes
  and what it is called, in a line of its own after the numbering line: its row and its line go where it runs, and
  its name is the first of three that fits. Work that an iteration not DONE needs first splits that iteration
  into lettered parts under its row. At the end of its category it takes the next whole number. Between two rows
  it takes the name of the row above it with the next letter. workshop-forge's text
  (`skills/workshop-forge/SKILL.md`, under "Keeping iterations.md up to date") has a short form of the rule with
  its reason, for an iteration added by any of its rules, and points at the format for the rarer cases.
- A split iteration is done when all its parts are, and the lines that name it stay as written. Three texts say
  so: the SPLIT status line of the format of `iterations.md`; the work map's format
  (`skills/workshop-craft/formats/workmap.md`), where a release-point iteration that splits stays the release
  point; and workshop-forge's line on the end of an iteration, which tells the user which pipeline can start also
  when the iteration just finished is the last part of a split release point. Before, the work map's format said
  to update the wait when a release-point iteration split. A release-point iteration that is dropped still gets
  its wait updated in the same turn.

## Build decisions
- Work that comes out of finished work, and that no iteration not started needs first, is named after the
  iteration it runs after, in a row right after it, whichever iteration's work it fixes: 6.7.a after 6.7, then
  6.7.b, and 6.7.a.a when it runs between 6.7.a and a 6.7.b that exists. With 2.1, 2.2 and 2.3 done, a fix of 2.1's
  work that runs before 2.4 is 2.3.a. Its line says what it came out of. The iteration planned next is untouched.
  Why: the table stays in the order the work ran and the names read in order; the name comes from the place alone,
  so the agent never has to judge where a fix belongs.
  Rules out: a split of the next planned iteration for work it does not need; a fix of older work in a row under
  what it fixes, with the row that is running among finished ones.
- At the end of a category a fix takes the next whole number, like any other added iteration: letters appear only
  between two rows.
  Why: nothing comes after it in its category, so a whole number reads in order, and the name comes from the place
  alone.
  Rules out: telling a fix from new work to pick a name.
- The skills say "an iteration not DONE" where the planning decision says "an iteration not started".
  Why: the iteration that most often needs work first is the one whose mini grill just found it, and the format
  calls that one CURRENT, "running now", so an agent could read "not started" as leaving it out.
  Rules out: "not started" in the skills' text.
- workshop-forge's text carries a short form of the rule itself, and the format the whole of it.
  Why: workshop-forge reads the format only before it first writes the file, so an agent that last read it before
  a compaction would name a new row from memory.
  Rules out: the rule in the format alone, with one sentence in workshop-forge that points at it.
- One line in workshop-forge covers every way it adds an iteration, and the sentences that add one in their own
  words (a fix, a cleanup, an unmet check, a review's finding) stay as they were.
  Why: the name and the place do not depend on why the iteration was added.
  Rules out: the rule's words repeated in each of those sentences.

## Tried and dropped
- A fix named after the iteration it came out of. Dropped because: it gave no answer for a fix of older work, whose
  row would sit either away from where it runs or out of order by name; named after the iteration it runs after,
  it gives the same name whenever the fix is of the iteration just finished.

## Traps
- Every reader of a status table skips a row whose name is not of the shape it accepts, such as 6.7a or 6.7.A, with
  no error: the hook then names another iteration as the next one, and the mod neither shows nor counts the row.
- The mod is released apart from the plugin. A mod older than this change skips lettered rows: with a lettered
  iteration next and every other row done, its status line says the pipeline is done.
- A judge who reads an eval run in the run's own folder can see which text the run used: a reply names files as
  links with the full path, and the folder's path holds the name of its config. This task's judges first read the
  runs that way. Read again from copies with the path taken out, two of the 352 checks they read came out
  differently, one each way.

## Known issues
- The mod's status line and pane were run with lettered rows in the mod's tests only, not in a real session.
- The eval case on a release point named by a split iteration does not tell the rule's text from the text before
  it in every run: an agent can work out alone that a split iteration is done once all its parts are. What the
  case catches is a Releases line or a work map's wait rewritten to name the last part.
- The check on how a reply ends, "Ends with the next iteration ... and the question to continue last", is read two
  ways when a reply puts a decision for the user before the question to continue, which workshop-forge's report
  rules allow: one judge passed that ending in two runs of the case on a second find, another failed it in a
  third. The four new cases now say that such a decision does not fail the check and that the reply's last
  sentence is the question to continue; the 18 cases the suite had keep the old wording. The fixture of the case on
  a second find invites the decision: its CSV writer keeps the name `monthly_csv` once it writes any header and
  rows, so an agent asks whether to rename it.
- A release point is the whole split iteration, also when what the other pipeline receives is ready after an
  earlier part: the agent tells the user that the other pipeline can start only once the last part is done.
- The rule's words were run for a fix the user asks for, work the next iteration needs first, and a second find
  inside a split. Not run: an iteration added by the cleanup of a dropped design, by an unmet check at the end of
  a pipeline, or by a review's finding.
- No review ran over the pipeline's changes at its end: the developer went on to the release, 0.7.3.
