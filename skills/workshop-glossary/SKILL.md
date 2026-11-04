---
name: workshop-glossary
description: TARS project glossary and ADRs. Keeps the project's terms in docs/GLOSSARY.md and the decisions that outlive a task as ADRs in docs/adrs/, each entry approved by the user before it is written. In a project that has them, workshop-craft loads it to align a task's terms with the glossary, and workshop-forge loads it at the end of a pipeline to merge what the pipeline built. Use it when workshop-craft or workshop-forge calls for it, or when the user types /workshop-glossary or names workshop-glossary. A plain mention of a glossary is not enough.
---

sttp applies. workshop-glossary keeps the project's language and the decisions that outlive a task in the project, where they last after a task's blueprint is gone:

- `docs/GLOSSARY.md`: the project's terms, what each one is, and the words to avoid for it.
- `docs/adrs/<area>-<decision>.md`: one ADR per decision that outlives a task.

They are optional: a project keeps them by choice, and no skill suggests creating them. A project has them when `docs/GLOSSARY.md` or `docs/adrs/` exists, or its own equivalent of either; workshop-craft and workshop-forge load this skill only then. The first entry of a project without them comes from the user asking, as in Typed by the user.

Reading them needs no skill: every engineering task reads the glossary and the ADRs of its area, as sttp-software-engineering says. This skill writes them, at three points: workshop-craft aligns a task's terms with the glossary, workshop-forge merges what a pipeline built at the end of the pipeline, and the user changes an entry directly.

The formats are in `formats/glossary.md` and `formats/adr.md`. Read a format before writing its file for the first time.

## Where they live

- `docs/GLOSSARY.md` and `docs/adrs/`, at the root of the project: the git repository, or the folder the user named.
- The project's own convention wins. A glossary under another name or place, such as `CONTEXT.md` or a `GLOSSARY.md` at the root, an ADR folder such as `docs/adr/`, or a team's own ADR format: use what is there, in its format.
- A file is created with its first entry; there are no empty placeholder files.
- Outside a git repository, suggest a folder, for example the project's own, and ask before the first file is written.

## What gets in

- **A term**: specific to the project, and used by what was built. The entry says what the thing is, not how the code implements it. A glossary that takes in every answer of a conversation turns into a spec, and every later task reads it.
- **An ADR**: a decision that was built and passes all three tests:
  1. hard to reverse: undoing it costs more than changing the code, because of stored data, an interface other systems call, or people outside the code who rely on it. A format or a setting that one change and its test can undo is not hard to reverse;
  2. surprising without its context;
  3. the result of a real trade-off.

  Most of a task's decisions are about the task, such as its split, its iteration size, where a function goes or the format of what it produces, and they end with its blueprint. A decision about work not built yet is not an ADR: later tasks would read it as in force.
- **Not in an ADR**: mechanics, such as constants, function names and file paths. They tie later work to one implementation.

## Writing an entry

1. Read what is there first: the glossary, and the ADRs of the area. List `docs/adrs/` and open the files whose area the entry touches. A new term that an existing term already covers, or that the glossary lists to avoid, is a question for the user: name the term that covers it, and give the options, such as keeping that term, renaming it, or adding the new one as a different thing, with a recommendation. Nothing is written until the user answers.
2. Show the entry as it will be written, with the text it replaces when it changes one, and wait for the user's answer. An OK approves exactly the entry shown. An unreviewed glossary written by an agent misleads every task that reads it.
3. Write it. An entry is edited in place: a changed term or decision replaces the old text, with no dated amendment under it. An ADR whose decision changes is renamed to match.
4. A superseded ADR is deleted, not marked; git keeps the history. A decision left in the folder is read as in force, and every later task pays for it in context.

Several entries at once, as in a merge, are shown in one message, numbered, each as it will be written. Each is approved on its own, so the user answers by number.

## Aligning a task (workshop-craft)

workshop-craft keeps the task's terms in its blueprint, in the format of `../workshop-craft/formats/knowledge.md`. With a project glossary:

- The task uses the glossary's terms. A word the glossary lists to avoid is replaced by its term, in chat and in the files.
- A clash is a question for the user, with a recommendation: the task means a glossary term differently, needs to rename one, or decides something a glossary entry or an ADR contradicts. The answer goes into Terms, or into the Decisions, as a change to that entry.
- Terms in the blueprint need no approval of their own: each is approved when the merge proposes it. `docs/` is not touched before the merge.

## The merge (workshop-forge, at the end of a pipeline)

workshop-forge runs it at the end of a pipeline, after the Done when check. It also runs when the user asks for a merge by name, for the pipeline the user names; otherwise it does not.

1. Collect what the pipeline built:
   - the terms its work uses, from Terms, with the changes to glossary entries recorded there;
   - the decisions in its `knowledge.md`, and those of `00-knowledge.md` it built, that pass the three tests;
   - the changes to ADRs recorded in the Decisions.

   Terms and decisions of pipelines not built yet stay in the blueprint.
2. Check the existing entries the pipeline touched against what was built: the glossary terms its work uses, and the ADRs of the areas it changed. An entry the work contradicts becomes a proposed change, and so does an `_In the code_` line whose name the code no longer uses.
3. Propose the entries, as Writing an entry says: new and changed terms, new and changed ADRs, ADRs to delete. Say in one line what stays in the blueprint and why.
4. Write the approved entries. Each moves out of the blueprint, it is not copied: remove it from Terms or Decisions, so that later pipelines read the one version in `docs/`. The pipeline's file of the task's TARS Blueprint Record keeps a decision that became an ADR in full, with an `ADR:` line naming its file, as `../workshop-craft/formats/record.md` says.

Nothing to propose: say so in one line. workshop-forge then goes on with the end of the pipeline.

## Typed by the user

`/workshop-glossary` (`$workshop-glossary` in Codex) with a request adds, changes or removes one term or one ADR, as Writing an entry says. With no request, ask what to add, change or remove.
