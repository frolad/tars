# Starting from a session, without a blueprint

What workshop-forge does when it starts from what the session discussed, with no blueprint: the files it writes before the first iteration, and the first turn.

- Before the first iteration, create the pipeline's `knowledge.md` and `iterations.md` under `<blueprint>/pipelines/01-<name>/`, filled from the conversation, in workshop-craft's formats, and the pipeline's record file, unless the record is off. Where the blueprint goes follows `layout.md`; outside a git repository, the suggested folder goes into the first message with the iterations, and the files are written after the user's OK.
- `iterations.md` gets the categories and the first iterations the session implies, all PLANNED, and a suggested iteration size for the user to confirm. Its Done when is written as checkable lines, since there is no scope to point to.
- The first turn ends after the files are written: show the first iterations and the suggested size, and ask the user to confirm them. The first iteration starts after the OK.
- The pipeline's `knowledge.md` also holds the Terms, since there is no `00-knowledge.md`. With no workshop-craft run before it, the mini grill checks the session's words against the code's names, and against the project's glossary when there is one, as the mini grill in `SKILL.md` says.
- No scope and no work map: those stay workshop-craft's. If the task grows, the user runs workshop-craft, which builds on these files.
- In a git repository, if `.blueprints` is not ignored by git (`git check-ignore -q .blueprints/`, with the slash, which also works before the folder exists), say so in one line and change nothing.
