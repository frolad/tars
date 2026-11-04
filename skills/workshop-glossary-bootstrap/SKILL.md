---
name: workshop-glossary-bootstrap
description: Build the glossary of an existing project with the user, area by area, and ADRs for the surprising decisions the user explains. Each proposal is approved before it is written; workshop-glossary keeps the files afterwards.
disable-model-invocation: true
---

sttp and sttp-software-engineering apply. workshop-glossary-bootstrap builds the glossary of an existing project in one run: its terms, and ADRs for the decisions in the code that the user explains. The scope is one area, several, or the whole project. Afterwards workshop-glossary keeps the files, through workshop-forge's merge and `/workshop-glossary`.

It exists because workshop-glossary grows a glossary one pipeline at a time, and on a large codebase most of the domain never comes up in a task. Asking about each term one by one runs to dozens of questions. This run reads the project first and asks only about collisions and surprises.

A project's glossary is its own choice. The user starting this skill makes that choice; nothing else suggests it.

## Before the plan

- Load workshop-glossary with the Skill tool. It holds where the files live and the project's own convention, the entry formats, what gets in, the three ADR tests, and how an entry is shown and approved. This skill holds only the run's flow.
- The text after the command names the areas: `/workshop-glossary-bootstrap [areas]` (`$workshop-glossary-bootstrap` in Codex). With none, the plan proposes the scope.
- A working file from an earlier run, `.blueprints/glossary-bootstrap/bootstrap.md`, means the run continues: read it and go on from its Current line, with no new plan. The same holds after a compaction.
- Do the recon for the plan, which is cheap: the project's layout, its README, CLAUDE.md, AGENTS.md and `docs/`, the glossary and decision records it already has under any name, and enough of each area to judge its size. The mining comes after the plan.

## The plan: the first turn

The first turn is the plan, for the user to confirm or correct. Nothing is written in it.

- **Scope**: the areas named after the command, or the whole project, as a list of areas with a line each on what it holds. An area is a part with nouns of its own: an app of a monorepo, a module, a service; outside software, a part of the project's files.
- **Size**, from the recon: small, meaning one area or a project one agent can read in a session; or large.
- **How it is mined**: inline, one area at a time, for a small run. For a large one, one read-only subagent per area, in parallel, where the harness has subagents.
- **Order**: core first. The areas whose nouns the others use come first, so later groups align with the terms already approved.
- **What exists**: the glossary and the decision records the project has, and where. Their entries stand, and only what is missing is mined. A glossary section inside the README stays there unless the user agrees to move it to a file of its own: ask.
- **Where it writes**: the existing glossary, or `docs/GLOSSARY.md` and `docs/adrs/` as workshop-glossary says; and the working file, `.blueprints/glossary-bootstrap/bootstrap.md`. In a git repository, check that `.blueprints` is ignored (`git check-ignore -q .blueprints/`, with the slash, which also works before the folder exists); if it is not, say so in one line and change nothing. Outside a git repository, suggest a folder for the working file and ask.

What the user decides, such as the scope, the order or a move of the README section, is a numbered question with a recommendation. End the turn with the question to start.

## Mining

Once the plan is confirmed, create the working file in the format of `formats/bootstrap.md`, with the plan. Then mine as `mining.md` says: the sources, what a term, a collision and a surprise are, and the shape of an area's result. Read it before the first area.

- **Small**: mine the first area inline, write its result to the working file, and propose its first group. The next area is mined once the last group of the one before is answered.
- **Large**:
  1. Map the areas; the plan did.
  2. Mine every area in parallel, one read-only subagent per area. Give each the area and its paths, the path of `mining.md`, and the terms the glossary already has. Write each result to the working file as it arrives.
  3. Merge across areas. A thing two areas name differently, or a name two areas use for different things, such as billing's "account" against auth's "account", shows only here. Record it as a collision of the area proposed first.
  4. Propose area by area, in the plan's order.

  Without subagents, mine the areas one after another, writing each to the working file before the next, so a compaction loses nothing.

## Proposals

One proposal per turn, as in workshop-forge: shown, answered, the approved entries written, then the next proposal.

- A proposal holds one term, or a group of up to about 10 terms from the same area. A bigger area is split into several groups.
- Each entry is numbered and shown as it will be written, in the glossary's format: the existing glossary's own format when there is one. A change to an existing entry shows the text it replaces.
- The plain terms, with one meaning and no competing name, need no question: the user answers them in one line, such as "yes, except 4: …".
- Each collision and each surprise of the group is a numbered question in the same proposal, `Q<n>`, with the options and a recommendation. The numbers count once per session: they go on from the session's last question, through every group and after a compaction, and a new session starts at Q1. The number of questions is the number of collisions and surprises, not of terms.
  - **A collision**: one thing named differently in two sources, such as `Customer` in the code and "client" on every page, or one name used for two things. Recommend the word the project's users see, on its pages and in its docs, with the code's name as `_In the code_`, unless that word already means something else.
  - **A surprise**: what the code does and where, why it looks deliberate, and what git shows of its why. When git gives the why, show the ADR as it would be written, as an option. When it does not, ask the user for the why. A surprise the user cannot explain is dropped, never guessed.
- An OK approves exactly the entries shown, as workshop-glossary says. An entry the user changes in the answer is written as changed when the answer gives its exact text; otherwise it is shown again in the next proposal.
- In the turn of the answer: write the approved entries, take them and the dropped ones out of the working file, move its Current line on, and show the next proposal. A decision in an answer, such as the word a collision keeps, holds for the later groups too.

## What is written

- The glossary entries, in the file the plan names, in the existing glossary's format or else in workshop-glossary's. A file is created with its first entry.
- When the chosen term differs from the code's name for the thing, the entry gets `_In the code_: <name>`, as workshop-glossary's format says. The term is also a rename candidate: note it in the working file. A rename is a task of its own, not a glossary edit.
- An ADR for each surprise the user explained, in workshop-glossary's ADR format, with these fields for an old decision:
  - Decided by: whoever the user names, or "the team".
  - The date: that of the commit that introduced the decision, when git shows it; otherwise "before <today>".
  - A last line: `Confirmed by the user on <today>.`
- The decision records the project already has stay as they are, in their own format. An existing glossary entry changes only as a proposed change the user approved.
- Nothing else: no code, and nothing in git. The commit is the user's.

## The end

The run ends when every area of the scope is answered. Delete `.blueprints/glossary-bootstrap/`, then send the last message:

- what was written: the terms and the ADRs, by file;
- the areas not covered;
- the rename candidates: each term and the code's name for it;
- that the commit is the user's;
- `/workshop-craft <task>` (`$workshop-craft` in Codex), only when the session has a task waiting.

A run the user stops earlier keeps the working file, so `/workshop-glossary-bootstrap` continues it later. Its last message says so and lists the areas not reached as not covered.

## Outside software

The run is the same for any project with files, such as a research folder or a design system. The sources are the project's own files, the terms are the project's, and a surprise is a choice in its structure that looks deliberate.
