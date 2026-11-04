#!/usr/bin/env python3
"""TARS hooks. Usage: sttp.py session-start|prompt|pre-edit|pre-bash|subagent-start [part] (stdin: hook JSON)."""
import glob, json, os, re, shutil, sys, tempfile, time

EVENTS = {"session-start": "SessionStart", "prompt": "UserPromptSubmit", "pre-edit": "PreToolUse",
          "pre-bash": "PreToolUse", "subagent-start": "SubagentStart"}
# Shared with the mod, which knows the environment, not flag_dir: HOME when set, else the user's profile folder, as
# the mod finds it. Python on Windows reads only USERPROFILE for "~", and a Windows terminal sets no HOME.
STATE_DIR = os.path.join(os.environ.get("HOME") or os.path.expanduser("~"), ".tars")
MODE_FILE = os.path.join(STATE_DIR, "mode")
GUARDS_DEFAULT = os.path.join(STATE_DIR, "guards-default")
QUESTIONS_FILE = os.path.join(STATE_DIR, "questions")
# The per-session notes in STATE_DIR, deleted at a session start once untouched this long; the settings files stay.
SESSION_NOTES = ("paused-", "guards-off-", "forge-")
NOTES_KEPT_FOR = 30 * 24 * 3600
# Claude Code shows a hook's output over this many characters as a 2 KB preview, the rest saved to a file. Longer text
# goes in parts, one per hooks.json command of the event: `sttp.py session-start 2` prints the second.
LIMIT = 10_000
REMINDER = "STTP active. If the STTP rules are not in your context, load the sttp skill before answering."
IN_TRANSCRIPT = " Grill questions: in the transcript, not the question dialog (/workshop-questions transcript)."
RESUME_FROM = {"workshop-craft": "the task's 02-scope.md", "workshop-forge": "the pipeline's iterations.md",
               "workshop-glossary-bootstrap": "its working file, .blueprints/glossary-bootstrap/bootstrap.md"}
# Where each skill's blueprint file sits under .blueprints/, for the one written since the skill started.
WORKING_FILE = {"workshop-craft": "*/02-scope.md", "workshop-forge": "*/pipelines/*/iterations.md",
                "workshop-glossary-bootstrap": "glossary-bootstrap/bootstrap.md"}
# A background task or another session reporting back also fires UserPromptSubmit; it is not the user's message.
NOTICE = re.compile(r"<task-notification>|<agent-message\b|\[SYSTEM NOTIFICATION")
GIT_STEP = re.compile(r"\bgit((?:\s+(?:-[Cc]\s+\S+|--?[\w-]+(?:=\S+)?))*)\s+(add|commit|push|tag|stash|reset|restore)\b"
                      r"([^;&|\n]*)")
FORGE_ARGS = re.compile(r"^[/$](?:tars:)?workshop-forge(?=\s|$)(?:\s+([^\s,;]+))?(?:\s+([^\s,;]+))?", re.I)
# A status table row of an iteration not finished: | Category | # | Title | Status |
UNFINISHED = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|[^|]*\|\s*(PLANNED|CURRENT|NEXT|BLOCKED)\s*\|\s*$", re.M)
# The words in the user's latest message that ask for each step (Codex, which cannot ask from a hook).
GIT_WORDS = {"add": r"\b(?:stag|add)\w*", "commit": r"\bcommit\w*", "push": r"\bpush\w*", "tag": r"\btag\w*",
             "stash": r"\bstash\w*", "reset": r"\b(?:reset|unstag)\w*", "restore --staged": r"\b(?:unstag|restor)\w*"}


def main(event, part=1):
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ.get("PLUGIN_ROOT") \
        or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sid = data.get("session_id", "")
    agent = data.get("agent_id", "")
    flag_dir = data.get("scratchpad_dir") or os.environ.get("CLAUDE_PLUGIN_DATA") \
        or os.environ.get("PLUGIN_DATA") or tempfile.gettempdir()
    carry_over(sid, flag_dir, data.get("transcript_path") or "")
    if event == "session-start":
        drop_old_notes()
    pause_flag = os.path.join(STATE_DIR, f"paused-{sid}")  # the mod's status line reads it
    coding_flag = os.path.join(flag_dir, f"sttp-coding-{sid}" + (f"-{agent}" if agent else ""))
    part_flag = coding_flag + (f".{part}" if part > 1 else "")  # each part's own: the parts run at the same time
    allow_flag = os.path.join(flag_dir, f"sttp-allow-{sid}")
    guards_file = os.path.join(STATE_DIR, f"guards-off-{sid}")
    guards_switch = read(guards_file).strip()
    guards_default = "off" if read(GUARDS_DEFAULT).strip() == "off" else "on"
    guards_off = (guards_switch if guards_switch in ("on", "off") else guards_default) == "off"
    guards_state = (f"{guards_switch} for this session; the default is {guards_default}."
                    if guards_switch in ("on", "off") else f"{guards_default}, the default.")
    last_prompt = os.path.join(flag_dir, f"sttp-last-prompt-{sid}")
    mode = read_mode()
    questions = "transcript" if read(QUESTIONS_FILE).strip().lower() == "transcript" else "dialog"
    reminder = REMINDER + (IN_TRANSCRIPT if questions == "transcript" else "")

    def skill(name):
        with open(os.path.join(root, "skills", name, "SKILL.md"), encoding="utf-8") as f:
            return re.sub(r"\A---\n.*?\n---\n", "", f.read(), flags=re.S)

    def core():
        return ["STTP active:\n" + skill("sttp"), "STTP engineering active:\n" + skill("sttp-software-engineering")]

    def emit(*blocks):
        """Prints this call's part of the blocks, packed in order into parts of at most LIMIT characters."""
        parts = [[]]
        for block in blocks:
            if parts[-1] and len("\n".join(parts[-1] + [block])) > LIMIT:
                parts.append([])
            parts[-1].append(block)
        if part <= len(parts):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": EVENTS[event],
                                                     "additionalContext": "\n".join(parts[part - 1])}}))

    paused = os.path.exists(pause_flag)

    if event == "prompt":
        prompt = (data.get("prompt") or "").strip()
        m = re.match(r"^[/$](?:tars:)?(workshop-craft|workshop-forge|workshop-glossary-bootstrap)(?:\s|$)",
                     prompt, re.I)
        cwd = data.get("cwd") or os.getcwd()
        pipeline = forge_pipeline(prompt, cwd) if not agent else ""
        if m:
            write(os.path.join(flag_dir, f"{m.group(1).lower()}-{sid}"), os.path.abspath(pipeline) if pipeline else "")
            if m.group(1).lower() == "workshop-forge":  # the mod reads it
                write(os.path.join(STATE_DIR, f"forge-{sid}"), os.path.abspath(pipeline) if pipeline else "")
        state = "" if paused or not pipeline else forge_state(pipeline, cwd)
        if "turn_id" in data and not agent and not NOTICE.search(prompt[:400]):  # Codex: the git guard reads it
            write(last_prompt, prompt)
            if re.match(r"^allow[.!]?$", prompt, re.I):
                touch(allow_flag)
                return emit("TARS: a git step the guard denied can go through until the user's next message."
                            + ("" if paused else " " + reminder))
            remove(allow_flag)
        m = re.match(r"^[/$@](?:tars:)?sttp-guards(?:\s+(.*?))?\s*$", prompt, re.I)
        if m:
            arg = " ".join((m.group(1) or "").lower().split())
            if arg in ("off", "on"):
                write(guards_file, arg + "\n")
            if arg in ("default off", "default on"):
                write(GUARDS_DEFAULT, arg.split()[1] + "\n")
            if arg == "off":
                return emit("TARS guards off for this session: git steps are not checked. "
                            "/sttp-guards on turns them back on.")
            if arg == "on":
                return emit("TARS guards on.")
            if arg == "default off":
                return emit("TARS guards default: off. Sessions without their own /sttp-guards on|off, open ones too, "
                            "don't check git steps. /sttp-guards default on turns it back on.")
            if arg == "default on":
                return emit("TARS guards default: on.")
            if arg == "default":
                return emit(f"TARS guards default: {guards_default}.")
            if arg:
                return emit(f"Unknown argument '{arg}'. Use /sttp-guards on|off or /sttp-guards default on|off.")
            return emit("TARS guards: " + guards_state)
        m = re.match(r"^[/$@](?:tars:)?sttp-mode(?:\s+(\S+))?\s*$", prompt, re.I)
        if m:
            arg = (m.group(1) or "").lower()
            if arg in ("primary", "full"):
                write_mode(arg)
                return emit(f"STTP mode set to {arg}.")
            if arg:
                return emit(f"Unknown STTP mode '{arg}'. Use primary or full.")
            return emit(f"STTP mode: {mode}.")
        m = re.match(r"^[/$@](?:tars:)?workshop-questions(?:\s+(\S+))?\s*$", prompt, re.I)
        if m:
            arg = (m.group(1) or "").lower()
            if arg in ("dialog", "transcript"):
                write(QUESTIONS_FILE, arg + "\n")
                return emit(f"Grill questions set to {arg}.")
            if arg:
                return emit(f"Unknown question form '{arg}'. Use dialog or transcript.")
            return emit(f"Grill questions: {questions}.")
        if re.match(r"^[/$@](?:tars:)?tars-doctor(?=\s|$)", prompt, re.I):  # answered while paused too
            real = os.path.realpath(root)  # a linked install shows the checkout it links to
            notes = [f"TARS {version(real, 'turn_id' in data)}, from {real}."]
            if paused:
                notes.append('STTP is paused for this session ("stop sttp"): its rules and the git guard are off on '
                             'purpose until "start sttp".')
            else:
                coding = ("sent at the first edit since the session's start or its last compaction."
                          if os.path.exists(coding_flag) else "not sent since the session's start or its last "
                          "compaction: they come back at the next edit.")
                notes += [f"STTP on, mode {mode}.",
                          "Rules the hooks add: sttp and sttp-software-engineering, at the session's start and after "
                          f"each compaction; sttp-software-coding and sttp-software-testing, {coding}",
                          "The git guard: " + guards_state,
                          f"Grill questions: {questions}."]
            notes.append("The pipeline /workshop-forge named: "
                         + (read(os.path.join(STATE_DIR, f"forge-{sid}")).strip() or "none") + ".")
            if read(os.path.join(flag_dir, f"sttp-carried-{sid}")).strip() == "untraced":
                notes.append("This session goes on from a conversation TARS could not trace: Claude Code left no line "
                             "naming the session it came from. If it was moved to the background or copied, the notes "
                             "it had there did not come along: the STTP pause, the git guard switch and the pipeline "
                             "/workshop-forge named start over here.")
            notes += [f"Started in this session: {name}, its file {path or 'not written yet'}."
                      + (f" Its Current line now:\n{now}" if now else "") for name, _, path, now in started(
                          flag_dir, sid, cwd)]
            notes.append(f"Skill files: {os.path.join(real, 'skills', '<name>', 'SKILL.md')}.")
            return emit("TARS doctor, the hooks' notes for this session:\n" + "\n".join(f"- {n}" for n in notes))
        if re.match(r"^(stop sttp|normal mode)[.!]?$", prompt, re.I):
            touch(pause_flag)
            return emit("STTP paused for this session. Say start sttp to resume.")
        if re.match(r"^start sttp[.!]?$", prompt, re.I):
            remove(pause_flag)
            return emit("STTP resumed. If the STTP rules are not in your context, load the sttp skill.")
        if not paused:
            emit(state + reminder)
        return

    if paused:
        return

    if event == "session-start":
        blocks = core()
        if data.get("source") == "compact":
            for f in glob.glob(os.path.join(flag_dir, f"sttp-coding-{sid}*")):
                remove(f)
            for name, where, path, now in started(flag_dir, sid, data.get("cwd") or os.getcwd()):
                blocks.append(f"{name} was started in this session. If it is still running and its instructions are"
                              f" not in your context, read {os.path.join(root, 'skills', name, 'SKILL.md')} and"
                              f" continue from the Current line of {where}."
                              + (f" Its file: {path}." + (f" Its Current line now:\n{now}\n" if now else "")
                                 if path else ""))
        return emit(*blocks)

    if event == "subagent-start":
        if mode == "full":
            emit(*core())
        return

    if event == "pre-bash":
        steps = [] if agent or guards_off else git_steps((data.get("tool_input") or {}).get("command"))
        if not steps:
            return
        if "turn_id" not in data:  # Claude Code: its own approval prompt; only Codex sends a turn_id
            return decide("ask", f"TARS guard: {named(steps)} changes the user's git state, and the user runs git "
                                 "steps themselves unless they ask for one.")
        said = read(last_prompt)
        missing = [s for s in steps if not re.search(GIT_WORDS[s], said, re.I)]
        if missing and not os.path.exists(allow_flag):
            return decide("deny", f"TARS guard: the user runs git steps themselves, and their latest message does not "
                                  f'ask for {named(missing)}. The user can ask for the step by name, or reply "allow" '
                                  "to let it through.")
        return

    if event == "pre-edit":
        if agent and mode != "full":
            return
        if os.path.exists(part_flag):
            return
        emit("STTP coding active:\n" + skill("sttp-software-coding"),
             "STTP testing active:\n" + skill("sttp-software-testing"))
        touch(part_flag)


def carry_over(sid, flag_dir, transcript):
    """A session moved to the background goes on under a new id: on its first hook call, copy the notes filed under
    the old id (the pipeline, the skill flags, the pause, guards off), once. The parts of one event run at the same
    time, so each copies until the copy is done, and a note is replaced whole, never seen half written. A session
    that goes on from a conversation no move line names gets "untraced" in its marker, for /tars-doctor."""
    marker = os.path.join(flag_dir, f"sttp-carried-{sid}")
    if not sid or not transcript or os.path.exists(marker):
        return
    old = continued_from(sid, transcript)
    old_flag_dir = os.sep.join(old if part == sid else part for part in flag_dir.split(os.sep))  # its own folder only
    for new_dir, old_dir in ((flag_dir, old_flag_dir), (STATE_DIR, STATE_DIR)) if old else ():
        for f in glob.glob(os.path.join(glob.escape(old_dir), f"*-{glob.escape(old)}*")):
            if os.path.basename(f).startswith("sttp-carried-"):
                continue  # the old session's own marker would mark this copy done before it is
            new = os.path.join(new_dir, os.path.basename(f).replace(old, sid))
            try:
                os.makedirs(new_dir, exist_ok=True)
                shutil.copy2(f, f"{new}.{os.getpid()}.tmp")  # keeps the time
                os.replace(f"{new}.{os.getpid()}.tmp", new)
            except OSError:
                pass  # sttp: a note not copied leaves the session as it was before this copy
    write(marker, "" if old or not goes_on(transcript) else "untraced\n")


def goes_on(transcript):
    """Whether the transcript already holds an answer at the session's first hook call: a move or a copy starts its
    transcript with the conversation it goes on from (Claude Code 2.1.295), and a new session has none yet. A session
    resumed under its own id after its marker was lost, such as a scratchpad cleared from /tmp, has one too."""
    try:
        with open(transcript, encoding="utf-8", errors="replace") as f:
            return any(json.loads(line).get("type") == "assistant" for line in f if '"assistant"' in line)
    except (OSError, ValueError, AttributeError):
        return False


def drop_old_notes():
    for f in glob.glob(os.path.join(glob.escape(STATE_DIR), "*")):
        try:
            if os.path.basename(f).startswith(SESSION_NOTES) and time.time() - os.path.getmtime(f) > NOTES_KEPT_FOR:
                os.remove(f)
        except OSError:
            pass  # sttp: the parts of one event run at the same time, and another may have deleted it first


def started(flag_dir, sid, cwd):
    """The skills started in this session, each with its working file and that file's Current line as it stands."""
    for name, where in RESUME_FROM.items():
        flag = os.path.join(flag_dir, f"{name}-{sid}")
        if os.path.exists(flag):
            path = working_file(name, flag, cwd)
            yield name, where, path, current(read(path)).strip() if path else ""


def version(root, codex):
    """The plugin's version, from the manifest of the tool running it."""
    for folder in (".codex-plugin", ".claude-plugin") if codex else (".claude-plugin", ".codex-plugin"):
        try:
            return json.loads(read(os.path.join(root, folder, "plugin.json")))["version"]
        except (ValueError, KeyError):
            continue
    return "of unknown version"


def continued_from(sid, transcript):
    """The session this one continues: Claude Code ends the old transcript, next to this one, with a line
    {"type":"continued-in",...,"continuedInSessionId":"<this id>"} followed by a few short ones (about 1 KB: the last
    prompt among them is cut to 200 characters), so the last 64 KB of each transcript holds it."""
    needle = f'"continuedInSessionId":"{sid}"'
    files = [f for f in glob.glob(os.path.join(glob.escape(os.path.dirname(transcript)), "*.jsonl"))
             if os.path.basename(f) != os.path.basename(transcript)]
    for f in sorted(files, key=mtime, reverse=True)[:20]:
        try:
            with open(f, "rb") as fh:
                fh.seek(max(0, os.path.getsize(f) - 64_000))
                tail = fh.read().decode("utf-8", "replace")
        except OSError:
            continue
        if any(line.startswith('{"type":"continued-in"') and needle in line for line in tail.splitlines()):
            return os.path.splitext(os.path.basename(f))[0]
    return ""


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}))


def git_steps(command):
    """The git steps in a shell command that change what is staged, committed, pushed, tagged or stashed."""
    steps = []
    for m in GIT_STEP.finditer(command or ""):
        step, rest = m.group(2), m.group(3).split()
        if step == "restore" and not {"--staged", "-S"} & set(rest):
            continue
        if step == "tag" and (not rest or rest[0] in ("-l", "--list", "-n")):
            continue
        if step == "stash" and rest and rest[0] in ("list", "show"):
            continue
        steps.append("restore --staged" if step == "restore" else step)
    return list(dict.fromkeys(steps))


def named(steps):
    return " and ".join(f"`git {s}`" for s in steps)


def forge_pipeline(prompt, cwd):
    """The iterations.md of the pipeline /workshop-forge names, or "" when the command could mean none or several."""
    m = FORGE_ARGS.match(prompt)
    if not m:
        return ""
    task, pipeline = m.groups()
    root = blueprints_dir(cwd)
    if task and os.path.isdir(os.path.join(cwd, task, "pipelines")):  # a blueprint's path, relative or absolute
        tasks = [os.path.join(cwd, task)]
    else:
        tasks = [] if not root else [os.path.join(root, task)] if task else glob.glob(os.path.join(root, "*"))
    files = [f for t in tasks for f in glob.glob(os.path.join(t, "pipelines", "*", "iterations.md"))
             if not pipeline or names_pipeline(os.path.basename(os.path.dirname(f)), pipeline)]
    return files[0] if len(files) == 1 else ""


def forge_state(path, cwd):
    """The pipeline's Current section and its next unfinished iteration, for the agent starting workshop-forge."""
    text = read(path)
    state = (f"workshop-forge's pipeline, from {os.path.relpath(path, cwd)}:\n\n## Current\n\n"
             + current(text).strip() + "\n")
    rows = list(UNFINISHED.finditer(text))  # CURRENT, else NEXT, else the first open one, as the mod's status line
    row = next((r for s in ("CURRENT", "NEXT") for r in rows if r.group(3) == s), rows[0] if rows else None)
    line = iteration_line(text, row.group(1), row.group(2)) if row else ""
    if line:
        state += f"\nIts next unfinished iteration, {row.group(1)}, iteration {row.group(2)}, {row.group(3)}:\n{line}\n"
    return state + "\n"


def iteration_line(text, category, number):
    """An iteration's line under its category's heading, with its continuation lines."""
    lines, inside = [], not re.search(r"^### ", text, re.M)  # a pipeline without categories lists them directly
    for line in text.splitlines():
        if line.startswith("### "):
            inside = line[4:].strip() == category
        elif lines and line.startswith("  "):
            lines.append(line)
        elif lines:
            break
        elif inside and re.match(rf"- Iteration {re.escape(number)}(?!\.?\d)", line):
            lines.append(line)
    return "\n".join(lines)


def names_pipeline(folder, name):
    """Whether `2`, `pdf-downloads` or `02-pdf-downloads` names the pipeline folder `02-pdf-downloads`."""
    number, _, rest = folder.lower().partition("-")
    name = name.lower()
    return name in (folder.lower(), rest) or name.isdigit() and number.isdigit() and int(name) == int(number)


def blueprints_dir(cwd):
    d = os.path.abspath(cwd)
    while True:
        if os.path.isdir(os.path.join(d, ".blueprints")):
            return os.path.join(d, ".blueprints")
        if os.path.dirname(d) == d:
            return ""
        d = os.path.dirname(d)


def working_file(name, flag, cwd):
    """The blueprint file a skill started in this session works in: the pipeline /workshop-forge named, else the
    newest of its kind written since the skill started; workshop-glossary-bootstrap's one working file at any age."""
    named = read(flag).strip()
    if named and os.path.isfile(named):
        return named
    root = blueprints_dir(cwd)
    since = 0 if name == "workshop-glossary-bootstrap" else mtime(flag)
    files = [f for f in glob.glob(os.path.join(root, WORKING_FILE[name])) if mtime(f) >= since] if root else []
    return max(files, key=mtime, default="")


def current(text):
    """The Current section of an iterations.md, or the `Current:` paragraph of a scope or a working file."""
    m = (re.search(r"^## Current\n(.*?)(?=^## |\Z)", text, re.M | re.S)
         or re.search(r"^(Current:.*?)(?=\n\s*\n|\Z)", text, re.M | re.S))
    return m.group(1) if m else ""


def mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def read_mode():
    try:
        with open(MODE_FILE) as f:
            m = f.read().strip().lower()
        return m if m in ("primary", "full") else "primary"
    except OSError:
        return "primary"


def write_mode(mode):
    os.makedirs(os.path.dirname(MODE_FILE), exist_ok=True)
    with open(MODE_FILE, "w") as f:
        f.write(mode + "\n")


def write(path, text):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        pass  # sttp: a lost latest message only makes the Codex git guard stricter; a lost switch leaves it on


def touch(path):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").close()
    except OSError:
        pass  # sttp: no flag means the hook fires again next time, harmless


def remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


if __name__ == "__main__":
    ev = sys.argv[1] if len(sys.argv) > 1 else ""
    if ev not in EVENTS or len(sys.argv) > 2 and not sys.argv[2].isdigit():
        sys.stderr.write(f"sttp.py: unknown event '{' '.join(sys.argv[1:])}'\n")
        sys.exit(1)
    try:
        main(ev, int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    except Exception as e:  # never block the user on a hook bug
        sys.stderr.write(f"sttp.py {ev}: {e}\n")
        sys.exit(1)
