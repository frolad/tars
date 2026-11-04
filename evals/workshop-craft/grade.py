"""Grade every run of an iteration: python3 grade.py <iteration-dir>.

Needs per run: outputs/final.md (the reply), outputs/commands.txt and metrics.json (extract.py), and optionally
judgement.json ([{"text", "passed", "evidence"}], graded by reading the reply). Writes grading.json per run.
The run's config is its directory's parent: with_skill reads the workshop-craft snapshot, without_body must not.
Takes what counts as a TARS Blueprint Record from `../workshop-forge/grade.py`.
"""
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("forge_grade", HERE.parent / "workshop-forge/grade.py")
fg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fg)
outside_blueprints_diff, record_files = fg.outside_blueprints_diff, fg.record_files
PIPELINE_FILE = "iterations.md"
BP = Path(".blueprints/finance-exports")
SNAPSHOT_MARK = "workshop-craft-snapshot"
SKILLS_READ = ("/skills/sttp/SKILL.md", "/sttp-software-engineering/SKILL.md", "/workshop-grill/SKILL.md")
EVALS = {e["id"]: e for e in json.load(open(HERE / "evals.json"))["evals"]}
EMOJI = re.compile("[☀-➿\U0001f300-\U0001faff⬅-⬇⭐]")
LABEL = re.compile(r"\*\*Q(\d+)(?:\*\*)?\s*[-–—:]")
SHAPE_LABEL = re.compile(r"^❓ \*\*Q\d+\*\* - \*\*[^*\n]+\*\*:", re.M)
RECOMMENDED = re.compile(r"(^|\n)\s*➡")
PROPOSED = re.compile(r"❓ \*\*Q\d+\*\* - \*\*([^*\n]+)\*\*:\s*\n+```\n(.*?)\n```", re.S)


def check(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": evidence}


def norm(text):
    return " ".join(text.split())


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def questions(reply):
    starts = [m.start() for m in LABEL.finditer(reply)]
    return [reply[a:b] for a, b in zip(starts, starts[1:] + [len(reply)])]


def sections(path):
    """{heading: normalised body} of a markdown file's '## ' sections; {} when the file is absent."""
    if not path.exists():
        return {}
    out, cur = {}, None
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            out[cur] = []
        elif cur:
            out[cur].append(line)
    return {k: norm("\n".join(v)) for k, v in out.items()}


def proposed(case):
    """{section title: normalised text} of the sections the case's prompt proposed in fenced blocks."""
    return {t.strip(): norm(b) for t, b in PROPOSED.findall(EVALS[case]["prompt"])}


def fresh(fixture):
    tmp = tempfile.TemporaryDirectory()
    repo = Path(tmp.name) / "repo"
    subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), fixture, str(repo)], check=True,
                   capture_output=True)
    return tmp, repo


def common(run, repo, base, commands):
    diff = outside_blueprints_diff(base, repo)
    records = sorted(str(f.relative_to(repo)) for f in record_files(repo))  # workshop-craft writes no record
    state = {"commits": git(repo, "rev-list", "--all", "--count"), "branches": git(repo, "branch", "--format=%(refname:short)"),
             "head": git(repo, "symbolic-ref", "--short", "HEAD"), "staged": git(repo, "diff", "--cached", "--name-only"),
             "stash": git(repo, "stash", "list"), "worktrees": str(len(git(repo, "worktree", "list").splitlines()))}
    git_ok = state == {"commits": "1", "branches": "main", "head": "main", "staged": "", "stash": "", "worktrees": "1"}
    if not (base / ".git").exists():
        git_ok = not (repo / ".git").exists()
        state = {"git": "not a repository" if git_ok else "a repository was created"}
    reads_craft = run.parent.name != "without_body"  # with_skill, or an older workshop-craft as the baseline
    allowed = SKILLS_READ + ((SNAPSHOT_MARK,) if reads_craft else ())
    other = [l for l in commands.splitlines() if l.startswith(("$ ", "["))
             and (("SKILL.md" in l and not any(a in l for a in allowed)) or "/skills/workshop-craft/" in l
                  or (SNAPSHOT_MARK in l and not reads_craft))]
    skill_calls = json.load(open(run / "metrics.json")).get("tool_calls", {}).get("Skill", 0)
    return [
        check("No file outside .blueprints changed, .gitignore included", not diff and not records,
              diff or (f"records written: {records}" if records else "no file outside .blueprints differs from the fixture")),
        check("Git untouched: one commit, only main, clean index, no stash, no extra worktree", git_ok, json.dumps(state)),
        check("No other skill was loaded", not other and not skill_calls,
              f"Skill tool calls: {skill_calls}; other skill reads: {other[:3]}"),
    ]


def format_checks(reply, qs):
    labels = LABEL.findall(reply)
    shaped = SHAPE_LABEL.findall(reply)
    emoji = [e for e in EMOJI.findall(reply) if e not in "❓➡"]
    rec = [q for q in qs if RECOMMENDED.search(q)]
    return [
        check("Questions use the transcript shape: '❓ **Qn** - **title**:' labels, '➡️' answers, no other emoji",
              qs and len(shaped) == len(labels) and not emoji,
              f"{len(labels)} labels, {len(shaped)} in the shape, other emoji: {''.join(emoji) or 'none'}"),
        check("Every question carries a recommended answer", qs and len(rec) == len(qs),
              f"{len(rec)} of {len(qs)} questions have one"),
    ]


def reads(commands):
    """Reads of the fixture repo; the skill files and the run's task file are not counted."""
    return [l for l in commands.splitlines()
            if (l.startswith("[Read]") and "<repo>" in l)
            or (re.match(r"\$ .*\b(cat|grep|rg|sed|head|ls|find)\b", l)
                and not re.search(r"workshop-craft-snapshot|task\.md", l))]


def pipeline_checks(repo):
    files = sorted((repo / BP / "pipelines").glob(f"0*-*/{PIPELINE_FILE}"))
    out = [check("One pipeline file per pipeline, three pipelines", len(files) == 3,
                 f"{[str(f.relative_to(repo / BP)) for f in files]}")]
    missing, not_prelim, releases = {}, [], False
    for f in files:
        t = f.read_text()
        need = {"Goal": r"^Goal:", "Done when: scope": r"^Done when: scope",
                "Iteration size": r"^Iteration size:[^\n]*(?:\n[^\n#-][^\n]*)*?user[^\n]*(?:\n[^\n]*)??\d{4}-\d{2}-\d{2}",
                "## Current": r"^## Current", "## Iterations": r"^## Iterations"}
        gone = [k for k, rx in need.items() if not re.search(rx, t, re.M)]
        if gone:
            missing[f.parent.name] = gone
        st = {(c, n): s for c, n, s in
              re.findall(r"^\|\s*([^|]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|[^|]*\|\s*([A-Z-]+)\s*\|\s*$", t, re.M)}
        category, its = "", []
        for line in t.splitlines():
            if line.startswith("### "):
                category = line[4:].strip()
            elif m := re.match(r"- Iteration (\d+(?:\.\d+)?)", line):
                its.append((category, m.group(1)))
        not_prelim += [f"{f.parent.name}: {c}, iteration {n}: {st.get((c, n), 'no row')}" for c, n in its
                       if st.get((c, n)) not in ("PLANNED", "BLOCKED")] or ([] if its else [f"{f.parent.name}: no iteration"])
        if f.parent.name.startswith("01-"):
            releases = bool(re.search(r"^Releases:", t, re.M))
    out.append(check("Each pipeline file has Goal, Done when: scope, Iteration size confirmed by the user on a date, "
                     "Current and Iterations", files and not missing, f"missing: {missing or 'none'}"))
    out.append(check("Every iteration has a PLANNED or BLOCKED row in the status table", files and not not_prelim,
                     f"not PLANNED or BLOCKED: {not_prelim[:4] or 'none'}"))
    out.append(check("Pipeline 1 has a Releases line", releases, "Releases: found" if releases else "no Releases: line in 01-*"))
    questions_nyc, bad_blockers = [], []
    for f in files:
        body = dict(re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", f.read_text(), re.M | re.S))
        questions_nyc += [f"{f.parent.name}: {l[:70]}" for l in body.get("Not yet clear", "").splitlines()
                          if re.search(r"\?|decid|decision|the user", l, re.I)]
        bad_blockers += [f"{f.parent.name}: {l[:70]}" for l in body.get("Blockers", "").splitlines()
                         if l.startswith("- ") and not re.match(r"- Blocker \d+, blocks [^,]+, iteration \d+", l)]
    out.append(check("An open decision is a Blocker naming the iteration it blocks, not a Not yet clear line",
                     files and not questions_nyc and not bad_blockers,
                     f"questions under Not yet clear: {questions_nyc or 'none'}; malformed blockers: {bad_blockers or 'none'}"))
    return out


def grade(run, case):
    reply = (run / "outputs/final.md").read_text()
    commands = (run / "outputs/commands.txt").read_text()
    repo, qs = run / "repo", questions(reply)
    tmp, base = fresh(EVALS[case]["fixture"])
    scope, base_scope = sections(repo / BP / "02-scope.md"), sections(base / BP / "02-scope.md")
    scope_text = (repo / BP / "02-scope.md").read_text() if (repo / BP / "02-scope.md").exists() else ""
    out = common(run, repo, base, commands)
    if case == 1:
        r = [l for l in reads(commands) if "reports/" in l]
        out.append(check("Read the code under reports/ before replying", r, f"{len(r)} reads of reports/"))
        files = [str(p.relative_to(repo)) for p in (repo / ".blueprints").rglob("*") if p.is_file()]
        out.append(check("No blueprint file written before the task is confirmed", not files, f"files: {files or 'none'}"))
        out.append(check("02-scope.md holds no section text", not scope, f"sections: {list(scope) or 'none'}"))
        out.append(check("The reply says .blueprints is not ignored by git",
                         re.search(r"\.blueprints", reply) and re.search(r"ignor", reply, re.I),
                         "mentions .blueprints and ignore" if re.search(r"ignor", reply, re.I) else "no mention of ignore"))
        out += format_checks(reply, qs)
    if case in (2, 3):
        out.append(check("No blueprint written", not (repo / ".blueprints").exists(),
                         "no .blueprints directory" if not (repo / ".blueprints").exists() else ".blueprints exists"))
    if case == 3:
        out.append(check("The reply mentions workshop-forge", re.search(r"\bworkshop-forge\b", reply, re.I), "workshop-forge named" if
                         re.search(r"\bworkshop-forge\b", reply, re.I) else "workshop-forge not named"))
    if case == 4:
        out.append(check("02-scope.md holds Task, Goal and Done when, and no In scope or Out of scope",
                         {"Task", "Goal", "Done when"} <= set(scope) and not {"In scope", "Out of scope"} & set(scope),
                         f"sections: {list(scope)}"))
        out.append(check("02-scope.md has a Current line", re.search(r"^Current:", scope_text, re.M),
                         (re.search(r"^Current:.*$", scope_text, re.M) or [""])[0][:120] or "no Current line"))
        out += format_checks(reply, qs)
        low = [n for n in LABEL.findall(reply) if int(n) <= 7]
        out.append(check("New questions take numbers after Q7", qs and not low,
                         f"labels: {LABEL.findall(reply)}"))
    if case == 5:
        written = [p for p in ("03-workmap.md", "pipelines") if (repo / BP / p).exists()]
        out.append(check("No work map or pipeline written before the split is confirmed", not written,
                         f"written: {written or 'none'}"))
        want = proposed(5)["Out of scope"]
        out.append(check("Out of scope is written as approved, word for word", scope.get("Out of scope") == want,
                         f"Out of scope: {(scope.get('Out of scope') or 'absent')[:120]}"))
        out.append(check("In scope is unchanged", scope.get("In scope") == base_scope.get("In scope"),
                         f"In scope: {(scope.get('In scope') or 'absent')[:120]}"))
    if case == 6:
        wm = (repo / BP / "03-workmap.md").read_text() if (repo / BP / "03-workmap.md").exists() else ""
        need = {"Waits for": r"Waits for:", "Hands over": r"Hands over:", "Order": r"^## Order", "Critical path": r"^Critical path:"}
        gone = [k for k, rx in need.items() if not re.search(rx, wm, re.M)]
        out.append(check("03-workmap.md has Waits for, Hands over, an Order section and a Critical path", wm and not gone,
                         f"missing: {gone or 'none'}" if wm else "no 03-workmap.md"))
        out += pipeline_checks(repo)
        confirmed = re.search(r"^Confirmed on:", scope_text, re.M)
        current = re.search(r"^Current:.*$", scope_text, re.M)
        out.append(check("The scope keeps a Current line and has no Confirmed on before the user's OK",
                         current and not confirmed,
                         f"Confirmed on: {'yes' if confirmed else 'no'}; {current.group(0)[:100] if current else 'no Current line'}"))
        changed = [k for k in ("In scope", "Out of scope") if scope.get(k) != base_scope.get(k)]
        out.append(check("In scope and Out of scope are unchanged", not changed, f"changed: {changed or 'none'}"))
    if case == 7:
        files = [str(p.relative_to(repo)) for p in (repo / ".blueprints").rglob("*") if p.is_file()] \
            if (repo / ".blueprints").exists() else []
        out.append(check("No blueprint file written before the first round is answered", not files,
                         f"files: {files or 'none'}"))
        out.append(check("The reply says .blueprints is not ignored by git",
                         re.search(r"\.blueprints", reply) and re.search(r"ignor", reply, re.I),
                         "mentions .blueprints and ignore" if re.search(r"ignor", reply, re.I) else "no mention of ignore"))
        out += format_checks(reply, qs)
    if case == 8:
        new = sorted(str(p.relative_to(repo)) for p in repo.rglob("*") if p.is_file()
                     and not (base / p.relative_to(repo)).exists() and "__pycache__" not in p.parts)
        out.append(check("No file written in the folder", not new, f"new files: {new or 'none'}"))
        out.append(check("The reply suggests a folder for the blueprint", re.search(r"folder|directory", reply, re.I),
                         "a folder is named" if re.search(r"folder|directory", reply, re.I) else "no folder named"))
        out += format_checks(reply, qs)
    if case == 9:
        confirmed = re.search(r"^Confirmed on: \d{4}-\d{2}-\d{2}", scope_text, re.M)
        current = re.search(r"^Current:", scope_text, re.M)
        out.append(check("The scope has Confirmed on: <date> in place of its Current line", confirmed and not current,
                         f"Confirmed on: {confirmed.group(0) if confirmed else 'no'}; Current line: {'yes' if current else 'no'}"))
        bp, base_bp = repo / BP, base / BP
        others = {str(f.relative_to(base_bp)) for f in base_bp.rglob("*") if f.is_file()} | \
                 {str(f.relative_to(bp)) for f in bp.rglob("*") if f.is_file()}
        differ = sorted(f for f in others - {"02-scope.md"} if not (bp / f).exists() or not (base_bp / f).exists()
                        or (bp / f).read_text() != (base_bp / f).read_text())
        out.append(check("No other blueprint file changed", not differ, f"changed: {differ or 'none'}"))
        changed = sorted(k for k in set(scope) | set(base_scope) if scope.get(k) != base_scope.get(k))
        out.append(check("The scope's sections are unchanged", not changed, f"changed: {changed or 'none'}"))
        m = re.search(r"/workshop-forge finance-exports[^\n`]*", reply)
        out.append(check("The last message gives /workshop-forge finance-exports", m, m.group(0) if m else "no /workshop-forge finance-exports"))
    if case == 10:
        first = sorted(f.name for f in (repo / ".blueprints").glob("*/*.md")) if (repo / ".blueprints").exists() else []
        out.append(check("The blueprint's first files are written: 00-knowledge.md and 02-scope.md",
                         {"00-knowledge.md", "02-scope.md"} <= set(first), f"{first or 'none'}"))
        out += format_checks(reply, qs)
        low = [n for n in LABEL.findall(reply) if int(n) <= 3]
        out.append(check("New questions take numbers after Q3", qs and not low, f"labels: {LABEL.findall(reply)}"))
    tmp.cleanup()
    j = run / "judgement.json"
    if j.exists():
        out += json.load(open(j))
    passed = sum(c["passed"] for c in out)
    json.dump({"expectations": out,
               "summary": {"passed": passed, "failed": len(out) - passed, "total": len(out),
                           "pass_rate": round(passed / len(out), 3)}},
              open(run / "grading.json", "w"), indent=2)
    return passed, len(out)


if __name__ == "__main__":
    it = Path(sys.argv[1])
    for run in sorted(it.glob("eval-*/*/run-*")):
        if (run / "outputs/final.md").exists():
            p, t = grade(run, int(run.parent.parent.name.split("-")[1]))
            print(f"{run.relative_to(it)}: {p}/{t}")
