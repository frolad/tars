# TARS Blueprint Record: no work spent on code that is going away: code-going-away

The code is the source of truth: check anything here against the code before relying on it.

State: done on main.

## Why
When a pipeline replaces old code, TARS planned and ran it so that the old code kept working until a cleanup near
the end deleted it: the old code's other users moved late, new data was written to both the old and the new store,
and old functions were patched to handle the new data, all of it deleted later. That is work spent on code that is
going away, and the developer reviews it for nothing. This pipeline adds a short rule to workshop-forge and a
sentence to workshop-craft's split, so the plan deletes that code as early as it can and avoids code written only to
keep it working, and eval cases that show the difference.

## Planning decisions
- The goal is no work spent on code that is going away: nothing written only so that it keeps working, such as a
  write to both the old and the new store, an adapter from the new shape to the old one, or a patch so an old
  function handles the new data, beyond what keeps the tree building and the tests passing. The way there: delete
  it as early as the plan allows, and leave unwritten the code that would only keep it working.
  Why: the waste is the time spent on code that is removed anyway; less to review follows from it.
  Rules out: easing the review as a goal of its own.
- The step right after the last one that needs the old code deletes it, as a step of its own; code written only to
  keep old code working is named in the report, with the step that deletes it.
  Why: in the pipeline behind the task, the deletes piled up in a cleanup near the end, and the code written to keep
  the old flow working until then was deleted with it.
  Rules out: a cleanup near the end as the default; deleting in the same step as the move.
- The skills give the code written only to keep old code working no name of its own: they describe it, with
  examples.
  Why: the skills are written for agents, and a word like "bridge" or "compatibility code" reads several ways to an
  agent.
  Rules out: "bridge", "shim" or "compatibility code" as a word in the skills.
- The rules are checked by new eval cases on a repository with an old flow that has other users, each failing with
  the skills before this task and passing with the new text, and by every existing workshop-craft and workshop-forge
  case, old text against new, scoring no lower.
  Why: the only way to see the rules change what the agent does and break nothing else.
  Rules out: running only the new cases; adding the rules on reading alone.

## Not in this task
- The other work left for later when the repository went public: iterations split in a way the developer does not
  expect, a loose match in the workshop-craft eval's grader, and the order of Codex's install steps in README. Why:
  each is a task of its own.
- The engineering check's question "Does it depend on code that is going away?" and the coding rule to remove what a
  change orphaned. Why: they stay as they are; the new rules are about the order of a pipeline's steps.
- workshop-forge's rules for a design dropped partway and for old tests made redundant. Why: they cover other cases
  and stay as they are.
- workshop-forge's end of the pipeline and what its review removes. Why: the waste comes from the order of the
  steps before it.
- The changelog entry and the version bump. Why: done at the next release.

## What was built
- workshop-forge's "Replacing and dropping" has a short rule, "Cleanup moves up", in
  `skills/workshop-forge/SKILL.md`. An agent running a pipeline now plans the delete of old code as the step right
  after the last one that needs it, and moves it up when the plan has it later. Where a step is planned to write code
  only to keep old code working, it proposes the earlier cleanup instead. Before an early cleanup it looks through the
  repository for what still uses the old code, and when something does, it tells the developer what stops working and
  until when, and goes on only after the developer confirms. That part then does not work until the step that moves
  it, but the tree still builds and the tests still pass: the agent stubs what they still need.
- workshop-forge's "Reporting an iteration" has a line for code written only to keep old code working, such as a
  write to both the old store and the new one, in `skills/workshop-forge/SKILL.md`. After a step that wrote such
  code, the agent's report now says what that code keeps working, which tests check it, and which step deletes it
  and removes or changes those tests. The developer then reviews the diff knowing which lines are deleted later.
- workshop-craft's split step has a sentence for old code that the task replaces, in
  `skills/workshop-craft/SKILL.md`. An agent proposing a split now plans the delete of the old code as a step of
  its own, and orders the old code's users so that this step comes right after the last one that needs the old code.
  Where that order leaves a part of the system not working for a while, the proposal says what stops working and
  until which step, for the developer to confirm.
- A workshop-craft eval case, `split-old-store`, in `evals/workshop-craft/`: the split of a task that moves sales
  from a JSON-lines file store to SQLite, in a repo where the pages, the intake, the admin correction and three jobs
  use the store. Its checks want nothing written to both stores, the store deleted in a step of its own, right
  after the step that moves its last caller, and what the order leaves not working for a while said with the step
  that ends it, for the developer to confirm.
- A workshop-forge eval case, `delete-next`, in `evals/workshop-forge/`: a "continue" whose iteration moves the
  intake, the last caller of the file store, in a plan that has a sales list by month before a cleanup at the end.
  Its checks want the intake's sales in SQLite only, the file store and its tests left as they are in that turn, and
  the delete of the file store as the next iteration, on its own, in the plan's file and in the reply. Its fixture,
  `store-intake-next`, is the craft case's repo partway through the move.
- A workshop-forge eval case, `skip-offer`, in `evals/workshop-forge/`: a "continue" whose iteration, as planned, has
  the intake write each sale to SQLite and to the file, only so that the accounting CSV keeps every sale while the move
  of its export is blocked. Its checks want no code before the developer's answer, the plan's file saying it waits on
  the developer, and a reply that proposes not to build that write, by leaving it out or by deleting the file store
  earlier, and says what stops working and until when. Its fixture, `store-export-waits`, is an earlier state of the
  same repo.
- A workshop-forge eval case, `kept-write`, in `evals/workshop-forge/`, on the same fixture as `skip-offer`: the
  same "continue", in which the developer keeps the write to both stores. Its checks want the write built without
  asking again, each sale in SQLite and in the file, the file store's code left as it is, and a report that says a
  later step removes the write to the file, names that step, and names the tests of that write as going with it.
- A workshop-forge eval case, `missed-caller`, in `evals/workshop-forge/`: the same "continue" as `skip-offer`, in a
  repo where a job merged after the plan was made, a morning stock alert, still reads the sales from the file store,
  and nothing in the plan moves or removes it. Its checks want no code, the plan's file saying it waits on the
  developer, and a reply that names the job and asks what to do with it. Its fixture, `store-missed-caller`, is
  `store-export-waits` plus that job.

## Build decisions
- The rules are one short rule that carries its reason: cleanup steps move up, because code written only to keep old
  code working is deleted later anyway, and the developer confirms when an early cleanup stops something that still
  uses the old code from working; that part is stubbed, so the tree still builds. workshop-forge has the rule, and
  workshop-craft's split step has a sentence of its own.
  Why: the developer found a block of rules too abstract for a skill; an agent that is told the reason acts on the
  cases the rule does not list.
  Rules out: a definition of code going away in the skills; a stub offered to the developer as a choice; a tree that
  does not build after a cleanup; workshop-craft pointing to workshop-forge's text.
- The workshop-craft case is a storage move, with a job to drop and two jobs to move, and it also checks where the
  delete goes and that the gap the order leaves is named.
  Why: a storage move is where writing to both stores is the habit; the split proposal shows the delete's place as a
  category, and a late delete is the problem behind the task; the split is where the order that causes a gap is
  chosen, and the developer picks each gap.
  Rules out: a case checking only the order and nothing written to both stores, with the delete's place and the gap
  left to the workshop-forge cases.
- The workshop-forge case for the delete moves the last caller of the whole file store, with other work planned
  between that move and the cleanup.
  Why: the whole store is unused after the turn, as in the pipeline behind the task, so a reply that keeps the late
  cleanup or deletes in the same turn fails a check, and nothing about the fail is debatable.
  Rules out: a turn that leaves only one function of the store unused, where a reply can fairly call it too small
  for a step of its own.
- The workshop-forge fixture is built on the workshop-craft one: its script calls the craft script for the store
  repo, then adds its own commits and the finished blueprint.
  Why: one copy of the store repo, so the craft case and the forge cases cannot drift apart.
  Rules out: a copy of the store repo in the forge script. The forge suite needs the craft script to build this
  fixture, and the build stops when a text of the craft fixture it replaces is no longer there.
- Something that still uses the old code and that the plan misses is put to the developer before any code: what
  stops working and until when, and the work goes on only after the developer confirms.
  Why: the plan can no longer delete the old code as written.
  Rules out: doing the step as planned and naming the caller in the report; the agent adding a step that moves the
  caller on its own.
- Code the developer chose to have written only to keep code going away working, such as a write to both stores kept
  when the skip was offered, is named in the report like a patch that could not be avoided, with the step that removes
  it.
  Why: at the review the developer sees which lines are temporary.
  Rules out: naming only a patch the developer was not asked about.
- The report names that code together with the tests written for it, with the step that deletes them.
  Why: tests of temporary code are reviewed for nothing too, and with the skills before this task no report said which
  tests go.
  Rules out: naming the code only, which the skills before this task already did in some runs.
- The `skip-offer` case runs on a plan whose order cannot avoid the write to both stores: every reader is on SQLite but
  one, whose move is blocked, and nothing ships before the whole task is done.
  Why: the plan itself asks for that write, so a run that follows the plan builds it; and with the last reader's
  move blocked, what stops working lasts until a step the reply can name.
  Rules out: a plan that simply moves the intake before the readers; a caller the plan does not move in this case's
  repo, which gets a case of its own.
- The checks of the `split-old-store` and `skip-offer` cases ask only for what the short rule says. Two checks left
  the workshop-craft case: the old store's other users moved first, and the pages before the writers. One left
  `skip-offer`: the step that deletes the file store named. A reply passes `skip-offer` when it proposes not to build
  the write, by leaving it out or by deleting the file store earlier, and says what stops working and until when.
  Why: a check for something the skills no longer ask fails a correct run with the new text.
  Rules out: a check kept as a stricter standard than the rule; a stub as one of two ways a reply must offer.
- In the `kept-write` case the developer's choice is in the message that starts the step, not in an earlier offer
  shown in the conversation.
  Why: an offer in the conversation already says which step removes the code, so a report could repeat it without
  any rule asking for it; and the case also shows that a choice already made is not asked again.
  Rules out: a conversation that shows the offer and the answer; a change that forces a patch to the file store as
  the scenario, which this repo has no natural case of.
- The `kept-write` case asks for the tests in a check of its own, beside its two checks on the code.
  Why: the skills before this task already named the kept write and the step that removes it in some runs, and never
  the tests, so the case tells the two texts apart on that check.
  Rules out: one check for the code and its tests together, which would hide what the skills before this task
  already did.
- The `missed-caller` case asks for the missed job to be found at the step that would first treat the file store as
  going away, not at the step that deletes it.
  Why: before the delete, an agent already searches for callers and the tests fail, with or without the new rule;
  the new rule is that the look through the repository comes before an early cleanup or any code for the old code.
  Rules out: a case on the step that deletes the file store, which the skills before this task would pass too.

## Tried and dropped
- A block of five rules in workshop-forge: a fixed meaning of code going away, with a search checklist (names in
  strings, routes, templates and config) and a question about code callable from outside the repository; the order,
  with the old code's other users first and readers before writers; a skip or a stub offered for the developer to
  pick, never across a release point; and the delete. Dropped because: the developer found it too abstract for a
  skill; the short rule replaced it before it was ever run.
- A stub as one of two ways offered to the developer, beside leaving the code unwritten. Dropped because: in the
  short rule the stub is not a choice; it is what keeps the tree building once the developer confirmed the cleanup.
- A new order and a skip as two separate replies, the skip only where the order cannot avoid a write to both stores.
  Dropped because: both became "propose the earlier cleanup".
- One copy of the rules in workshop-forge, with workshop-craft's split step pointing to it. Dropped because: the rule
  became short enough for workshop-craft to carry a sentence of its own.

## Traps
- The workshop-craft grader used one blueprint path for every case; a case on another task's blueprint needs its own
  entry in `CASE_BP` in `grade.py`, or its scope checks read a file that is not there.
- With the skills before this task, workshop-craft already plans a storage move with the readers before the writers
  and nothing written to both stores, and removes a dropped user of the old store first. What it misses: leaving the
  gap that order leaves to the developer, and, in one run of two, deleting the old store in a step of its own.
- A judged check that says "deleted in the step right after its last caller moves, not in a cleanup after everything
  else" is read by a judge as "not a late cleanup", and passes a delete in the same step as the move. The check now
  says "in a step of its own, right after the step that moves its last caller: not in that step".
- "Deleted as early as the plan allows" alone lets workshop-craft put the delete in the same step that moves the old
  code's last users: with the split step's sentence as first written, one run of two did, because the old store's
  test goes through one of those users. The sentence now says "in an iteration of its own", and with it two runs
  of two plan the delete as a step of its own.
- The workshop-craft grader's check that a run read the code leaves out every command line that names the skill's
  snapshot folder. A run that reads the code in the same command as it lists that folder fails "Read the code under
  reports/" though it read the code.
- Where no other work is planned after the last caller's move, workshop-craft already puts the delete right after
  it, with the skills before this task. A workshop-forge case shows the rule only when the plan has other work
  between that move and the cleanup.
- In the craft fixture every test of the file store records its sale through the intake, so moving the intake
  breaks them. The forge fixture's file store tests add their own sale, so that the move leaves the file store and
  its tests passing and unused.
- A plan's Current line that waits on the developer's "continue" after a finished step also matches a pattern for "waits
  on the user". The `skip-offer` case's check therefore also wants the step not done; the two older workshop-forge cases
  with that pattern end before any step is done.
- With the skills before this task, workshop-forge keeps the delete of the old store for the cleanup at the end, builds
  a planned write to both stores with no offer, and finds a caller the plan misses only after that write is built,
  then names it in the report and asks. When the developer kept a write to both stores, one run of two already named
  it in the report with the step that removes it, since the plan had a step of its own for taking it out; no run named
  the test written for that write.
- The two store fixtures of the workshop-forge suite are built by one branch of its fixture script, `store-export-waits`
  being the earlier state that `store-intake-next` goes on from. A change to the shared steps changes both.

## Known issues
- No review ran over the pipeline's changes at its end: the developer chose none.
- With the split step's new sentence, workshop-craft also looks for old code in a task that replaces no old flow. In
  the eval's task of CSV and PDF downloads, the runs with the new text name `require_role`, the access check the
  task may widen or replace, as code to delete in a step of its own. One run of two wrote that open choice under Not
  yet clear in the pipeline's plan, where the format wants an open decision under Blockers. Left as it is by the
  developer's decision: naming such code is what the sentence is for.
- The workshop-forge grader's check that an iteration is done and the plan's Current line moved on fails a Current
  line worded "<Category>, iteration N is done"; it accepts "<Category>, iteration N: done". The `delete-next` case
  uses that check, and its fixture words its Current line the accepted way. In the runs with the skills before this
  task, no run worded the line the failing way. Not fixed.
- The `kept-write` case's two checks on what the report says about the write are read either way by a judge for a
  reply that builds nothing and only describes the write. Such a reply fails the scripted checks, so the case still
  fails it. Not fixed.
