# Changelog

Changes from 0.7.0 on. Each version's section is also its GitHub release's text.

## 0.7.3

TARS and its optional mod, tars-mod, are both at 0.7.3. Update the mod together with the plugin.

### Changes

- An iteration that `/workshop-forge` adds to a running pipeline gets a name that reads in order where it runs. A
  fix that runs after 6.7 and before 6.8 is 6.7.a, and the next one 6.7.b. Before, it took the next free number of
  its category, such as 6.20 in a category planned up to 6.19, so a status table read 6.7, 6.20, 6.8.
- Work that an iteration not yet done needs first splits that iteration. Its row keeps its name, with the status
  SPLIT, and its parts are the rows right under it: 6.8.a, the new work, then 6.8.b, what 6.8 was planned to do. A
  part splits the same way, into 6.8.b.a and 6.8.b.b.
- No name already in a plan changes, so every earlier mention of an iteration, in a report or a note, still points
  at it. At the end of its category an added iteration takes the next whole number, as before.
- A split iteration is done when all its parts are. A release point, or another pipeline's wait, that names it
  stays as written, and `/workshop-forge` tells you which pipeline can start once the last part is done. Before, the
  work map's format said to rewrite the wait when such an iteration was split.
- The note that tells `/workshop-forge` which iteration is next, and the mod's status line and pipeline pane, read
  the new names. An older mod skips them: with an iteration such as 6.7.a next and every other one done, its status
  line says the pipeline is done.
- What does not change: the iterations already in a blueprint keep their numbers, a planned iteration that only
  moves keeps its number, and a new plan from `/workshop-craft` is numbered with whole numbers.
- The testing rules say where test cases come from: what is already known about the real data, such as earlier runs
  and their counts, bug reports, logs, the task records in `docs/tars-reports/`, your examples, and under
  `/workshop-forge` the blueprint's recons and knowledge files. Each path the change touches that this data reaches
  gets its own test, and values that take the same path are one case. An invented case tests what the agent
  expects; a case from a real run tests what the data holds.
- Code that the change calls without changing it, that this data reaches and no test covers, gets its test in the
  same change. That code already works, so the test cannot fail first: the agent proves it by breaking the code
  once and putting it back.

### For contributors

- The workshop-forge evals have four new cases on the name and the place of an added iteration: `fix-named-after`,
  `needed-first`, `second-find` and `split-release`, with two fixtures whose plans hold lettered names,
  `writer-moved` and `access-split`.
- The workshop-forge and workshop-craft graders read lettered names, and the workshop-craft grader has tests of its
  own, `evals/workshop-craft/test_grade.py`.
- The testing evals have a fourth case, `cases-from-recon`: a change to how a document's citations are fixed, where
  a dry run's notes show the paths the real data takes. Its grader breaks each path in a copy of the repo to see a
  test fail.
- When you judge eval runs with a second agent, give it copies of the reply and the repo with the run's path taken
  out. A reply names files as links with the full path, and a run's folder says which version of a skill it used.
  The record of this version's task, `docs/tars-reports/iteration-numbers/`, has the details under Traps.

## 0.7.2

### Changes

- `/workshop-forge` deletes old code as soon as nothing planned needs it: the iteration that deletes it runs right
  after the last iteration that needs that code, on its own, and not in a cleanup at the end of the pipeline. A plan
  that has it later is reordered. Before, old code stayed until the end, and the iterations before it wrote code only
  to keep it working, such as a write to both the old store and the new one, which was deleted later anyway.
- When an iteration is planned to write such code, the agent proposes the earlier cleanup instead, before writing it.
- A cleanup can come while something still uses the old code. The agent first looks through the whole repository for
  what does, tells you what stops working and until which iteration, and goes on only after you confirm. The tree
  still builds and the tests still pass in between: what they need is stubbed with the least code that does it.
- When you keep such code, the iteration's report says what it keeps working, the tests that check it, and the
  iteration that deletes it, so you review the diff knowing which lines are deleted later.
- `/workshop-craft` proposes a task's split the same way: the iteration that deletes the old code comes right after
  the last one that needs it, and where that order leaves a part of the system not working for a while, the proposal
  says what stops working and until which iteration, for you to confirm.

### For contributors

- The workshop-craft evals have an eleventh case, `split-old-store`: the split of a task that moves sales from a
  file store, which pages, an intake and three jobs use, to SQLite.
- The workshop-forge evals have four new cases on the same repo, partway through that move: `delete-next`, where
  the next iteration must be the delete of the old store though the plan has it at the end; `skip-offer`, where the
  planned write to both stores must be put to the user before any code; `kept-write`, where the user keeps that
  write and the report must name the iteration that deletes it; and `missed-caller`, where a job the plan never
  mentions still reads the old store.
- The workshop-forge grader can post a sale to that repo's intake, and tells a question asked before the code from
  the wait for "continue" after a done iteration.

## 0.7.1

### Changes

- The coding rules ask for no wasted work while the code is written: nothing computed or fetched twice, no query or
  file read inside a loop when one before it does, independent requests and queries run at the same time, nothing
  slow added to startup or a hot path. New code next to a function that does it the slow way does not copy it; that
  function stays as it is, and the report names it.
- The coding rules also ask for no state that can be derived from other state, one function with a parameter instead
  of copy-paste with a small change, early returns instead of deep nesting, and no long-lived closure that keeps
  large values alive.
- These checks hold for the code a change writes. They never on their own make the agent change code that already
  exists: the report names the cost instead. They take their ideas from Claude Code's bundled `/simplify` skill.

### For contributors

- The coding evals have a seventh case, `parallel-fetches`: an async dashboard added next to a function that awaits
  its two requests one after the other. The coding grader also finds `async def` tests.

## 0.7.0

The first public version of TARS and of its optional mod, tars-mod, after 0.5.4 and 0.1.10.

### Platforms

- Native Windows: Claude Code and Codex CLI, checked in real sessions on Windows 11.
- The Claude desktop app, checked on Windows 11, with the mod's status line and pipeline pane.
- macOS, through the hook and mod tests that CI runs.

### Changes

- Session notes in `~/.tars` (the `paused-`, `guards-off-` and `forge-` files) are deleted at session start once
  untouched for 30 days, in Claude Code and Codex. Before, they were never deleted. The settings files stay.
- `/tars-doctor` says when a session goes on from a conversation TARS could not trace, such as a move to the
  background that Claude Code did not record: the session's pause, git guard switch and pipeline did not come along.
- The mod no longer redraws its status line when a subagent's turn starts.
- On Windows, the hooks and the mod keep their notes in the same folder: `HOME` when it is set, else your profile
  folder. Before, with no `HOME`, as in a normal Windows terminal, the mod wrote its notes to a folder named
  `undefined\.tars` inside the project, and the hooks never saw them.
- The README tells Windows users how to get a real `python3`: a fresh Windows has only the Microsoft Store's
  shortcut, on which every hook fails.

### For contributors

- CI runs on every push and pull request: the hook tests on Linux, macOS and Windows with the newest Python, and on
  Linux with Python 3.9 too, and the mod tests on all three with Claude Code's latest release.
- `tests/windows/` sets up a Windows 11 VM in Docker for the checks CI cannot run: real sessions in Claude Code,
  Codex and the desktop app. Its README has the steps and what each check should show.
- The skill tests' graders for sttp-enforce, workshop-glossary-bootstrap, workshop-grill, workshop-glossary and
  workshop-forge no longer fail a run for reasons outside the skill. Each fixed grader has a `test_grade.py` next to
  it that checks the grader with no model.
