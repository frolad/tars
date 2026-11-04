---
name: workshop-craft
description: Define a complex task with the user and write its blueprint, the split into pipelines and iterations, for workshop-forge to build from.
disable-model-invocation: true
---

sttp and sttp-software-engineering apply. workshop-craft is the definition stage of a large task. It does the recon, grills the user, and writes the task's blueprint, under `.blueprints/<slug>/` in a git repository: the scope, the knowledge, the blockers, the split into pipelines and categories, and planned iterations. workshop-forge then builds from it, one reviewed iteration at a time.

workshop-craft is not a full spec and not a full plan. workshop-forge always follows it, so the user stays in the loop and the plan emerges while workshop-forge runs. The blueprint holds what workshop-forge needs to start: no user stories, no full list of iterations up front, no interface contracts beyond the one handover line of a release point.

workshop-craft writes only markdown files, in the blueprint's folder. It writes no code and touches nothing in git: no branch, no worktree, no ignore rule. Git setup after workshop-craft, and putting `.blueprints` under git, are the user's decisions. A project's glossary and ADRs, when it has them, change only at the end of a pipeline, through workshop-glossary's merge.

## Before the first question

- Load workshop-grill with the Skill tool. Every question workshop-craft puts to the user follows it: numbered rounds, a recommended answer for each, facts found by you, decisions left to the user.
- When the project has a glossary or ADRs (`docs/GLOSSARY.md`, `docs/adrs/`, or its own equivalent), load workshop-glossary with the Skill tool too: the task's terms then align with that glossary and reach it only at the end of a pipeline. A project without them has not chosen to keep one; the task's terms are built all the same, and creating a glossary is not suggested.
- The text after the command is the task: a description, a ticket, a document, or items of another task's `postponed.md`.
- Called in the middle of a session, workshop-craft starts from what the session already has. With no text after the command, the task is the one the conversation worked on.
- Align the session with workshop-craft's flow first: map its research onto `00-knowledge.md` and its conclusions onto the scope sections, and go on from the first step the session does not cover. What the session settled is not redone; what workshop-craft needs and the session lacks is asked.
- Research done in the session is recon. Its facts go to `00-knowledge.md` with their source; re-read the ones that rest on code not read in this session, such as facts carried over in a summary. Decisions the user took in the session are written as decisions and not asked again. The first round confirms the reading of the session: the intent, those decisions, and where the flow goes on, for the user to correct.
- A decision taken in chat is not an approved In scope or Out of scope: their text is still shown and approved.
- A blueprint for the task may already exist, from an earlier session or from a pipeline workshop-forge started without one. Build on it: read it, keep what it holds, and continue from the Current line of its `02-scope.md`.
- Search `docs/tars-reports/` for the task's area before the recon: the TARS Blueprint Records of earlier tasks keep their decisions, traps and known issues.
- Do the recon first: the code the task touches, the documents it names, the sources the user gave, and, when the project has them, its glossary and the ADRs of the areas the task touches. A subagent's recon report goes to the blueprint's `recons/`, as `formats/layout.md` says.

## The levels

Guidance, not a fixed structure. A task uses only the levels it needs, and levels grow as the work goes. workshop-craft suggests the split; the user decides it.

1. Task: huge work, like an epic. One folder under `.blueprints`, one scope.
2. Pipeline: work that can run in its own worktree or go to another person.
3. Category: an affected area or a specific feature.
4. Iteration: one step workshop-forge runs, one per turn cycle.

## The flow

1. **Define the task.** The first round of the grill confirms the intent. workshop-craft fits any work complex enough to split into pipelines and iterations, not only code: engineering and architecture, research, a design in a tool such as Figma or Blender, and other kinds. Outside software, leave out the scope sections that do not fit, such as Who reads what we write.
   - If the task is really several tasks, say so in this round, before any detailed question, and ask which one to craft first.
   - Compare the task's words with the names the project already uses for the same things: what its users see (pages, UI, docs), the code, and the glossary and ADRs when there are any. These are questions of this round, since they change what the task means: a word the project uses for a different thing; a task word that differs from what the project's users see, so the user picks the one the task uses; a contradiction with a glossary entry or an ADR. Only the code's internal name differing, such as `Transaction` behind "sale" on every page, is not a question: say so, and it goes to Terms as the code's name.
   - Short path: if the recon shows the task fits in one session and leaves no decision to the user, say so and suggest running workshop-forge on the session instead of writing a blueprint.
2. **Settle where the blueprint lives**, as `formats/layout.md` says: `.blueprints/` in a git repository, checked to be ignored by git (`git check-ignore -q .blueprints/`, with the slash, which also works before the folder exists); a folder the user names; or, outside a git repository, a folder you suggest and the user confirms. The slug is one no other task's record has, as `formats/layout.md` says.
3. **Fill the scope with the grill.** The files are created once the task is confirmed. Read `formats/layout.md` before the first one, and each file's format in `formats/` before writing that file.
   - Settle the destination first: Task, Goal and Done when. Then the other sections.
   - Facts come from the codebase, internal documents and other sources, and go to `00-knowledge.md` with their source and the date read. Decisions go to the user; once taken, they go to the knowledge too, with why and what they rule out.
   - The words the task uses go to the Terms section of `00-knowledge.md`, as `formats/knowledge.md` says: what each one means in this task, the words to avoid, and the code's name when it differs. Use them in chat and in every file. workshop-forge reads them in every iteration, and a task word mapped to the wrong thing in the code is built wrong. With a project glossary, align them with it as workshop-glossary says.
   - In scope and Out of scope are proposed in chat as the text that goes into the file, as a question of the round: they draw the line of the task. An OK approves exactly the text shown, and workshop-craft writes exactly that text.
   - Every other section has no question of its own. It is written as soon as the rounds have settled what it says, Current state from the code, and rewritten when a later answer changes it. One line in chat names what was written: "Written to the scope: Current state, Risks. You'll review them at the end." The user reads them in the review.
   - What must be resolved before the scope can be finished goes to `01-blockers.md`.
4. **Self-check the scope** once every section is written: placeholders, contradictions between sections, vague lines, Done when items that cannot be checked. A finding in In scope or Out of scope becomes a new proposal in chat, its text before and after. Any other is fixed in the file and named in the review.
5. **Propose the split, in one message:**
   - the levels this task needs;
   - the pipelines: a few sentences on what each does, what each waits for, and the resulting order. Each one can run in its own worktree or go to another person. Pipeline size is the user's choice: give a suggestion, the reason, and what each way of cutting costs:
     - by concern: small pipelines with focused knowledge, and parallel work is easy to see. Cost: more waits between pipelines, and a work map that changes more often as pipelines are found;
     - by page or surface: matches how the user reviews and ships, with few waits. Cost: shared work lands in one pipeline and blocks the others;
     - one pipeline for everything: no work map to maintain, the categories carry the structure. Cost: long files that mix concerns, and nothing shows what could run in parallel;
   - each release point, and what it hands over;
   - the categories of each pipeline;
   - the suggested iteration size, in words.

   Before sending it, check that every numbered Done when item belongs to at least one pipeline. An item with no owner means a pipeline is missing or the item should leave the scope; propose either one. The message writes each Done when item out in full, next to the pipelines that check it, not only its number: Done when has no question of its own, so this is where the user reads it before anything is built on it.

   The user corrects and confirms the split. Then write `03-workmap.md`, only with more than one pipeline, and one `iterations.md` per pipeline.
6. **Planned iterations** go into each `iterations.md` with the split, without a separate confirmation, because workshop-forge proposes each one again before running it. Each gets a row in the status table, PLANNED. Write one only when it can be stated sharply; work that cannot be stated sharply yet gets one line under Not yet clear. A decision still open goes under the pipeline's Blockers, naming the iteration it blocks, which is then BLOCKED.
7. **Review.** Once the split is written and `01-blockers.md` is empty or absent, one message lists each file written, its path and what it holds, marks the scope sections the user has not seen in chat, and names the self-check's fixes. It ends by asking the user to read the files and reply OK or name what to change, after the list and the fixes. The message is text, never a question tool's call: the turn ends with it, so the user reads the files before answering. Nothing is asked again: In scope, Out of scope and the decisions of the rounds stand as approved. A change is made and the list shown again; a change that moves the split proposes the split again.
8. **End.** The user's OK confirms the whole blueprint. The scope's Current line gives way to `Confirmed on:` with the date of the OK. The last message names the pipeline that can start and how to start it: `/workshop-forge <task> <pipeline>` (`$workshop-forge` in Codex), with the blueprint's path in place of `<task>` when it is not under `.blueprints/`. Starting workshop-forge is the user's step, so workshop-craft ends with that message.

## Files

The md files are your working state; the user works in chat. The exception is `02-scope.md`, which both of you read. A file is created when it first has content, and every file shows the current state, not the first plan. The layout and the rules all files follow are in `formats/layout.md`; each file's format is in `formats/`, named after the file: `scope.md`, `knowledge.md`, `blockers.md`, `workmap.md`, `iterations.md`, `postponed.md`.
