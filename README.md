# TARS

For engineers who still want to be engineers, in the age of AI agents.

Honestly, you can skip the rest of this page: [install it](#install), run `/workshop-craft` on a real task or two,
and see if it brings back the joy of software engineering for you, as it did for us.

TARS is a plugin for Claude Code and OpenAI Codex: skills and hooks that change how you work with an agent.

- **Several tasks at once, instead of a long spec for one.** The usual way to hand an agent a big task is hours of
  spec and plan, a long run on its own that drifts as it goes, and a huge diff at the end. With TARS you define the
  task in a conversation, then the agent builds it one reviewed step at a time, at the size you set, and stops after
  each step with a report and the next step. Coming back to a task means reading that report, not reloading the
  whole plan into your head, so you keep several tasks moving in separate worktrees and stay in the loop on all of
  them.
- **You decide, the agent finds the facts.** Before each step the agent looks up what it can and asks you only the
  decisions, each with a recommendation. Nothing gets built on a design nobody chose.
- **Straight to the point.** The `sttp` rules make the agent answer first, in plain words, change the smallest code
  that does the whole job, and mark as unverified what it has not read.

## What is different

Numbers from a month of the author's own use, October 2026: 16 tasks, 396 steps that each ended in a stop for
review, up to 4 tasks moving at once, and 1,002 questions answered.

- **A small way back in.** A task keeps its state in files under `.blueprints/`. The line that says where it stands
  and the table of its steps are about 4% of them, so coming back takes a read, not a re-plan. Half the replies to a
  stop were a short go-ahead such as "next", and coming from another task, the median reply came 54 seconds after
  the last message there. The work also goes on after Claude Code compacts the session: 47 of 55 compactions led to
  more steps.
- **The plan changes in the open.** Of 467 planned steps, 127 were added from facts found on the way, 42 came from
  splitting a step, and 33 were dropped with a reason. 55 facts were corrected in place, and 616 decisions are on
  record with who took them and when.
- **Broken things are flagged, not worked around.** A tool or test helper that does not work opens the report, and
  its fix is offered as a step of its own.
- **Moves are reviewed as moves.** Moving or renaming code is a step of its own, with no feature in it, so its diff
  reads in a minute.
- **Your git stays yours.** What you staged is what you reviewed: the agent stages, commits or pushes only when you
  ask, and a guard in both tools holds it to that.
- **Records outlive tasks.** Each pipeline writes a record that you commit with the code: why it is the way it is,
  the decisions, the traps and the known issues. The next task reads it.
- **A code review's findings become steps you pick**, each built and reviewed like any other step.
- **Claude Code and Codex.** The same skills and files work in both. In Claude Code, an optional mod adds a status
  line and a pane with the running pipeline.

## Install

Claude Code:

```
/plugin marketplace add frolad/tars
/plugin install tars@tars
```

Optional, Claude Code only: the TARS mod answers `/sttp-mode`, `/sttp-guards` and `/workshop-questions` at once, pins a status
line under the prompt and shows the pipeline `/workshop-forge` runs in a pane, which `/workshop-forge-pane` opens and
closes (see Controls). TARS works the same without it.

```
/plugin install tars-mod@tars
```

Installed it as `sttps` before? It is `tars` now: run `/plugin marketplace remove sttps`, then the install above.
Your settings move with `mv ~/.sttps ~/.tars`. From a clone, replace the old `sttps` and `sttps-mod` links with the
two below.

Claude Code, from a clone, so your edits and `git pull` apply at the next session start:

```sh
git clone https://github.com/frolad/tars.git
cd tars
mkdir -p ~/.claude/skills
ln -s "$PWD" ~/.claude/skills/tars
ln -s "$PWD/mods/tars-mod" ~/.claude/skills/tars-mod   # optional mod
```

Claude Code loads every folder in `~/.claude/skills/` that has a `.claude-plugin/plugin.json` as a plugin, in every
session, from where it is: no `/plugin install` step. Keep the clone where it is, since the links point at it. Use
either this or the marketplace install, not both: both would load. To remove it, delete the two links.

The hooks need `python3` on the PATH, in both tools. On Windows, a fresh install has only the Microsoft Store's
`python3` shortcut, which prints "Python was not found" and runs nothing, so the hooks fail until Python is installed.
python.org's install manager gives a real `python3`: `winget install Python.PythonInstallManager`, then, in a new
terminal, `py install --yes default`.

Codex (from this local checkout):

```sh
codex plugin marketplace add .
codex plugin add tars@tars
```

Codex (from GitHub):

```sh
codex plugin marketplace add frolad/tars
codex plugin add tars@tars
```

The marketplace points to the plugin at its own root, so a local install uses
this checkout and a GitHub install uses the downloaded checkout.

In Codex, open `/hooks` and review and trust every TARS hook it lists, once.
Then start a new conversation. STTP loads automatically at startup, resume,
clear, and compaction, as it does in Claude Code. Say `stop sttp` or
`normal mode` to turn it off in the conversation.
You can also invoke the installed plugin skill directly with `$tars:sttp`
without enabling its hook.

Codex skips untrusted plugin hooks even when the plugin is enabled. The hooks
print the STTP rules and the session's notes, block the git steps listed under
Controls, and keep their notes in `~/.tars/`; Codex supplies
`CLAUDE_PLUGIN_ROOT` for compatibility. See the [Codex hook documentation](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks).

For manual activation without the plugin or hook, link just the skill from this
checkout into Codex's user skill directory:

```sh
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/sttp" ~/.agents/skills/sttp
```

Then use `$sttp` in Codex. This link follows edits to this checkout; keep the
checkout in place. Choose either the plugin or the skill link to avoid duplicate
skill entries. See [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills).

After changing an installed local plugin, update its manifest version and run
`codex plugin add tars@tars` again to refresh the installed copy. Start a new
conversation; changed hook definitions require another review in `/hooks`.

## Quick start

Pick a change too big for one session, in a git repository, and add `.blueprints/` to its `.gitignore`: the agent
keeps its notes on the task there. Say the reports page needs CSV exports:

1. `/workshop-craft add CSV exports to the reports page`. It reads the code, then asks about the task in rounds;
   each question comes with a recommended answer, so most answers are a pick. It ends with the list of files it wrote:
   read them, reply OK, and it names the command that starts the work, such as `/workshop-forge exports 1`.
2. Run that command. One iteration runs, sometimes after a question about a decision only you can take. The turn ends
   with a report, the next iteration and a question to continue.
3. Read the report and the diff. Reply `continue` to approve it and start the next one, or say what to change.
   Nothing is committed: you commit when you like.

Use, below, has more on each command.

## Use

The rules need no command. `sttp` and `sttp-software-engineering` load at session start and after each compaction,
`sttp-software-coding` and `sttp-software-testing` before the first edit.

For work too big for one session, such as an engineering task, a research topic or a design:

1. `/workshop-craft <task>`, with the task as a description, a ticket or a document. It reads the code and the sources,
   asks you about the task in numbered rounds, each question with a recommended answer, and writes the task's
   blueprint: the scope, the facts found, and the split into pipelines and iterations. You approve the scope's In scope
   and Out of scope as it writes them, and the rest once, in a review of the written files at the end. In a git
   repository it goes to `.blueprints/<task>/`, which should be ignored by git; workshop-craft says so when it is not,
   and changes nothing in git.
2. `/workshop-forge <task> <pipeline>`, such as `/workshop-forge exports 2`, builds that pipeline one iteration per turn. Each
   turn ends with a report and the next iteration; your "continue" approves the one done and starts the next. It does
   not commit; you commit when you like. At the end it checks the result against the scope's Done when list and
   guides you to a review. `/workshop-forge` alone, after a session that discussed the work, starts a pipeline from that
   session, without workshop-craft.

Each task in a git repository also gets a TARS Blueprint Record, the folder `docs/tars-reports/<task>/`: why its code
is the way it is (the decisions with their reasons, what was tried and dropped), its traps, known issues and postponed
work, and where each pipeline stands (in progress, built once every iteration is done, done after the end of the
pipeline). Each pipeline's workshop-forge writes its own file, such as `01-csv-downloads.md`, with what a reader needs
from the task's plan, so pipelines on separate branches never edit the same file. The folder sits at the repository's
root, and you commit each pipeline's file with its work. The files are written from the blueprint in the same
turn something changes, and leave out what must not reach a
shared repository, such as secrets, people's names, production data and home paths. Teammates and later sessions find it by searching `docs/tars-reports/`;
workshop-craft searches it before its recon. The code stays the source of truth, and each record's first lines say so.
To turn it off for a repository, have git ignore `docs/tars-reports/` (in `.gitignore` for everyone, in
`.git/info/exclude` for you alone); for one task, say so, and the agent adds `Record: off` to the blueprint and deletes
its record.

Other commands:

```
/sttp-enforce <path>        lists what sttp would change in the files under a path; writes what you pick
/workshop-glossary-bootstrap    builds an existing project's glossary and ADRs in docs/, area by area
```

After the bootstrap, workshop-craft and workshop-forge keep the glossary: a pipeline's new terms and decisions are proposed for
it at the pipeline's end. In Codex, type `$` instead of `/`: `$workshop-forge exports 2`.

## Controls

Pause for this conversation: say `stop sttp` or `normal mode`. Resume: `start sttp`.
The pause survives compaction and a move to the background, and ends with the session.

Mode, persistent, stored in `~/.tars/mode`, shared by Claude Code and Codex:

```
/sttp-mode            show current mode
/sttp-mode primary    main thread only (default)
/sttp-mode full       subagents too: rules injected at subagent start, coding rules fire inside subagents
```

In Codex type `$sttp-mode full`. Turning the plugin off entirely is `claude plugin disable tars`
or the Codex equivalent; there is no off mode.

How workshop-grill asks its questions in `/workshop-craft`, workshop-forge's mini grill and `/workshop-grill`, persistent, stored in
`~/.tars/questions`, shared by Claude Code and Codex:

```
/workshop-questions             show the current form
/workshop-questions dialog      the question dialog, when the tool has one (default)
/workshop-questions transcript  as text in the transcript
```

In Codex type `$workshop-questions transcript`. Where there is no question dialog, the questions come in the transcript
either way. While `transcript` is set, the reminder the hook adds to every message says so, which is how a running
grill learns it, open sessions included.

The git guard, in both tools: `git add`, `git commit`, `git push`, `git tag`, `git stash`, `git reset` and
`git restore --staged` show Claude Code's approval prompt. Codex cannot ask from a hook, so there the step is blocked,
with the reason shown in the session, unless the user's latest message names it: "commit", "push", "tag", "stash",
"reset", "stage" or "add" for `git add`, "unstage" for `git restore --staged`. In Codex, a message that is just
`allow` lets a blocked step through until the next message.

`stop sttp` turns the guard off with the rest of STTP. For the guard alone:

```
/sttp-guards              show whether it is on in this session, and the default
/sttp-guards off          off for the rest of the session
/sttp-guards on           back on for the rest of the session
/sttp-guards default off  off in every session without its own on or off, open ones too, in every project
/sttp-guards default on   back to on as the default
```

In Codex type `$sttp-guards off`. Not checked: subagents' git steps. The default is kept in `~/.tars/guards-default`,
shared by Claude Code and Codex; with none set, the guard is on. A session's own switch is kept in
`~/.tars/guards-off-<session>` and wins over the default. Only you can call `/sttp-guards`: the agent is not offered
it, so it cannot turn the guard off itself.

When STTP seems not to work, or the work drifted from its course:

```
/tars-doctor          check the session, put back what got lost, name the drift
```

`$tars-doctor` in Codex. The hook tells the agent what the session should have: which copy of TARS runs, its
version, the mode, the pause, the git guard, the question form, whether the coding rules were sent, the pipeline `/workshop-forge` named and
the skills started. The agent reads the STTP rules and the running skills from their files again, compares its recent
turns with them, and reports what was wrong first; a fix that changes files or starts work waits for your go. Only you
can call it, and it reads the skill files without asking, in that turn only.

With the optional mod in `mods/tars-mod/` (Claude Code only), `/sttp-mode`, `/sttp-guards` and `/workshop-questions`
answer at once, with no model turn. Without it, the hook answers and the model repeats its line.

The mod also pins a status line under the prompt: the STTP mode, or `paused`, and the pipeline `/workshop-forge` named in
the session with its CURRENT row, else its NEXT one, else its first PLANNED or BLOCKED one, from the pipeline's status
table, and how many of its iterations are done, such as `⚠ tars-mod: primary · csv → CSV → header row · CURRENT · 1/3`
(the terminal draws `⚠ tars-mod:` before every mod's status line; the desktop app's status bar shows `tars-mod`). The count leaves out the iterations dropped, reverted, split or
left for later. It follows each turn and each write under `.blueprints/`. To hide it, turn tars-mod's `Status line` off in `/config`;
`/sttp-mode`, `/sttp-guards` and `/workshop-questions` still answer at once.

`/workshop-forge` also opens a `Pipeline` pane: the pipeline it named, every iteration under its category, `✓` for DONE, `▶`
for CURRENT (between iterations, the NEXT one, with `· NEXT` after it, else the first PLANNED or BLOCKED one), `○` for
PLANNED, `⊘` for BLOCKED, and the iterations dropped, reverted,
split or left for later dimmed with their status. It follows the same turns and writes as the status line. A session
start or a plugin reload leaves it closed; `/workshop-forge-pane` opens it at any time, and closes it when it is open. In
fullscreen from 110 columns the terminal docks it beside the chat; otherwise it sits above the prompt. To keep it
closed, turn tars-mod's `Pipeline pane` off in `/config`; an open one closes, and `/workshop-forge-pane` says it is off.

What the hooks do:

- Session start, resume, clear, compact: inject the `sttp` and `sttp-software-engineering` rules. On compact, reset the coding once-per-session flag.
- Every prompt: one-line reminder to reload `sttp` if it fell out of context, which also says the grill questions go in the transcript while `/workshop-questions transcript` is set; handles `/sttp-mode`, `/sttp-guards`, `/workshop-questions`, `/tars-doctor`, `allow` (Codex) and the pause phrases.
- Before a shell command: the git guard above.
- `/workshop-craft`, `/workshop-forge` or `/workshop-glossary-bootstrap` (`$` in Codex) at the start of a prompt: marks the session. After a compaction of a marked session, one more line per skill tells the agent where its SKILL.md is, so a running workshop-craft continues from its scope's Current line, a running workshop-forge from its pipeline's, and a running workshop-glossary-bootstrap from its working file's. The line also gives that file's path and its Current line as they stand: the pipeline `/workshop-forge` named, or else the newest scope or `iterations.md` written since the skill started.
- `/workshop-forge` that names one pipeline (`/workshop-forge exports 2`, `/workshop-forge exports pdf`, or `/workshop-forge` alone when there is only one): adds that pipeline's Current section and its next unfinished iteration (its CURRENT row, else its NEXT one, else the first PLANNED or BLOCKED one, as the status line shows, with its line), so the agent starts from them, and notes the pipeline in `~/.tars/forge-<session>` for the mod. Nothing is added when the command could mean more than one pipeline.
- Before the first edit of a session (Edit, Write, MultiEdit, NotebookEdit, apply_patch): inject `sttp-software-coding` and `sttp-software-testing`.
- Subagent start: inject `sttp` and `sttp-software-engineering` in full mode only.
- The rules come in parts, one hook entry each, such as `sttp.py session-start 2`: Claude Code shows a hook's output
  over 10,000 characters as a 2 KB preview, with the rest saved to a file the agent may never read. Each part stays
  under it; the tests fail when a skill grows past it. Checked with Claude Code 2.1.295.
  After updating an install that points at a checkout, as `~/.claude/skills/tars` does, start a new session: an open
  session keeps the hook entries it started with but runs the new `sttp.py`, so a part with no entry of its own never
  arrives. After 0.3.0, such a session gets no engineering rules at its next compaction and no testing rules at its
  first edit.
- The first hook call of a session that Claude Code moved to the background, which gives it a new id: copies the
  notes kept under the old id (the pipeline `/workshop-forge` named, the marks of a running skill, the pause, guards off),
  so they follow the session. The old id comes from the "continued-in" line Claude Code writes at the end of the old
  transcript, which is not a documented format: if it changes, the notes reset at a move, as they did before.

## Layout

```
skills/sttp/SKILL.md            core skill
skills/sttp-software-engineering/SKILL.md  engineering conduct, injected with the core skill
skills/sttp-software-coding/SKILL.md  coding rules, injected before the first edit
skills/sttp-software-testing/SKILL.md  testing rules (test-first), injected with the coding rules
skills/workshop-grill/SKILL.md      the interview procedure; workshop-craft and workshop-forge load it
skills/workshop-craft/SKILL.md      /workshop-craft: defines a large task and writes its blueprint in .blueprints/
skills/workshop-craft/formats/      the blueprint's layout and file formats, and the TARS Blueprint Record's; workshop-forge reads them too
skills/workshop-forge/SKILL.md      /workshop-forge: builds one pipeline, one reviewed iteration per turn
skills/workshop-glossary/SKILL.md   the project's optional glossary and ADRs in docs/; workshop-craft and workshop-forge load it if present
skills/workshop-glossary-bootstrap/SKILL.md  /workshop-glossary-bootstrap: builds an existing project's glossary, area by area
skills/sttp-enforce/SKILL.md    /sttp-enforce: brings the files under a path to sttp's rules, after the user picks what to change
skills/sttp-mode/SKILL.md       the /sttp-mode command; the hook does the work
skills/sttp-guards/SKILL.md     the /sttp-guards command; the hook does the work
skills/workshop-questions/SKILL.md  the /workshop-questions command; the hook does the work
skills/tars-doctor/SKILL.md     /tars-doctor: checks that STTP works in the session and is back on course
skills/<name>/SKILL.md          one folder per skill, same format for both tools
.mcp.json                       MCP servers, same format for both tools
mcp/<name>/                     MCP server sources, if any are built here
hooks/hooks.json                the hook entries, all calling hooks/sttp.py; the rules come in parts (see Controls)
hooks/sttp.py                   the rules at session start and before the first edit, in parts; the prompt hook (reminder, pause, /sttp-mode, /sttp-guards, /workshop-questions, /tars-doctor, Codex's allow); the /workshop-craft, /workshop-forge and /workshop-glossary-bootstrap markers and the pipeline's state; the git guard; subagents; notes carried over when a session moves to the background (python3)
tests/test_sttp_hooks.py        tests of hooks/sttp.py in both tools: the git guard, its switch and its default, the pipeline's state, compaction, a session moved to the background, the rule parts, the doctor: python3 -m unittest tests.test_sttp_hooks
mods/tars-mod/                 the optional TARS mod, Claude Code only: answers /sttp-mode, /sttp-guards and /workshop-questions with no model turn, the status line and the pipeline pane with /workshop-forge-pane (each off in /config); tests: claude plugin test mods/tars-mod
evals/<case>/prompt.md          benchmark cases for `claude plugin eval`
evals/<case>/graders/*.md       regex and LLM graders for that case
.claude-plugin/                 Claude Code plugin + marketplace manifests
.codex-plugin/plugin.json       Codex plugin manifest
.agents/plugins/marketplace.json  Codex marketplace manifest
```

## Platforms

Checked for 0.7:

- Claude Code in the terminal: on Linux under WSL and on native Windows 11, in real sessions with Claude Code
  2.1.314; on Linux, Windows and macOS, by the hook and mod tests that CI runs on every push and pull request.
- The Claude desktop app: on native Windows 11, version 4.4212.0.0, with the mod's status line and pipeline pane.
- Codex CLI: on native Windows 11 with 0.166.0, and on Linux with 0.153.4.

The hooks need Python 3.9 or newer as `python3`. CI runs the hook tests on Python 3.9 and on the newest Python.

## Add a skill

Create `skills/<name>/SKILL.md`:

```markdown
---
name: <name>
description: What it does and when to use it. This line is how the agent decides to load it.
---

Instructions here.
```

Names: lowercase, digits, hyphens, under 64 chars. Folder name equals `name`.
Extra files (scripts, references) live next to `SKILL.md`.

## Add an MCP server

Add an entry to `.mcp.json`:

```json
{
  "mcpServers": {
    "example": { "type": "http", "url": "https://example.com/mcp" },
    "local": { "command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/local/index.js"] }
  }
}
```

Server source, if written here, goes in `mcp/<name>/`.

## Benchmark

`evals/` holds one case per question type from `skills/sttp/SKILL.md` (which, why,
how many, yes/no with a risk, wrong premise, multi-part, instance-not-concept) plus
`formal-email`, a control where an explicit form request must win over STTP, and two cases for its plain
terms: `rfc-open-comments` (labelled items named by their subject) and `mid-flow-decision` (decisions mid-way
through a plan with its own labels, in plain words).

```
claude plugin eval .
```

Runs each case 3 times with and without the plugin and reports the score delta.
Regex graders check the opening, filler phrases, and a word cap set at about twice
the length of an STTP answer on Opus 5; one LLM grader per case checks answer-first
order. The default judge is haiku; `--judge-model sonnet` is stricter on wording and
less noisy. Results land in `evals/results/` (ignored by
git). Useful flags: `--case <glob>`, `--runs <n>`, `--model <model>`,
`--judge-model <model>`, `--no-publish`.

`evals/<skill>/` folders without a `prompt.md` hold the skill-creator tests of one skill: prompts,
fixtures and grading scripts. Their results live outside the repo. A `test_grade.py` next to a grading script checks
the script itself, with no model: `python3 -m unittest discover -s evals/<skill>`.

Grader format: frontmatter `type: regex` with `pattern`, optional `flags`
(JS RegExp), `match: contains | not_contains | count:N`, `weight`; or
`type: llm` with the rubric as the body. A run passes only if every grader
passes; the case score is the mean over runs.

## Contributing

Issues and pull requests are welcome, one change per pull request, so each can be reviewed on its own. Before you
open one, run the checks that cover your change:

```
python3 -m unittest tests.test_sttp_hooks   # the hooks
claude plugin test mods/tars-mod            # the mod
claude plugin validate .                    # the plugin's manifests
claude plugin validate mods/tars-mod        # the mod's manifest
```

CI runs the hook and mod tests on Linux, Windows and macOS for every pull request. A change to a skill's wording is
checked with the evals: `claude plugin eval .` for the sttp cases, and the skill-creator tests in `evals/<skill>/` for
the skills that have them (see Benchmark).

## Credits

`sttp-software-testing` adapts Matt Pocock's `tdd` and `codebase-design` skills
([mattpocock/skills](https://github.com/mattpocock/skills), MIT). The license notice is in
`skills/sttp-software-testing/NOTICE.md`.

`workshop-grill` adapts Matt Pocock's `grilling` skill (same repository, MIT). The license notice is in
`skills/workshop-grill/NOTICE.md`.

`workshop-glossary` is after Matt Pocock's `domain-modeling` skill (same repository, MIT): the glossary with
words to avoid, and ADRs offered only for decisions that are hard to reverse, surprising and a real trade-off.

`workshop-glossary-bootstrap` takes its shape from Taylor Lilley's description of `canon-init` in
[mattpocock/skills#930](https://github.com/mattpocock/skills/issues/930): mine the sources, draft, ask only about
the conflicts, publish. No text is adapted.

Three lines of the Write list in `sttp-software-coding` take their checks from Claude Code's bundled `simplify`
skill: no wasted work, no state that can be derived, copy-paste made into one function, deep nesting turned into
early returns, and no long-lived closure that keeps large values alive. No text is adapted.
