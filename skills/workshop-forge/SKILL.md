---
name: workshop-forge
description: Build one pipeline of a task with the user, one reviewed iteration per turn, from an workshop-craft blueprint or from what the session discussed.
disable-model-invocation: true
---

sttp and sttp-software-engineering apply. workshop-forge is the construction stage. It builds one pipeline, one iteration per turn cycle, with the user in the loop: after each iteration it reports and describes the next one with the question to continue. The user's "continue" approves the finished iteration and starts the next one.

workshop-forge sets the process, the iteration contract and the reports; sttp-software-coding governs only the code written. Its "no plan, do it and report" and its Report section give way inside workshop-forge, and its "ask before editing" for a refactor becomes workshop-forge's next iteration.

The blueprint is workshop-craft's, under `.blueprints/<slug>/` in a git repository or in a folder the user named. Its layout, where it lives, and its file formats are in `../workshop-craft/formats/`, starting with `layout.md`; read a file's format before writing that file for the first time. A pipeline's state is its `iterations.md`, and its Current line is the way back in after a compaction. The task also has a TARS Blueprint Record, the folder `docs/tars-reports/<slug>/`, in `record.md`'s format: each pipeline writes its own file there, and the developer commits it with the pipeline's work.

## Outside software

workshop-forge runs any work complex enough to split into iterations, not only code: a topic to research, a scene in Blender, a screen in Figma, and other kinds. The process holds as written: the contract, the mini grill, the stop, `iterations.md` and the reports. The code and test rules apply where they have a counterpart and are skipped where they do not. The iteration's check is the work's own: the sources hold up, the file opens and renders, the screen matches the decision. Name it in the iteration's line. What the user reviews is the output itself, such as the notes, the render or the screen, and the report points to it.

## Picking what to run

- `/workshop-forge <task> <pipeline>` runs that pipeline. The task is a name under `.blueprints/` or the path of a blueprint folder. The pipeline can be given by its number, its name or its folder: `2`, `pdf-downloads` or `02-pdf-downloads`. In Codex, `$workshop-forge` passes the rest of the message as plain text; read the task and the pipeline from it.
- `/workshop-forge` alone:
  - exactly one pipeline is current or can start, its waits in the work map met: take it and name it in one line;
  - several can run: list them numbered and ask;
  - no blueprint: start from the session (below);
  - a blueprint exists but the session discussed something else: ask which one is meant.

## The iteration contract

Every iteration runs these eight steps, in this order:

1. Run the mini grill on this iteration: the light mode of workshop-grill. Keep it short; it must not take over the turn.
2. If it found decisions for the user, ask them, and wait for the answers.
3. After the answers, run the mini grill again and ask follow-ups only for what is still open, until nothing is.
4. Once everything is clear, do the iteration.
5. New facts make the iteration impossible as planned: stop the change, say what was found, and go back to step 3. The sign is work that starts to need files, packages or decisions the iteration did not name: a growing diff means a question was not asked.
6. Minor uncertainties do not stop the iteration: finish it and note each one.
7. Finished with uncertainties left: ask the user to clarify them, in workshop-grill's format. The answer leads to step 8, or back to step 3.
8. Finished with nothing left: report, briefly evaluate the next iteration if one exists, and describe it with the question to continue.

### The mini grill

- Load workshop-grill with the Skill tool and run its light mode, started from the engineering check of sttp-software-engineering. It is light because workshop-craft did the recon: read the pipeline's Current line, the iteration's line, the pipeline's `knowledge.md`, and whatever of `00-knowledge.md` the iteration touches. Read code only for what the knowledge does not cover; search the blueprint's `recons/` for it first and read only the parts that match. A subagent's recon report is saved there, as `layout.md` says.
- The blueprint's Terms are checked against the names the iteration's code and pages use. A name that differs only inside the code is a fact: add it to the term as its `_In the code_` line. A task word that differs from what the project's users see, or that the code uses for a different thing, is a decision for step 2. A wrong term is fixed in place with a Corrected line, like a wrong fact.
- When the project has a glossary or ADRs, the glossary and the ADRs of the area the iteration touches are read with the knowledge. A glossary entry or an ADR that the iteration contradicts is a decision for step 2: the user's answer goes into Terms or the Decisions as a change to that entry, and the merge at the end of the pipeline applies it. workshop-glossary is not loaded for this, and the glossary and ADRs are not edited during an iteration.
- A PLANNED or NEXT iteration is a suggestion, not the source of truth. It becomes CURRENT when its mini grill starts.
- When the iteration writes or changes tests, load sttp-software-testing if it is not loaded. One question only: does a test already cross the interface this iteration touches? The iteration's knowledge answers it, or one look at the tests next to that code. A new seam, fake, port or test dependency is a decision for step 2. Nothing broader is analysed.
- There is no fixed stop after a proposal. Once everything is clear, the iteration is done right away, unless the user asked to see it first ("show me", "let me know"). The decisions the user owns are asked in step 2.

### The stop

The turn ends with the report, the next iteration's description and the question to continue. The question to continue is text, never a question tool's call: the turn ends with it, so the user reads the report and the diff before answering. The obvious next step is not started in the same turn, however small: the value of workshop-forge is the review between iterations. The user's "continue" after step 8 approves the finished iteration and starts the next one.

When the report offers a fix for something broken, the offer goes into Current with the next iteration, so a compaction does not lose it. The fix runs only when the user's reply clearly asks for it, in any words. It is then an iteration of its own, with its report and the stop, and the planned iteration waits for the next "continue". A plain "continue" runs the planned iteration, and the fix goes to `postponed.md`. When the report says so, it says it before the question to continue, which stays last.

## Keeping iterations.md up to date

- The status table holds every iteration's status (DONE, CURRENT, NEXT, PLANNED, BLOCKED, SKIPPED, WONT-DO, REVERTED, SPLIT); a row changes in the turn its status does, and the iteration lines carry none.
- A question to the user goes into Current as "waiting on the user". If it outlives the turn, it becomes a blocker, and the iteration it stops is BLOCKED.
- New facts that stop the iteration (step 5) make it SPLIT, with `split from` iterations, or add a `spawned by` one.
- For code, when the first iteration starts, write `Base:` in the header: the commit HEAD is at. The review at the end of the pipeline starts from it, however many commits the user made in between.
- Facts and decisions found go to the pipeline's `knowledge.md`, and move up to `00-knowledge.md` when a second pipeline or the scope needs them. A new term of the task goes to the Terms of `00-knowledge.md`.
- At the end (step 8): the finished iteration becomes DONE, and the next one becomes NEXT, which the Current line names, until its mini grill makes it CURRENT. One row at most is NEXT: when the next iteration changes, by the user's choice or a new proposal, the old one goes back to PLANNED in the same turn. Check the pipeline's `Releases` line: when the iteration just finished is a release point, tell the user which pipeline can start and what it receives.
- When the pipeline finds that another pipeline is needed, or that the scope moves: propose it in chat. After the user's OK, update the work map (the entry, its waits, the derived order) and the scope in the same turn, and add a line to the scope's Changes. Without a scope, in a pipeline started from a session, suggest running workshop-craft instead.
- Something found and left for later goes to `postponed.md` in the turn it is found; the report mentions it in one line.
- The pipeline's record file, unless the record is off (`layout.md`), changes in the same turn as an iteration done, a decision, a trap, a known issue, a postponed item or the pipeline's state, as `record.md` says: State is in progress from the first iteration and built once every iteration is done, and a planning decision the build changes goes to its Tried and dropped. When the checkout the work runs in has no file for the pipeline, write it from the blueprint. The developer turning it off: a `Record: off` line where `layout.md` says, and the written record deleted, in that turn. The developer dropping the task: State abandoned with why.

## Rules that hold at every size

1. **A reorganization is its own iteration**, with no feature and no behaviour change in it. Moving, renaming, lifting to a common place, deleting, re-pointing importers, extracting an inline component into its own file: one iteration. The feature is the next one. A pure move is reviewed as a move, in a minute; mixed with a feature, the reviewer cannot tell a moved line from a changed one and reads every line as new.
   - A move keeps bodies identical. Something that looks wrong in the moved code is noted in the report and fixed in the feature iteration or in its own.
   - A rename is part of the move, not of the feature.
   - Verification includes that the moved bodies are identical to the old ones. The test assertions do not change and the tests stay green; imports and calls re-pointed by the move are part of it.
   - The report lists every file as one of: moved from, to; renamed; extracted from; deleted; re-pointed. Nothing else appears in the diff.
2. **The tree builds and the tests pass** at the end of every iteration.

## Iteration size

The user sets it: workshop-craft suggests it, the user confirms it, and the user can change it at any moment ("these fixes one by one"). It is stored in the `iterations.md` header; a change is logged in the scope's Changes. When the user has set nothing more specific:

- its diff can be read in a couple of minutes;
- one verification proves it: a test run, a typecheck, a route registration;
- it leaves the tree buildable and the tests green;
- the report fits in a screen.

Signs an iteration is too big: more than one design decision in it, two subsystems touched, or the user would have to read tests to understand the change. Split before starting, not after. Order iterations by dependency; inside a feature, go server first when the client cannot be built without the contract.

At the default size, one logical fix or one behaviour change is one iteration. When a finding lists several fixes, the proposal lists them as iterations in order and the turn does the first only. Groundwork the first fix needs goes in with it, unless a mistake in it would change what code outside the fix does: then it is its own iteration, first. Later iterations extend the groundwork when they need more. A fix found while doing another is noted in the report as the next iteration, not added to the diff.

An iteration holds one or more test slices, done one at a time, red then green each; the stop comes after the iteration, not after each slice. A bug that already existed, found while proving a test, is its own iteration with its own red test.

## Replacing and dropping

- **Replacing an old flow starts with an audit.** When a category rebuilds something an old flow does, its first iteration lists what the old flow did besides its main job: the checks it ran, its side effects, its prefills. Each item becomes an iteration, is dropped by the user, or goes to `postponed.md`. A restriction or quirk of the old flow (a disabled button, a filter, a limit) is neither ported nor dropped as is: its reach is confirmed with the user first.
- **Cleanup moves up.** An iteration that deletes old code runs right after the last iteration that needs that code, on its own, and not in a cleanup at the end: when the plan has it later, move it up, and order the old code's users so that it comes early. The reason: as long as old code stays, iterations write code only to keep it working, such as a write to both the old store and the new one, and that code is deleted later anyway. An iteration planned to write such code is a sign: propose the earlier cleanup instead, before writing it. An early cleanup can come while something still uses the old code. Before it, look through the whole repository for what does. When something does, tell the user what stops working and until when, and go on only after the user confirms. That part then does not work until the iteration that moves it, but the tree must still build and the tests must still pass: stub what they still need, with the least code that does it, such as a function that returns an empty result or a fixed value.
- **A dropped design gets a cleanup iteration.** When the user takes another route partway through a category, list what the dropped design left in the tree and suggest reverting it, even when those iterations were done and approved; suggest it without being asked. The cleanup is the next iteration: it removes the code, fields, parameters and tests the new route does not need, adds no feature, and is reported like a move: every file reverted, removed or kept, and why a kept one stays. The iterations it undoes become REVERTED.
- **Old tests made redundant** by new tests at a deeper interface are listed in the report and proposed as a cleanup iteration, reported the same way.

## Starting from a session, without a blueprint

- Before the first iteration, create the pipeline's `knowledge.md` and `iterations.md` under `<blueprint>/pipelines/01-<name>/`, filled from the conversation, in workshop-craft's formats, and the pipeline's record file, unless the record is off. Where the blueprint goes follows `layout.md`; outside a git repository, the suggested folder goes into the first message with the iterations, and the files are written after the user's OK.
- `iterations.md` gets the categories and the first iterations the session implies, all PLANNED, and a suggested iteration size for the user to confirm. Its Done when is written as checkable lines, since there is no scope to point to.
- The first turn ends after the files are written: show the first iterations and the suggested size, and ask the user to confirm them. The first iteration starts after the OK.
- The pipeline's `knowledge.md` also holds the Terms, since there is no `00-knowledge.md`. With no workshop-craft run before it, the mini grill checks the session's words against the code's names, and against the project's glossary when there is one, as above.
- No scope and no work map: those stay workshop-craft's. If the task grows, the user runs workshop-craft, which builds on these files.
- In a git repository, if `.blueprints` is not ignored by git (`git check-ignore -q .blueprints/`, with the slash, which also works before the folder exists), say so in one line and change nothing.

## Reporting an iteration

No fixed headings or labels; how it is written is your call every time. What it carries, when there is something to say:

- What changed, as behaviour, first. Not the files, the tests or the diff size; the user reads those in the diff.
- A check that failed or could not be run, up front. Checks that passed are not listed.
- Something broken that the iteration went around, up front too: a tool, a test helper, a file or a source that does not work as it should, such as stale generated mocks, a Blender add-on that fails or a source page that will not load. Say what is broken, how the iteration went around it, and the fix with its size, offered as an iteration of its own before the planned one. Recommend one way: the fix first when the next iteration needs the broken thing.
- The red line: the new test that went red and what it failed with. It is the one exception to "checks that passed are not listed", because the diff cannot show that the test failed first, and it is the report's only line about tests. A red step that did not go red is a failed check, up front.
- Blockers: the ones the iteration found, and the open ones that stop or shape the next iterations.
- What was skipped on purpose, and when to add it.
- Code written only to keep old code working, such as a write to both the old store and the new one: what it keeps working, the tests that check it, and the iteration that deletes it and removes or changes those tests. The user then reviews the diff knowing which lines are deleted later.
- What could not be verified in the session.
- What exists, what was reused and what is new, as sttp-software-engineering asks of every report.
- What it affects on the platform, as sttp-software-engineering describes.
- For code, a commit point in one line, when the iteration closes a reorganization, a release point or a category. The user can commit at any point; workshop-forge does not commit.
- The plan for the next iteration:
  - what it does: the change in behaviour and what is wrong today, in one or two sentences. Always;
  - a decision for the user, when the mini grill found one the iteration cannot settle alone;
  - an overlap, when something built since the iteration was planned already does part or all of it: what does it, and the question whether the iteration is still wanted;
  - a heads-up, when the user would want to know before saying yes: it changes an existing test's expectation, touches something shared, is noticeably bigger than usual, or reaches other places;
  - the queue after it, in one line, when the user asks what is next or the order changed;
  - the question to continue, last.

  Not in the plan: which files change, what the test is, how the code is shaped.

  The plan questions the next iteration only on a fact found since it was planned. An iteration the user chose stays chosen; the user's answer to another question is no such fact.

Findings, options and questions are numbered and answerable without the code: each option says what it does for the end user or for the readers of the data. Every question stands on its own, with a recommendation.

## End of the pipeline

When `iterations.md` is done: no iteration PLANNED, CURRENT, NEXT or BLOCKED, and no blocker or Not yet clear item left. The pipeline's record file says State built from then until step 6, and in progress while an iteration added by a step below runs.

1. Check the pipeline's Done when items, from the scope or from `iterations.md`, and the checks the scope's Risks name for it ("How we would notice"), against what was built: each one met, with where to see it, or not met. An unmet item becomes the next iteration, and the end of the pipeline stops there: the steps below wait until that iteration is done and the check passes.
2. When the project has a glossary or ADRs (`docs/GLOSSARY.md`, `docs/adrs/`, or its own equivalent), load workshop-glossary with the Skill tool and run its merge: the terms and decisions this pipeline built are proposed for the project's glossary and ADRs, each approved by the user. The proposals end the turn; once the user has answered and the approved entries are written, go on with the next step, so the commit takes them in. With nothing to propose, go on in the same turn. A project without them has not chosen to keep a glossary: skip this step without a word about it, and the Terms stay in the blueprint.
3. For code, suggest committing the pipeline's work before the review, since some review skills read only commits. The commit is the user's.
4. For code, guide the user to a review of everything since the pipeline's `Base:` commit. Give the current condition: the range `<Base>..HEAD` and what is not committed yet. List the review skills you see in this session, numbered, with no recommendation: which one fits is the user's call, and the skills change. Run the one the user picks with the Skill tool; one you cannot invoke, the user types.
5. The findings are numbered for the user. Each accepted finding becomes an iteration, one fix each. A finding about code the pipeline did not change is listed, not fixed. The review runs once: the fixes are not reviewed again unless the user asks, since a review finds something new on every run.
6. The pipeline is done when every Done when item is met, the merge, if there was one, is answered, and every finding is taken, listed or dropped. The Current line says so, and the pipeline's record file says State done.
