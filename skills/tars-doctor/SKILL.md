---
name: tars-doctor
description: Checks that STTP works in this session and is back on course. Reloads the STTP rules and the running TARS skills that got lost, names where the recent turns drifted from them, and shows the session's TARS notes and which copy of TARS runs. For when STTP seems not to work or the work went off course.
disable-model-invocation: true
allowed-tools: Read
---

The user calls this when STTP seems not to work, or the work drifted from its course. Find what is missing or off, put back what reading a file puts back, and say what was wrong. This turn does no task work and changes no task files: a fix that would is proposed and waits for the user's go. When the user said what went wrong after the command, start from it.

## What the session should have

The TARS prompt hook answered the command with a "TARS doctor" block: which copy of TARS runs, whether STTP is on or paused, the rules the hooks sent, the git guard, the question form, the pipeline `/workshop-forge` named, the skills started in this session with their working files, and where the skill files are.

- No such block came with the command: the prompt hook did not run, and that is the first finding. Without it nothing sends the rules again after a compaction. Likely causes: the plugin is off or not installed (`/plugin` in Claude Code, the plugin list in Codex), Codex has not trusted the hook (`/hooks`), or `python3` is missing. Go on with what you can see, with the skill files in the folders next to this skill's.
- STTP is paused: say so, and that `start sttp` turns it back on. Reload nothing and check no drift: the rules are off on purpose.

Otherwise these should be in your context:

- `sttp` and `sttp-software-engineering`, always;
- `sttp-software-coding` and `sttp-software-testing`, when the block says they were sent; when not, they come back at the next edit and are not read now;
- each skill the block says was started and is still running, that is, its working file's Current line does not say it is done or confirmed. `workshop-craft` and `workshop-forge` also load `workshop-grill`, and `workshop-glossary` when the project has a glossary or ADRs (`docs/GLOSSARY.md`, `docs/adrs/`);
- any other TARS skill you can see was in use and is not finished, such as `sttp-enforce` partway through.

## Check and reload

1. For each one, look for its text in your context: the hook's blocks ("STTP active:", "STTP engineering active:", "STTP coding active:", "STTP testing active:"), a skill's body, or, after a compaction, the skills re-added as invoked earlier. A mention in a summary is not its text, and neither is a block that arrived as a short preview with the rest saved to a file ("Output too large … Full output saved to"): until now the session worked from the preview alone, so it counts as missing. After a compaction Claude Code keeps 5,000 tokens of each skill and 25,000 in all, dropping the oldest first, so a skill loaded early can be gone.
2. Read the SKILL.md of every one on the list, the present ones too: a missing one is reloaded, and a present one is fresh for the drift check. Read the file rather than invoking the skill again: a skill invoked again with the same text only gets an "already loaded" note.

## Drift

Compare your recent turns, newest first, with the rules and skills just read and with the running skill's working file. Drift is what they ask that the turns did not do, or did the other way. For example:

- an answer that opens with a lead-in, or carries what sttp cuts;
- workshop-forge doing the next iteration without the user's "continue", or two in one turn;
- the pipeline's Current line or status table behind the work done;
- a decision taken without asking the user.

Each finding names where it happened, the rule, and what you do from now on.

## Report

What was wrong and what was done first, then what is in place, then the notes, with the TARS version and folder. When nothing was wrong, one line. A fix waiting for the user's go ends the report, as a question.

```
TARS doctor
- sttp and engineering arrived cut to a preview at the compaction: reloaded in full
- workshop-forge was dropped at the compaction: reloaded
- off course: iteration 2.4 started in the same turn as iteration 2.3's report, without your "continue". From now on
  one iteration per turn; iteration 2.4's changes wait for your review
- coding and testing rules: come back at the next edit
- in context: workshop-grill
- notes: TARS 0.3.0 from ~/work/pets/sttps, mode primary, guards on, pipeline tars-mod 01-mvp
```

```
TARS doctor: all intact, no drift. In context: sttp, engineering, workshop-forge, workshop-grill. Notes: TARS 0.3.0 from
~/work/pets/sttps, mode primary, guards on, pipeline tars-mod 01-mvp.
```
