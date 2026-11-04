"""The git guard and the blueprint state lines in hooks/sttp.py, run as Claude Code and Codex run it: the hook JSON on stdin, the answer on stdout."""
import json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "sttp.py"
PIPELINE = """# Pipeline 1: csv

Goal: finance downloads its reports as CSV.

## Current

CSV, iteration 2.1: done and reported; waiting on the user's "continue" for iteration 2.2.

## Status

| Category | #   | Title           | Status  |
|----------|-----|-----------------|---------|
| Setup    | 1.1 | export route    | DONE    |
| CSV      | 2.1 | header row      | DONE    |
| CSV      | 2.2 | totals          | PLANNED |
| CSV      | 2.3 | download button | PLANNED |

## Iterations

### Setup
- Iteration 1.1: the export route (`reports/urls.py`).

### CSV
- Iteration 2.1: the header row (`reports/csv.py`).
- Iteration 2.2: totals at the bottom of each
  file, in the user's currency.
- Iteration 2.3: a download button.
"""
SCOPE = "# Scope: exports\n\nCurrent: the split, waiting on the user's answer to Q4.\n\n## Task\nCSV downloads.\n"
BOOTSTRAP = "# Glossary bootstrap\n\nCurrent: Billing, group 2: waiting on the user's picks.\n\n## Areas\n- Billing\n"
CSV = ".blueprints/exports/pipelines/01-csv/iterations.md"
# The arguments of every hooks.json command, by event: the hook's output can come in several parts.
COMMANDS = {}
for _groups in json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"].values():
    for _hook in (h for g in _groups for h in g["hooks"]):
        _args = _hook["command"].split('sttp.py" ', 1)[1].split()
        COMMANDS.setdefault(_args[0], []).append(_args)


class Session:
    """One session's hook calls, in a throwaway project."""

    def __init__(self, tmp, codex=False):
        self.flags = tmp / "flags"
        self.project = tmp / "project"
        self.home = tmp / "home"
        self.codex = codex
        for d in (self.flags, self.project, self.home):
            d.mkdir(parents=True)

    def run(self, event, root=ROOT, **data):
        """Every command hooks.json gives the event, as Claude Code runs them: their texts joined, each in parts."""
        env = {**os.environ, "HOME": str(self.home), "CLAUDE_PLUGIN_ROOT": str(root)}
        if self.codex:  # Codex sends a turn_id and no scratchpad_dir; plugin hooks get the plugin's data folder
            data = {"session_id": "s1", "turn_id": "t1", "cwd": str(self.project), **data}
            env.update(PLUGIN_DATA=str(self.flags), CLAUDE_PLUGIN_DATA=str(self.flags))
        else:
            data = {"session_id": "s1", "scratchpad_dir": str(self.flags), "cwd": str(self.project), **data}
        self.parts = []
        for args in COMMANDS[event]:
            out = subprocess.run([sys.executable, str(HOOK), *args], input=json.dumps(data), capture_output=True,
                                 text=True, env=env, check=True).stdout
            self.parts.append(json.loads(out) if out.strip() else {})
        time.sleep(0.02)  # keeps every flag and file written later strictly newer
        texts = [context(p) for p in self.parts if context(p)]
        if len(texts) < 2:
            return next((p for p in self.parts if p), {})
        return {"hookSpecificOutput": {"additionalContext": "\n".join(texts)}}

    def prompt(self, text, **data):
        return self.run("prompt", prompt=text, **data)

    def write(self, rel, text):
        path = self.project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        time.sleep(0.02)

    def bash(self, command, **data):
        return self.run("pre-bash", tool_name="Bash", tool_input={"command": command}, **data)


def refusal(out):
    h = out.get("hookSpecificOutput", {})
    return h.get("permissionDecisionReason", "") if h.get("permissionDecision") == "deny" else ""


def question(out):
    h = out.get("hookSpecificOutput", {})
    return h.get("permissionDecisionReason", "") if h.get("permissionDecision") == "ask" else ""


def context(out):
    return out.get("hookSpecificOutput", {}).get("additionalContext", "")


class Base(unittest.TestCase):
    codex = False

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.s = Session(Path(self.tmp.name), codex=self.codex)

    def tearDown(self):
        self.tmp.cleanup()


class GitGuard(Base):
    def test_a_commit_asks_first(self):
        self.assertIn("git commit", question(self.s.bash('git commit -m "Fix the header"')))

    def test_reading_git_goes_through(self):
        self.assertEqual(self.s.bash("git status --short && git diff && git log -3"), {})

    def test_options_before_the_step_are_seen(self):
        self.assertIn("git add", question(self.s.bash("git -C /repo add -A")))

    def test_listing_tags_and_stashes_goes_through(self):
        for command in ("git tag", "git tag -l", "git stash list"):
            self.assertEqual(self.s.bash(command), {}, command)
        self.assertIn("git tag", question(self.s.bash("git tag v1.0")))
        self.assertIn("git stash", question(self.s.bash("git stash")))

    def test_restore_asks_only_when_it_unstages(self):
        self.assertIn("git restore --staged", question(self.s.bash("git restore --staged README.md")))
        self.assertEqual(self.s.bash("git restore reports/views.py"), {})

    def test_a_named_step_still_asks_in_claude_code(self):
        self.s.prompt("commit this")
        self.assertIn("git commit", question(self.s.bash("git commit -m x")))

    def test_a_subagent_git_step_goes_through(self):
        self.assertEqual(self.s.bash("git commit -m x", agent_id="a1"), {})

    def test_allow_is_an_ordinary_message_in_claude_code(self):
        self.assertTrue(context(self.s.prompt("allow")).startswith("STTP active."))
        self.assertIn("git push", question(self.s.bash("git push")))


class CodexGitGuard(Base):
    codex = True

    def test_an_unnamed_step_is_refused(self):
        self.s.prompt("fix the header row")
        reason = refusal(self.s.bash("git commit -m x"))
        self.assertIn("git commit", reason)
        self.assertIn('"allow"', reason)

    def test_only_the_named_step_goes_through(self):
        self.s.prompt("commit this")
        self.assertEqual(self.s.bash("git commit -m x"), {})
        self.assertIn("git push", refusal(self.s.bash("git push")))

    def test_commit_and_push_lets_both_through(self):
        self.s.prompt("commit and push it")
        self.assertEqual(self.s.bash("git commit -m x && git push"), {})

    def test_stage_names_git_add_and_unstage_names_restore(self):
        self.s.prompt("stage the fix and unstage the README")
        self.assertEqual(self.s.bash("git add reports/views.py && git restore --staged README.md"), {})

    def test_allow_lets_a_refused_step_through(self):
        self.s.prompt("fix the header row")
        self.s.prompt("allow")
        self.assertEqual(self.s.bash("git push"), {})

    def test_a_report_back_is_not_the_latest_message(self):
        self.s.prompt("commit this")
        self.s.prompt('<agent-message from="a1">\nDone. Should I push?\n</agent-message>')
        self.assertIn("git push", refusal(self.s.bash("git push")))


class GuardsSwitch(Base):
    def test_off_turns_the_git_guard_off_and_on_turns_it_back(self):
        self.assertIn("guards off", context(self.s.prompt("/sttp-guards off")))
        self.assertEqual(self.s.bash("git commit -m x"), {})
        self.assertIn("guards on", context(self.s.prompt("/tars:sttp-guards on")))
        self.assertIn("git commit", question(self.s.bash("git commit -m x")))

    def test_the_switch_the_mod_wrote_is_read(self):
        marker = self.s.home / ".tars" / "guards-off-s1"
        marker.parent.mkdir()
        marker.write_text("off\n")
        self.assertEqual(self.s.bash("git commit -m x"), {})
        self.assertIn("guards: off", context(self.s.prompt("/sttp-guards")))
        marker.write_text("on\n")
        self.assertIn("git commit", question(self.s.bash("git commit -m x")))

    def test_no_argument_tells_the_state(self):
        self.assertIn("guards: on", context(self.s.prompt("/sttp-guards")))
        self.s.prompt("/sttp-guards off")
        self.assertIn("guards: off", context(self.s.prompt("/sttp-guards")))


class GuardsDefault(Base):
    """/sttp-guards default off|on: the git guard in every session without its own /sttp-guards on|off."""

    def test_default_off_reaches_new_and_open_sessions(self):
        self.s.prompt("hello", session_id="s2")
        self.assertIn("guards default: off", context(self.s.prompt("/sttp-guards default off")))
        self.assertEqual(self.s.bash("git commit -m x"), {})
        self.assertEqual(self.s.bash("git push", session_id="s2"), {})
        self.assertEqual(self.s.bash("git tag v1.0", session_id="s3"), {})

    def test_a_sessions_own_switch_wins_over_the_default(self):
        self.s.prompt("/sttp-guards default off")
        self.s.prompt("/sttp-guards on")
        self.assertIn("git commit", question(self.s.bash("git commit -m x")))
        self.assertEqual(self.s.bash("git commit -m x", session_id="s2"), {})

    def test_default_on_turns_it_back_on(self):
        self.s.prompt("/sttp-guards default off")
        self.assertIn("guards default: on", context(self.s.prompt("/tars:sttp-guards default on")))
        self.assertIn("git commit", question(self.s.bash("git commit -m x")))

    def test_the_default_the_mod_wrote_is_read(self):
        default = self.s.home / ".tars" / "guards-default"
        default.parent.mkdir()
        default.write_text("off\n")
        self.assertEqual(self.s.bash("git commit -m x"), {})
        default.write_text("maybe\n")
        self.assertIn("git commit", question(self.s.bash("git commit -m x")))

    def test_no_argument_tells_the_session_and_the_default(self):
        self.assertIn("guards: on, the default.", context(self.s.prompt("/sttp-guards")))
        self.s.prompt("/sttp-guards default off")
        self.assertIn("guards: off, the default.", context(self.s.prompt("/sttp-guards")))
        self.s.prompt("/sttp-guards on")
        self.assertIn("guards: on for this session; the default is off.", context(self.s.prompt("/sttp-guards")))
        self.assertIn("guards default: off.", context(self.s.prompt("/sttp-guards default")))

    def test_an_unknown_default_changes_nothing(self):
        self.assertIn("Unknown argument 'default maybe'", context(self.s.prompt("/sttp-guards default maybe")))
        self.assertFalse((self.s.home / ".tars" / "guards-default").exists())


class CodexGuardsSwitch(Base):
    codex = True

    def test_dollar_form_turns_the_git_guard_off(self):
        self.s.prompt("$sttp-guards off")
        self.assertEqual(self.s.bash("git push"), {})

    def test_dollar_form_sets_the_default(self):
        self.s.prompt("$sttp-guards default off")
        self.s.prompt("fix the header row")
        self.assertEqual(self.s.bash("git push"), {})


class QuestionForm(Base):
    """/workshop-questions dialog|transcript: how workshop-grill asks, told to the model in the reminder line."""

    def test_transcript_is_kept_and_shown(self):
        self.assertIn("Grill questions set to transcript.", context(self.s.prompt("/workshop-questions transcript")))
        self.assertEqual((self.s.home / ".tars" / "questions").read_text(), "transcript\n")
        self.assertIn("Grill questions: transcript.", context(self.s.prompt("/tars:workshop-questions")))
        self.assertIn("Grill questions set to dialog.", context(self.s.prompt("/workshop-questions dialog")))
        self.assertIn("Grill questions: dialog.", context(self.s.prompt("/workshop-questions")))

    def test_no_form_or_an_unknown_one_means_dialog(self):
        self.assertIn("Grill questions: dialog.", context(self.s.prompt("/workshop-questions")))
        form = self.s.home / ".tars" / "questions"
        form.parent.mkdir()
        form.write_text("panel\n")
        self.assertIn("Grill questions: dialog.", context(self.s.prompt("/workshop-questions")))

    def test_an_unknown_argument_changes_nothing(self):
        self.assertIn("Unknown question form 'panel'", context(self.s.prompt("/workshop-questions panel")))
        self.assertFalse((self.s.home / ".tars" / "questions").exists())

    def test_the_reminder_says_transcript_while_it_is_set_in_every_session(self):
        self.assertNotIn("in the transcript", context(self.s.prompt("hello")))
        self.s.prompt("hello", session_id="s2")
        self.s.prompt("/workshop-questions transcript")
        self.assertIn("Grill questions: in the transcript", context(self.s.prompt("hello")))
        self.assertIn("Grill questions: in the transcript", context(self.s.prompt("hello", session_id="s2")))
        self.s.prompt("/workshop-questions dialog")
        self.assertNotIn("in the transcript", context(self.s.prompt("hello")))


class CodexQuestionForm(Base):
    codex = True

    def test_dollar_form_sets_it_and_the_reminder_follows(self):
        self.s.prompt("$workshop-questions transcript")
        self.assertIn("Grill questions: in the transcript", context(self.s.prompt("fix the header row")))


class ForgeState(Base):
    def setUp(self):
        super().setUp()
        self.s.write(".blueprints/exports/pipelines/01-csv/iterations.md", PIPELINE)

    def assertState(self, out):
        text = context(out)
        self.assertIn(os.path.normpath(CSV), text)
        self.assertIn("CSV, iteration 2.1: done and reported", text)
        self.assertIn("next unfinished iteration, CSV, iteration 2.2, PLANNED:\n"
                      "- Iteration 2.2: totals at the bottom of each\n  file, in the user's currency.", text)
        self.assertNotIn("Iteration 2.3", text)
        self.assertNotIn("- Iteration 2.1", text)

    def test_the_pipeline_by_number_name_or_folder(self):
        for command in ("/workshop-forge exports 1", "/tars:workshop-forge exports csv", "/workshop-forge exports 01-csv"):
            self.assertState(self.s.prompt(command))

    def test_the_task_by_path(self):
        self.assertState(self.s.prompt("/workshop-forge .blueprints/exports 1"))
        self.assertState(self.s.prompt(f"/workshop-forge {self.s.project / '.blueprints/exports'} csv"))

    def test_the_only_pipeline_when_none_is_named(self):
        self.assertState(self.s.prompt("/workshop-forge"))
        self.assertState(self.s.prompt("/workshop-forge exports"))

    def test_from_a_folder_inside_the_project(self):
        (self.s.project / "reports").mkdir()
        self.assertState(self.s.prompt("/workshop-forge exports 1", cwd=str(self.s.project / "reports")))

    def test_nothing_for_a_longer_command(self):
        for command in ("/workshop-forgeX", "/workshop-forge-pane exports 1", "/tars:workshop-forger"):
            self.assertNotIn("## Current", context(self.s.prompt(command)), command)

    def test_the_reminder_still_comes(self):
        self.assertIn("STTP active.", context(self.s.prompt("/workshop-forge exports 1")))

    def test_nothing_when_the_choice_is_not_clear(self):
        self.s.write(".blueprints/exports/pipelines/02-pdf/iterations.md", PIPELINE.replace("csv", "pdf"))
        for command in ("/workshop-forge", "/workshop-forge exports", "/workshop-forge exports 7", "/workshop-forge invoices 1"):
            self.assertNotIn("## Current", context(self.s.prompt(command)), command)
        self.assertState(self.s.prompt("/workshop-forge exports 1"))

    def test_nothing_while_sttp_is_paused_or_in_a_subagent(self):
        self.s.prompt("stop sttp")
        self.assertEqual(context(self.s.prompt("/workshop-forge exports 1")), "")
        self.s.prompt("start sttp")
        self.assertNotIn("## Current", context(self.s.prompt("/workshop-forge exports 1", agent_id="a1")))

    def test_the_status_comes_from_the_table(self):
        self.s.write(CSV, PIPELINE.replace("| CSV      | 2.1 | header row      | DONE    |",
                                           "| CSV      | 2.1 | header row      | BLOCKED |"))
        text = context(self.s.prompt("/workshop-forge exports 1"))
        self.assertIn("next unfinished iteration, CSV, iteration 2.1, BLOCKED:\n- Iteration 2.1: the header row", text)
        self.assertNotIn("Iteration 2.2", text)

    def test_the_current_row_comes_first_as_on_the_status_line(self):
        self.s.write(CSV, PIPELINE.replace("| CSV      | 2.1 | header row      | DONE    |",
                                           "| CSV      | 2.1 | header row      | BLOCKED |")
                                  .replace("| CSV      | 2.2 | totals          | PLANNED |",
                                           "| CSV      | 2.2 | totals          | CURRENT |"))
        text = context(self.s.prompt("/workshop-forge exports 1"))
        self.assertIn("next unfinished iteration, CSV, iteration 2.2, CURRENT:\n- Iteration 2.2: totals", text)
        self.assertNotIn("Iteration 2.1", text)

    def test_the_next_row_comes_before_an_earlier_planned_one(self):
        self.s.write(CSV, PIPELINE.replace("| CSV      | 2.3 | download button | PLANNED |",
                                           "| CSV      | 2.3 | download button | NEXT    |"))
        text = context(self.s.prompt("/workshop-forge exports 1"))
        self.assertIn("next unfinished iteration, CSV, iteration 2.3, NEXT:\n- Iteration 2.3: a download button", text)
        self.assertNotIn("Iteration 2.2", text)

    def test_the_pause_is_kept_where_the_mod_reads_it(self):
        flag = self.s.home / ".tars" / "paused-s1"
        self.s.prompt("stop sttp")
        self.assertTrue(flag.exists())
        self.s.prompt("start sttp")
        self.assertFalse(flag.exists())

    def test_the_pipeline_is_noted_for_the_mod(self):
        note = self.s.home / ".tars" / "forge-s1"
        self.s.prompt("/workshop-forge exports 1")
        self.assertEqual(note.read_text(), str(self.s.project / CSV))
        self.s.write(".blueprints/exports/pipelines/02-pdf/iterations.md", PIPELINE.replace("csv", "pdf"))
        self.s.prompt("/workshop-forge exports")
        self.assertEqual(note.read_text(), "")


class CompactionState(Base):
    def compact(self):
        return context(self.s.run("session-start", source="compact"))

    def test_workshop_forge_keeps_the_pipeline_it_named(self):
        self.s.write(CSV, PIPELINE)
        self.s.prompt("/workshop-forge exports 1")
        text = self.compact()
        self.assertIn(str(self.s.project / CSV), text)
        self.assertIn("CSV, iteration 2.1: done and reported", text)

    def test_workshop_forge_unnamed_keeps_the_pipeline_written_since(self):
        self.s.write(CSV, PIPELINE)
        self.s.write(CSV.replace("01-csv", "02-pdf"), PIPELINE)
        self.s.prompt("/workshop-forge")
        self.s.write(CSV, PIPELINE.replace("iteration 2.1: done and reported", "iteration 2.2: in progress"))
        text = self.compact()
        self.assertIn(str(self.s.project / CSV), text)
        self.assertIn("CSV, iteration 2.2: in progress", text)
        self.assertNotIn("02-pdf", text)

    def test_workshop_craft_keeps_the_scope_written_since(self):
        self.s.write(".blueprints/old/02-scope.md", SCOPE.replace("the split", "an old task"))
        self.s.prompt("/workshop-craft finance wants CSV downloads")
        self.s.write(".blueprints/exports/02-scope.md", SCOPE)
        text = self.compact()
        self.assertIn(str(self.s.project / ".blueprints/exports/02-scope.md"), text)
        self.assertIn("Current: the split, waiting on the user's answer to Q4.", text)
        self.assertNotIn("an old task", text)

    def test_workshop_glossary_bootstrap_keeps_its_working_file(self):
        self.s.write(".blueprints/glossary-bootstrap/bootstrap.md", BOOTSTRAP)
        self.s.prompt("/workshop-glossary-bootstrap")
        self.assertIn("Current: Billing, group 2: waiting on the user's picks.", self.compact())

    def test_only_the_resume_line_before_a_blueprint_file_exists(self):
        self.s.prompt("/workshop-craft finance wants CSV downloads")
        text = self.compact()
        self.assertIn("workshop-craft was started in this session", text)
        self.assertNotIn(str(self.s.project), text)

    def test_nothing_at_a_plain_start(self):
        self.s.write(CSV, PIPELINE)
        self.s.prompt("/workshop-forge exports 1")
        self.assertNotIn("CSV, iteration 2.1", context(self.s.run("session-start", source="startup")))


class MovedSession(Base):
    """A session moved to the background goes on under a new id, s2, with a scratchpad of its own; Claude Code ends
    the old transcript, s1's, with a "continued-in" line naming the new id."""

    def setUp(self):
        super().setUp()
        tmp = Path(self.tmp.name)
        self.transcripts = tmp / "transcripts"
        self.transcripts.mkdir()
        self.old = {"scratchpad_dir": str(tmp / "s1" / "scratchpad"),
                    "transcript_path": str(self.transcripts / "s1.jsonl")}
        self.new = {"session_id": "s2", "scratchpad_dir": str(tmp / "s2" / "scratchpad"),
                    "transcript_path": str(self.transcripts / "s2.jsonl")}

    def move(self, to="s2"):
        (self.transcripts / "s1.jsonl").write_text(
            '{"type":"user","sessionId":"s1"}\n'
            '{"type":"continued-in","timestamp":"2026-10-08T22:47:37.584Z","sessionId":"s1",'
            f'"continuedInSessionId":"{to}"}}\n'
            '{"type":"last-prompt","lastPrompt":"ok","sessionId":"s1"}\n')

    def test_the_pipeline_follows_into_the_compaction_lines_and_the_mods_note(self):
        self.s.write(CSV, PIPELINE)
        self.s.prompt("/workshop-forge exports 1", **self.old)
        self.move()
        text = context(self.s.run("session-start", source="compact", **self.new))
        self.assertIn("workshop-forge was started in this session", text)
        self.assertIn("CSV, iteration 2.1: done and reported", text)
        self.assertEqual((self.s.home / ".tars" / "forge-s2").read_text(), str(self.s.project / CSV))

    def test_a_folder_whose_name_holds_the_id_stays_as_it_is(self):
        runs = Path(self.tmp.name) / "runs2"  # "runs2" holds "s2"
        self.old["scratchpad_dir"] = str(runs / "s1" / "scratchpad")
        self.new["scratchpad_dir"] = str(runs / "s2" / "scratchpad")
        self.s.write(CSV, PIPELINE)
        self.s.prompt("/workshop-forge exports 1", **self.old)
        self.move()
        self.assertIn("workshop-forge was started in this session",
                      context(self.s.run("session-start", source="compact", **self.new)))

    def test_the_pause_follows(self):
        self.s.prompt("stop sttp", **self.old)
        self.move()
        self.assertEqual(self.s.prompt("hello", **self.new), {})

    def test_guards_off_follows(self):
        self.s.prompt("/sttp-guards off", **self.old)
        self.move()
        self.s.prompt("commit when you're done", **self.new)
        self.assertEqual(self.s.bash("git commit -m x", **self.new), {})

    def copied(self):
        """s2's transcript opens with the conversation it goes on from, its ids rewritten to s2, as after a move."""
        (self.transcripts / "s2.jsonl").write_text(
            '{"type":"user","sessionId":"s2","message":{"role":"user","content":"check the export"}}\n'
            '{"type":"assistant","sessionId":"s2","message":{"role":"assistant","content":"done"}}\n')

    def test_the_doctor_says_when_a_conversation_goes_on_with_no_move_line(self):
        self.copied()
        self.s.run("session-start", **self.new)
        self.assertIn("TARS could not trace", context(self.s.prompt("/tars-doctor", **self.new)))

    def test_the_doctor_says_nothing_of_it_in_a_new_session(self):
        (self.transcripts / "s2.jsonl").write_text(
            '{"type":"user","sessionId":"s2","message":{"role":"user","content":"/tars-doctor"}}\n')
        self.assertNotIn("TARS could not trace", context(self.s.prompt("/tars-doctor", **self.new)))

    def test_the_doctor_says_nothing_of_it_after_a_traced_move(self):
        self.copied()
        self.move()
        self.s.run("session-start", **self.new)
        self.assertNotIn("TARS could not trace", context(self.s.prompt("/tars-doctor", **self.new)))

    def test_another_sessions_notes_stay_with_it(self):
        self.s.write(CSV, PIPELINE)
        self.s.prompt("/workshop-forge exports 1", **self.old)
        self.move(to="s3")
        self.assertNotIn("workshop-forge was started", context(self.s.run("session-start", source="compact", **self.new)))
        self.assertFalse((self.s.home / ".tars" / "forge-s2").exists())


class OldNotes(Base):
    def test_a_session_start_deletes_the_session_notes_untouched_for_30_days(self):
        tars = self.s.home / ".tars"
        tars.mkdir()
        days = {"paused-old": 31, "guards-off-old": 31, "forge-old": 31, "paused-recent": 29,
                "mode": 31, "questions": 31, "guards-default": 31}
        for name, age in days.items():
            (tars / name).write_text("")
            then = time.time() - age * 24 * 3600
            os.utime(tars / name, (then, then))
        self.s.run("session-start")
        self.assertEqual(sorted(p.name for p in tars.iterdir()), ["guards-default", "mode", "paused-recent", "questions"])


class CodexOldNotes(OldNotes):
    codex = True


class CodexForgeState(ForgeState):
    codex = True

    def test_dollar_form_with_more_text_after(self):
        self.assertState(self.s.prompt("$workshop-forge exports csv, go on from where we stopped"))


class RuleParts(Base):
    """Claude Code shows a hook's output over 10,000 characters as a 2 KB preview, the rest saved to a file."""

    def assertWhole(self, out, *skills):
        for part in self.s.parts:
            self.assertLessEqual(len(context(part)), 10_000)
        for name in skills:
            body = (ROOT / "skills" / name / "SKILL.md").read_text().split("\n---\n", 1)[1]
            self.assertIn(body, context(out), name)

    def test_the_rules_at_a_compaction(self):
        self.s.write(CSV, PIPELINE)
        self.s.prompt("/workshop-forge exports 1")
        out = self.s.run("session-start", source="compact")
        self.assertWhole(out, "sttp", "sttp-software-engineering")
        self.assertIn("CSV, iteration 2.1: done and reported", context(out))

    def test_the_coding_rules_once(self):
        self.assertWhole(self.s.run("pre-edit", tool_name="Edit"), "sttp-software-coding", "sttp-software-testing")
        self.assertEqual(self.s.run("pre-edit", tool_name="Edit"), {})

    def test_the_rules_in_a_subagent(self):
        self.s.prompt("/sttp-mode full")
        self.assertWhole(self.s.run("subagent-start", agent_id="a1"), "sttp", "sttp-software-engineering")


class Doctor(Base):
    """/tars-doctor: the hook tells the agent what this session should have, from its notes."""

    def doctor(self, command="/tars-doctor"):
        return context(self.s.prompt(command))

    def test_which_copy_runs_and_the_notes(self):
        version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
        text = self.doctor()
        self.assertIn(f"TARS {version}, from {ROOT}.", text)
        self.assertIn("STTP on, mode primary", text)
        self.assertIn("git guard: on", text)
        self.assertIn("pipeline /workshop-forge named: none", text)
        self.assertNotIn("STTP active.", text)

    def test_the_coding_rules_count_from_the_last_compaction(self):
        self.assertIn("not sent since the session's start", self.doctor())
        self.s.run("pre-edit", tool_name="Edit")
        self.assertIn("sent at the first edit since", self.doctor())
        self.s.run("session-start", source="compact")
        self.assertIn("not sent since the session's start or its last compaction", self.doctor())

    def test_a_running_skill_with_its_current_line(self):
        self.s.write(CSV, PIPELINE)
        self.s.prompt("/workshop-forge exports 1")
        text = self.doctor()
        self.assertIn(f"pipeline /workshop-forge named: {self.s.project / CSV}", text)
        self.assertIn(f"Started in this session: workshop-forge, its file {self.s.project / CSV}", text)
        self.assertIn("CSV, iteration 2.1: done and reported", text)

    def test_the_pause_and_guards_off(self):
        self.s.prompt("/sttp-guards off")
        self.assertIn("git guard: off", self.doctor())
        self.s.prompt("stop sttp")
        text = self.doctor()
        self.assertIn("STTP is paused for this session", text)
        self.assertNotIn("STTP on", text)

    def test_the_question_form(self):
        self.assertIn("Grill questions: dialog.", self.doctor())
        self.s.prompt("/workshop-questions transcript")
        self.assertIn("Grill questions: transcript.", self.doctor())

    def test_the_guards_default(self):
        self.s.prompt("/sttp-guards default off")
        self.assertIn("The git guard: off, the default.", self.doctor())
        self.s.prompt("/sttp-guards on")
        self.assertIn("The git guard: on for this session; the default is off.", self.doctor())

    def test_a_linked_install_shows_the_folder_it_links_to(self):
        link = Path(self.tmp.name) / "skills-link"
        link.symlink_to(ROOT)
        text = context(self.s.prompt("/tars-doctor", root=link))
        self.assertIn(f"from {ROOT}.", text)
        self.assertIn(f"Skill files: {ROOT / 'skills'}{os.sep}", text)

    def test_its_forms(self):
        for command in ("/tars:tars-doctor", "/tars-doctor the agent skipped the stop"):
            self.assertIn("TARS doctor", self.doctor(command), command)
        self.assertNotIn("TARS doctor", self.doctor("/tars-doctorX"))


class CodexDoctor(Base):
    codex = True

    def test_dollar_form_with_codex_version(self):
        version = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())["version"]
        self.assertIn(f"TARS {version}, from {ROOT}.", context(self.s.prompt("$tars-doctor")))


if __name__ == "__main__":
    unittest.main()
