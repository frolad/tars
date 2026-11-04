---
name: workshop-grill
description: TARS interview procedure. Maps a plan as a design tree and puts its open decisions to the user in numbered rounds, each question with a recommended answer, until nothing is silently assumed; the agent finds the facts itself. workshop-craft loads it to grill a task's scope and split, and workshop-forge loads its light mode for the mini grill before each iteration. Use it when workshop-craft or workshop-forge calls for it, or when the user mentions "workshop grill" or "grill workshop" or types /workshop-grill. A plain "grill me" is not enough.
---

sttp applies. A grill reaches a shared understanding of a plan before anything is built. The facts are yours to find; the decisions are the user's. The grill itself edits nothing: what gets written, and when, is decided by the skill that loaded it.

## Before the first round

- Read the sources in full: the plan, the documents it names, the code it touches. A question asked from half a source is often answered in the other half.
- The first round confirms the intent. State your reading of the goal, and of what the thing is for, as recommended answers the user can correct. No detail question (names, file formats, layouts) comes before the intent is shared: details decided against a misread goal get decided twice.

## Rounds

Map the subject as a design tree: every decision branches into the decisions that hang off it. The frontier is every decision whose prerequisites are settled, the questions that can be asked now without guessing at answers not heard yet.

- Ask the whole frontier in one round. Number each question and give a recommended answer. Then stop and wait for the answers.
- A question whose answer depends on another question still open in the same round goes to a later round.
- Each round of answers reshapes the tree: settled decisions unblock the ones that hang off them. Recompute the frontier and ask the next round.

## Facts and decisions

- Finding facts is your job. When a question needs a fact from the environment (the code, files, docs, tools), look it up, through a subagent when it takes digging. Never ask the user for a fact you can find. Do not block on the lookup: only the questions downstream of it wait, and the rest of the frontier is asked now.
- A fact you could not settle is written "unverified", with what would settle it.
- Decisions are the user's. Put each one to the user and wait; a recommendation is not a decision.
- Each option says what it does for the end user or for the readers of the data, not only what changes in the code.

## Format

Questions and options, in either form below, are phrased in sttp's plain terms. A question's title names its subject in the user's words: `Q21 - Check 11: the skills don't get worse`, not `Q21 - Done when 11`. The question says what goes wrong, with a concrete picture for what the user has not seen: a skeleton of the file, a before and after, a small example.

The user picks the question form with `/workshop-questions`: `dialog`, the default, or `transcript`. The prompt hook's reminder says "Grill questions: in the transcript" while `transcript` is set. With `dialog`, and a tool that puts questions to the user with options to pick, such as AskUserQuestion in Claude Code, a round is asked through that tool. With `transcript`, or with no such tool, it is asked in the transcript.

- Through the tool:
  - First, a response of its own carries everything the round rests on that the user has not seen: the facts found, and any text to approve, such as a task description, a scope section or a file, printed in full, exactly as it will be written. It ends with a tool call: updating the working file's Current line to say the round waits on the user, or, with no working file, reading a file the round rests on. A line announcing a text ("I'm presenting the Task text") does not show it, and nothing is "shown above" unless that response holds it.
  - Then the next response is the tool call alone, with no text: text written in the same response as the call does not reach the user.
  - Up to 4 questions per call and 2 to 4 options per question, so a bigger round takes several calls in a row. Each question starts with its number and title (`Q3 - <title>: …`). The recommended option comes first, its label ending in "(Recommended)". Each option's description says what it does for the end user or for the readers of the data, and the recommended one's also says why, in one line. A question where several options can be picked has a "none of these" option: with nothing picked, the answer comes back empty, and the user has no way to say none. Each question makes sense on its own: what it rests on is in the question, its options or the response before it. No side box (`preview`) on any option: it cuts anything past a few lines, so a draft or a before and after goes in the response before. The user's own answer goes through the tool's free-text field.
- In the transcript, a round looks like this:

```
❓ **Q1** - **<title>**: <the question, with the options when there are several>

➡️ <the recommended answer, and why in one line>

---

❓ **Q2** - **<title>**: ...
```

Word each question so that "yes" accepts the recommended answer. A text to approve goes under its question, exactly as it will be written. A rule between questions, and no emoji besides ❓ and ➡️. The user answers by number ("Q1: yes, Q2: option 2"). In either form, numbers count once per session: Q1 is the session's first question, and the count goes on through every round, every mini grill and every grill a skill loads, after a compaction too. A question asked again keeps its number, and a new question takes the next number not used yet in the session. A new session starts at Q1.

## Answers

- An answer approves exactly the option shown. Anything beyond it is a new question for a later round.
- An unsure answer ("idk", "not sure") gets a narrower question or a firmer recommendation, never a silent assumption.
- "Explain", or any sign of confusion, means the question was still not answerable. Re-ask it with a more concrete picture, not a longer abstract version. When the user took it for another point, say in one line that the two are separate.
- When the user stops the grill, re-read the sources and restate the intent before going on.

## Done

The grill is done when the frontier is empty: every branch visited, nothing silently assumed. Say so, list the decisions taken, one line each, and ask the user to confirm that the understanding is shared. Nothing is acted on before that confirmation.

## Light mode

For workshop-forge's mini grill before an iteration, or whenever the caller asks for light mode. The rules above hold, narrowed to one piece of work that is already defined; it is light because the recon was done before.

- Start from the engineering check of sttp-software-engineering (ask, exists, facts, architecture, size), applied to this piece of work only. Read what the caller names first, such as the iteration's line and its knowledge files, and read code only for what they do not cover.
- Resolve every fact yourself. Only decisions reach the user.
- No intent round: the intent comes from the work's own description. Ask about it only when the check's first question has no clear answer.
- The check is your working, not the message. The message holds the decisions, each with the facts it rests on, and fits in one short message. What exists and what was reused go in the report of the work, not here.
- After the user answers, run it again, and ask follow-ups only for what is still open.
- When nothing needs the user, one line says so, with no question and no closing confirmation, and the caller goes on with the work.
