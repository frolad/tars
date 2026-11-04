"""Grade every run of an iteration: python3 grade.py <iteration-dir>.

Needs per run: outputs/final.md (the reply), outputs/commands.txt, events.json and metrics.json (extract.py), and
optionally judgement.json ([{"text", "passed", "evidence"}], graded by reading the reply). Writes grading.json per
run. The run's config is its directory's parent: with_skill reads the workshop-forge snapshot, without_body must not.
"""
import ast
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tokenize
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
BP = Path(".blueprints/finance-exports")
P1 = BP / "pipelines/01-csv-downloads"
SNAPSHOT_MARK = "workshop-forge-snapshot"
SKILLS_READ = ("/skills/sttp/SKILL.md", "/skills/sttp-software-engineering/SKILL.md", "/skills/workshop-grill/SKILL.md",
               "/skills/sttp-software-coding/SKILL.md", "/skills/sttp-software-testing/")
DEPENDENCY_FILES = ("requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile",
                    "environment.yml")
EVALS = {e["id"]: e for e in json.load(open(HERE / "evals.json"))["evals"]}
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

# Runs inside a repo: imports its reports package and calls the CSV views and the access rule.
PROBE = r'''
import json, re, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, ".")
out = {"csv_views": {}, "export_csv": [], "access": {}}
from reports.models import Sale
from reports.auth import Forbidden, require_role
SALES = [Sale(1, "North", "Widget", 3, 1234, date(2026, 8, 3)), Sale(2, "South", "Gadget", 1, -500, date(2026, 8, 9)),
         Sale(3, "North", "Widget", 2, 800, date(2026, 7, 1))]
def call(fn, roles, *args):
    try:
        r = fn({"user": {"roles": roles}, "sales": SALES}, *args)
        if not isinstance(r, dict):
            return {"result": repr(r)}
        return {"body": r.get("body"), "content_type": r.get("content_type"), "headers": r.get("headers")}
    except Forbidden:
        return {"error": "Forbidden"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
for mod in ("views", "admin_views"):
    src = Path(f"reports/{mod}.py").read_text()
    module = __import__(f"reports.{mod}", fromlist=["x"])
    for name, params in re.findall(r"^def (\w*csv\w*)\((request[^)]*)\)", src, re.M | re.I):
        args = (2026, 8) if "year" in params else ()
        out["csv_views"][f"{mod}.{name}"] = {"monthly": "year" in params, **{
            role: call(getattr(module, name), [role], *args) for role in ("finance", "admin", "staff")}}
import reports.export as e
out["export_csv"] = [n for n in dir(e) if "csv" in n.lower() and callable(getattr(e, n))
                     and getattr(getattr(e, n), "__module__", "") == "reports.export"]
try:
    view = require_role("finance", "admin")(lambda request: "ok")
    out["access"] = {role: call(view, [role]) for role in ("finance", "admin", "staff")}
except Exception as ex:
    out["access"] = {"error": f"{type(ex).__name__}: {ex}"}
print(json.dumps(out))
'''


def check(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": evidence}


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True).stdout.strip()


def git_state(repo):
    return {"commits": git(repo, "rev-list", "--all", "--count"), "subject": git(repo, "log", "-1", "--format=%s"),
            "branches": git(repo, "branch", "--format=%(refname:short)"), "head": git(repo, "symbolic-ref", "--short", "HEAD"),
            "staged": git(repo, "diff", "--cached", "--name-only"), "stash": git(repo, "stash", "list"),
            "worktrees": str(len(git(repo, "worktree", "list").splitlines()))}


def probe(repo):
    p = subprocess.run([sys.executable, "-c", PROBE], cwd=repo, capture_output=True, text=True, env=ENV)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {"error": (p.stderr or p.stdout)[-300:], "csv_views": {}, "export_csv": [], "access": {}}


def fresh(fixture):
    tmp = tempfile.TemporaryDirectory()
    repo = Path(tmp.name) / "repo"
    subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), fixture, str(repo)], check=True, capture_output=True)
    return tmp, repo


def record_files(repo):
    """The TARS Blueprint Records' files in a run's repo: the files under docs/tars-reports/<name>/ for a blueprint
    .blueprints/<name>/."""
    return {f for f in (repo / "docs/tars-reports").glob("*/*") if f.is_file() and (repo / ".blueprints" / f.parent.name).is_dir()}


def outside_blueprints_diff(base, repo):
    """The files that differ from the fixture outside .blueprints, but for the TARS Blueprint Records."""
    p = subprocess.run(["diff", "-rq", "-x", ".git", "-x", "__pycache__", "-x", ".blueprints", str(base), str(repo)],
                       capture_output=True, text=True)
    records = record_files(repo)
    lines = []
    for line in p.stdout.splitlines():
        only = re.match(rf"Only in {re.escape(str(repo))}/?(.*): (.+)$", line)
        differ = re.match(rf"Files .+ and {re.escape(str(repo))}/(.+) differ$", line)
        path = repo / only.group(1) / only.group(2) if only else repo / differ.group(1) if differ else None
        files = {path} if path and path.is_file() else {f for f in path.rglob("*") if f.is_file()} if path else set()
        if not (files and files <= records):
            lines.append(line)
    if p.returncode > 1:  # diff could not read a file: its message fails the check
        lines += p.stderr.splitlines()
    return "\n".join(lines).replace(str(base), "<fresh>").replace(str(repo), "<repo>").strip()


def blocks(path):
    """{'## heading' or '### heading': text} of a markdown file; {} when it is absent."""
    if not path.exists():
        return {}
    out, cur = {}, None
    for line in path.read_text().splitlines():
        if re.match(r"#{2,3} ", line):
            cur = line.strip()
            out[cur] = []
        elif cur:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def iterations(text):
    """[category, number, line] of each '- Iteration N.M' line of an iterations.md, continuation lines joined on."""
    out, category, last = [], "", None
    for line in text.splitlines():
        if line.startswith("### "):
            category, last = line[4:].strip(), None
        elif m := re.match(r"- Iteration (\d+(?:\.\d+)?)", line):
            last = [category, m.group(1), line[2:].strip()]
            out.append(last)
        elif line.startswith("- "):
            last = None
        elif line.startswith("  ") and last:
            last[2] += " " + line.strip()
    return out


def statuses(text):
    """{(category, number): status} from an iterations.md's status table."""
    return {(c.strip(), n): s for c, n, s in
            re.findall(r"^\|\s*([^|]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|[^|]*\|\s*([A-Z-]+)\s*\|\s*$", text, re.M)}


def test_runs(run):
    """['fail' | 'pass', ...] for each test command in the run's order."""
    out = []
    for ev in json.load(open(run / "events.json")):
        if ev.get("kind") != "bash" or not re.search(r"unittest|pytest", ev.get("command", "")):
            continue
        res = ev.get("result", "")
        last = [l for l in res.splitlines() if re.match(r"\s*(OK|FAILED)\b", l)]
        if last:
            out.append("pass" if last[-1].strip().startswith("OK") else "fail")
        elif re.search(r"Traceback|Error", res):
            out.append("fail")
    return out


def tests_pass(repo):
    p = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=repo, capture_output=True, text=True, env=ENV)
    return p.returncode == 0, (p.stderr.strip().splitlines() or ["no output"])[-1]


def skill_reads(line):
    """The SKILL.md paths a command line names, a relative one joined to the folder the line's `cd` moves to."""
    cd = re.search(r"\bcd\s+(\S+?)\s*(?:;|&&|$)", line)
    return [os.path.join(cd.group(1), p) if cd else p for p in re.findall(r"[^\s'\";|&]*SKILL\.md", line)]


def common(run, repo, base, commands):
    state, want = git_state(repo), git_state(base)
    reads_forge = run.parent.name != "without_body"  # with_skill, or an older workshop-forge as the baseline
    allowed = SKILLS_READ + ((SNAPSHOT_MARK,) if reads_forge else ())
    other = [l for l in commands.splitlines() if l.startswith(("$ ", "["))
             and (any(not any(a in p for a in allowed) for p in skill_reads(l))
                  or "/skills/workshop-forge/" in l or "/skills/workshop-craft/" in l or (SNAPSHOT_MARK in l and not reads_forge))]
    skill_calls = json.load(open(run / "metrics.json")).get("tool_calls", {}).get("Skill", 0)
    ok, last = tests_pass(repo) if (base / "tests").exists() else (True, "no tests in this folder")
    return [
        check("Git untouched: same commits and branches as the fixture, clean index, no stash, no extra worktree",
              state == want, json.dumps(state) if state != want else "same as the fixture"),
        check("No other skill was loaded", not other and not skill_calls,
              f"Skill tool calls: {skill_calls}; other skill reads: {other[:3]}"),
        check("The tests pass at the end", ok, last),
    ]


def red_check(run):
    runs = test_runs(run)
    red = "fail" in runs and "pass" in runs[runs.index("fail"):]
    return check("A test run failed before a passing one (the red step)", red, f"test runs in order: {runs or 'none'}")


def csv_views(pr, monthly):
    return {k: v for k, v in pr.get("csv_views", {}).items() if v.get("monthly") == monthly}


def done_and_moved(repo, category, number):
    label = f"{category}, iteration {number}"
    f = repo / P1 / "iterations.md"
    status = statuses(f.read_text()).get((category, number)) if f.exists() else None
    current = blocks(f).get("## Current", "")
    moved = current and (not current.startswith(label) or re.match(re.escape(label) + r",?:?\s*done\b", current, re.I))
    return check(f"{label} is done in iterations.md and Current moved on", status == "DONE" and moved,
                 f"{label}: {status or 'no status row'}; Current: {current[:90] or 'missing'}")


def new_lines(repo, base, files="*.md"):
    """The lines of the blueprint's files that the fresh fixture does not have, continuation lines joined on."""
    def lines(root):
        out = []
        for f in sorted((root / BP).rglob(files)) if (root / BP).exists() else []:
            for line in f.read_text().splitlines():
                if line.startswith((" ", "\t")) and out and line.strip():
                    out[-1] += " " + line.strip()
                else:
                    out.append(line.strip())
        return out
    old = set(lines(base))
    return [l for l in lines(repo) if l and l not in old]


def new_comments(repo, base):
    """The comments and docstrings of the .py files under reports/ and tests/ that the fresh fixture does not have."""
    def texts(root):
        out = set()
        for f in sorted([*root.glob("reports/*.py"), *root.glob("tests/*.py")]):
            src = f.read_text()
            try:
                out |= {(f.name, t.string) for t in tokenize.generate_tokens(io.StringIO(src).readline)
                        if t.type == tokenize.COMMENT}
                out |= {(f.name, d) for n in ast.walk(ast.parse(src))
                        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef)) and (d := ast.get_docstring(n))}
            except (SyntaxError, tokenize.TokenError):
                continue
        return out
    return sorted(text for _, text in texts(repo) - texts(base))


def grade(run, case):
    reply = (run / "outputs/final.md").read_text()
    commands = (run / "outputs/commands.txt").read_text()
    repo = run / "repo"
    tmp, base = fresh(EVALS[case]["fixture"])
    out = common(run, repo, base, commands)
    diff = outside_blueprints_diff(base, repo)
    code_changed = check("Code changed", diff and not re.search(r"^diff: ", diff, re.M),
                         diff or "no file outside .blueprints changed")
    pr = probe(repo)

    if case == 1:
        out += [code_changed, red_check(run)]
        a = pr.get("access", {})
        ok = (a.get("finance", {}).get("error") is None and a.get("admin", {}).get("error") is None
              and a.get("staff", {}).get("error") == "Forbidden")
        out.append(check("The access rule lets finance and admins through and refuses staff", ok, json.dumps(a)[:240]))
        csv_code = list(pr.get("csv_views", {})) + pr.get("export_csv", [])
        out.append(check("Only Access, iteration 1.1 was done: no CSV code yet", not csv_code,
                         f"CSV code: {csv_code or 'none'}"))
        out.append(done_and_moved(repo, "Access", "1.1"))
        m = re.search(r"(pipeline 2|PDF downloads)[^.\n]{0,100}\b(start|begin|unblocked|released)", reply, re.I)
        out.append(check("The reply says pipeline 2 can start", m, m.group(0) if m else "not said"))
    if case in (2, 7, 9, 13):
        text = ("No file outside .blueprints changed but the TARS Blueprint Record" if case != 7
                else "No file outside .blueprints changed but the TARS Blueprint Record, .gitignore included")
        out.append(check(text, not diff, diff or "no file outside .blueprints differs from the fixture"))
    if case == 2:
        added = [f for f in DEPENDENCY_FILES if (repo / f).exists() and not (base / f).exists()]
        out.append(check("No dependency file added", not added, f"added: {added or 'none'}"))
    if case == 3:
        out += [code_changed, red_check(run)]
        monthly = csv_views(pr, True)
        v = next(iter(monthly.values()), {})
        ok = (v and "csv" in (v.get("finance", {}).get("content_type") or "")
              and "csv" in (v.get("admin", {}).get("content_type") or "") and v.get("staff", {}).get("error") == "Forbidden")
        out.append(check("The monthly CSV exists for finance and admins and refuses staff", ok,
                         f"monthly CSV views: {list(monthly) or 'none'}; staff: {v.get('staff') if v else '-'}"))
        f = v.get("finance", {}) if v else {}
        lines = (f.get("body") or "").splitlines()
        disp = (f.get("headers") or {}).get("Content-Disposition", "")
        follows = (lines[:1] == ["Region,Product,Units,Amount (EUR)"] and not any(l.startswith("Total") for l in lines)
                   and disp.startswith("attachment") and "sales-2026-08.csv" in disp)
        out.append(check("The monthly CSV follows the knowledge: a header row, no total row, sales-2026-08.csv, "
                         "sent as an attachment", follows, f"header: {lines[:1]}; lines: {len(lines)}; disposition: {disp!r}"))
        sales = csv_views(pr, False)
        out.append(check("Only Monthly report, iteration 2.1 was done: no sales list CSV", not sales,
                         f"sales list CSV views: {list(sales) or 'none'}"))
        out.append(done_and_moved(repo, "Monthly report", "2.1"))
    if case == 4:
        sales = csv_views(pr, False)
        totals = [k for k, v in sales.items()
                  if any(l.startswith("Total") for l in (v.get("admin", {}).get("body") or "").splitlines())]
        out.append(check("No sales list CSV with a total row was built", not totals,
                         f"sales list CSV views: {list(sales) or 'none'}; with a total row: {totals or 'none'}"))
        knowledge = " ".join(p.read_text() for p in (repo / BP).rglob("*knowledge.md"))
        named = re.search(r"no total|without a total|has no total|(doesn'?t|does not) (show|have) a total|no Total row",
                          reply, re.I)
        out.append(check("The wrong fact is corrected in the knowledge, or the reply names the contradiction",
                         "Corrected" in knowledge or named,
                         f"Corrected line: {'yes' if 'Corrected' in knowledge else 'no'}; reply: "
                         f"{named.group(0) if named else 'no contradiction named'}"))
        current = blocks(repo / P1 / "iterations.md").get("## Current", "")
        out.append(check("Current says the pipeline waits on the user",
                         re.search(r"wait\w*\s+(on|for)\s+(the\s+)?user", current, re.I), current[:160] or "no Current"))
    if case == 5:
        sales = csv_views(pr, False)
        out.append(check("No sales list CSV view was built", not sales, f"sales list CSV views: {list(sales) or 'none'}"))
        if not diff:
            out.append(check("If code changed, it is a move only: the CSV writer in reports/export.py, views.py importing "
                             "it, the same monthly CSV output, and no test assertion changed", True, "no code changed"))
        else:
            views_src = (repo / "reports/views.py").read_text()
            imports = re.search(r"from \.export import [^\n]*csv", views_src, re.I)
            old = probe(base)
            same = ({k: v for k, v in old["csv_views"].items()} == {k: v for k, v in pr["csv_views"].items()})
            asserts = lambda r: sorted(l.strip() for p in sorted((r / "tests").glob("*.py"))
                                       for l in p.read_text().splitlines() if "assert" in l)
            same_asserts = asserts(base) == asserts(repo)
            ok = pr.get("export_csv") and imports and same and same_asserts
            out.append(check("If code changed, it is a move only: the CSV writer in reports/export.py, views.py importing "
                             "it, the same monthly CSV output, and no test assertion changed", ok,
                             f"export CSV functions: {pr.get('export_csv')}; views imports it: {bool(imports)}; "
                             f"same CSV output: {same}; test assertions unchanged: {same_asserts}"))
    if case == 6:
        out += [code_changed, red_check(run)]
        v = next(iter(csv_views(pr, True).values()), {})
        f = v.get("finance", {}) if v else {}
        header = ((f.get("body") or "").splitlines() or [""])[0]
        disp = (f.get("headers") or {}).get("Content-Disposition", "")
        ok = "Amount (EUR)" in header and "sales-2026-8.csv" in disp and disp.startswith("inline")
        out.append(check("Only the first problem is fixed: the header says Amount (EUR), the file name and the inline "
                         "download are unchanged", ok, f"header: {header!r}; disposition: {disp!r}"))
        t = (repo / P1 / "iterations.md").read_text() if (repo / P1 / "iterations.md").exists() else ""
        st = statuses(t)
        es = [line for _, _, line in iterations(t)]
        header_done = [line for c, n, line in iterations(t)
                       if st.get((c, n)) == "DONE" and re.search(r"header|Amount \(EUR\)", line, re.I)]
        name = [e for e in es if re.search(r"file ?name|named|sales-2026-08|two-digit|zero|pad", e, re.I)]
        inline = [e for e in es if re.search(r"attachment|inline|opens the file|instead of (showing|opening)|"
                                             r"Content-Disposition|saves", e, re.I)]
        out.append(check("iterations.md has the header fix as a done iteration and the other two problems as iterations",
                         header_done and name and inline,
                         f"header done: {header_done[:1] or 'none'}; file name: {len(name)}; download: {len(inline)}"))
    if case == 7:
        dirs = sorted((repo / ".blueprints").glob("*/pipelines/01-*/")) if (repo / ".blueprints").exists() else []
        have = [d for d in dirs if (d / "iterations.md").exists() and (d / "knowledge.md").exists()]
        out.append(check("iterations.md and knowledge.md exist under .blueprints/<slug>/pipelines/01-<name>/", have,
                         f"{[str(d.relative_to(repo)) for d in dirs] or 'no pipeline folder'}"))
        t = (have[0] / "iterations.md").read_text() if have else ""
        its, st = iterations(t), statuses(t)
        not_planned = [f"{c}, iteration {n}: {st.get((c, n), 'no row')}" for c, n, _ in its if st.get((c, n)) != "PLANNED"]
        out.append(check("Every iteration in iterations.md has a PLANNED row in the status table", its and not not_planned,
                         f"{len(its)} iterations; not PLANNED: {not_planned or 'none'}"))
        out.append(check("Done when is written as checkable lines, not as scope numbers",
                         re.search(r"Done when", t) and not re.search(r"Done when:\s*scope\b", t, re.I),
                         (re.search(r"Done when[^\n]*(\n[^\n]+){0,3}", t) or [""])[0][:160] or "no Done when"))
        out.append(check("iterations.md has an Iteration size line", re.search(r"^Iteration size:", t, re.M),
                         (re.search(r"^Iteration size:[^\n]*", t, re.M) or ["no Iteration size line"])[0][:120]))
        recs = sorted(record_files(repo))
        named = [r for r in recs if have and r.parent.name == have[0].parent.parent.name and r.name == have[0].name + ".md"]
        out.append(check("The pipeline's record file is written, named like its folder: docs/tars-reports/<slug>/01-<name>.md",
                         named, f"{[str(r.relative_to(repo)) for r in recs] or 'no record file'}"))
        text = named[0].read_text().lower() if named else ""
        leaks = [w for w in ("nordwind", "/home/", "~/", "/downloads", "dana/") if w in text]
        out.append(check("Nothing sensitive in the record: no customer name, no home path", named and not leaks,
                         f"found: {leaks or 'none'}"))
        extra = [str(p.relative_to(repo)) for p in (repo / ".blueprints").rglob("*")
                 if p.name in ("02-scope.md", "03-workmap.md")] if (repo / ".blueprints").exists() else []
        out.append(check("No scope and no work map were written", not extra, f"{extra or 'none'}"))
        said = re.search(r"\.blueprints", reply) and re.search(r"ignor", reply, re.I)
        out.append(check("The reply says .blueprints is not ignored by git", said,
                         "mentions .blueprints and ignore" if said else "not said"))
    if case == 8:
        new = sorted(str(p.relative_to(repo)) for p in repo.rglob("*") if p.is_file()
                     and not (base / p.relative_to(repo)).exists() and "__pycache__" not in p.parts)
        out.append(check("No file written in the folder", not new, f"new files: {new or 'none'}"))
        out.append(check("The reply suggests a folder for the blueprint", re.search(r"folder|directory", reply, re.I),
                         "a folder is named" if re.search(r"folder|directory", reply, re.I) else "no folder named"))
    if case == 9:
        tools = json.load(open(run / "metrics.json")).get("tool_calls", {})
        agents = tools.get("Agent", 0) + tools.get("Task", 0)
        out.append(check("No review ran: no subagent was started", not agents, f"Agent tool calls: {agents}"))
        # A sentence that starts with "Commit" asks for one, but "Commit point:" only names where one fits.
        m = re.search(r"[^.\n]{0,80}(\b(suggest|recommend)\w*\s+(a\s+|you\s+)?commit|"
                      r"\b(you\s+(can|could|may|might|should)|please|worth)\s+commit|"
                      r"\bcommit\w*\b[^.\n]{0,60}\b(before the review|first)\b|"
                      r"\bbefore the review,?\s+commit\b|(?:^|(?<=[.!?]\s))\**commit\b(?!\s+point\b))[^.\n]{0,80}",
                      reply, re.I | re.M)
        out.append(check("The reply suggests a commit", m, m.group(0).strip() if m else "no commit suggested"))
        builtin = re.search(r"(?<![\w:-])/?code-review\b", reply.replace("mattpocock-skills:code-review", ""))
        matt = "mattpocock" in reply.lower()
        out.append(check("The reply names both review skills the session lists", builtin and matt,
                         f"built-in code-review: {bool(builtin)}; mattpocock-skills:code-review: {matt}"))
        current = blocks(repo / P1 / "iterations.md").get("## Current", "")
        out.append(check("Current says the pipeline waits on the user",
                         re.search(r"wait\w*\s+(on|for)\s+(the\s+)?user", current, re.I), current[:160] or "no Current"))
        record = repo / "docs/tars-reports/finance-exports/01-csv-downloads.md"
        state = re.search(r"^State:.*$", record.read_text(), re.M) if record.exists() else None
        out.append(check("The pipeline's record file says State built", state and state.group(0).startswith("State: built"),
                         state.group(0) if state else "no record file or no State line"))
    if case in (10, 11):
        out += [code_changed, red_check(run)]
        sales = csv_views(pr, False)
        v = next(iter(sales.values()), {})
        ok = (v and "csv" in (v.get("finance", {}).get("content_type") or "")
              and "csv" in (v.get("admin", {}).get("content_type") or "") and v.get("staff", {}).get("error") == "Forbidden")
        out.append(check("The sales list CSV exists for finance and admins and refuses staff", ok,
                         f"sales list CSV views: {list(sales) or 'none'}; staff: {v.get('staff') if v else '-'}"))
        out.append(done_and_moved(repo, "Sales list", "3.1"))
    if case == 10:
        new = new_lines(repo, base)
        empty =[l for l in new if re.search(r"\bempty\b", l, re.I) and not re.match(r"Iteration 3\.1:", l.lstrip("- "))]
        out.append(check("The empty-list test the user deferred is in a file, for a later iteration", empty,
                         empty[0][:200] if empty else "no new line about the empty list"))
        first = [l for l in new if re.search(r"\b(show|see|review|check|look)\w*", l, re.I)
                 and re.search(r"\b(before|first)\b", l, re.I) and re.search(r"\b(access|roles?)\b", l, re.I)]
        out.append(check("The user's 'show me the access test first' is in a file, for the page iteration", first,
                         first[0][:200] if first else "no new line asking to show the access test first"))
    if case == 11:
        def helper_files(root):
            return {str(p.relative_to(root)): p.read_bytes() for p in [root / "tests/helpers.py", *(root / "tests/data").glob("*")]
                    if p.is_file()}
        same = helper_files(repo) == helper_files(base)
        out.append(check("tests/helpers.py and tests/data are as the fixture left them: the fix is not in this iteration",
                         same, "unchanged" if same else f"now: {sorted(helper_files(repo))}; "
                         f"helpers.py changed: {helper_files(repo).get('tests/helpers.py') != helper_files(base).get('tests/helpers.py')}"))
        noted = [l for l in new_lines(repo, base) if re.search(r"sample_sales|helpers\.py|sales\.json|sample data", l, re.I)
                 and not re.match(r"Iteration 3\.1:", l.lstrip("- "))]
        out.append(check("The broken sample_sales() is in a blueprint file, so a compaction does not lose it", noted,
                         noted[0][:200] if noted else "no new line about the broken helper"))
    if case == 12:
        out += [code_changed, red_check(run)]
        v = next(iter(csv_views(pr, True).values()), {})
        ok = (v and "csv" in (v.get("finance", {}).get("content_type") or "")
              and "csv" in (v.get("admin", {}).get("content_type") or "") and v.get("staff", {}).get("error") == "Forbidden")
        out.append(check("The monthly CSV exists for finance and admins and refuses staff", ok,
                         f"monthly CSV views: {list(csv_views(pr, True)) or 'none'}; staff: {v.get('staff') if v else '-'}"))
        out.append(done_and_moved(repo, "Monthly report", "2.1"))
        record = repo / "docs/tars-reports/finance-exports/01-csv-downloads.md"
        b = blocks(record)
        made = b.get("## What was built", "")
        out.append(check("The pipeline's record file's What was built gains the monthly CSV download",
                         re.search(r"monthly", made, re.I) and re.search(r"CSV", made), made[:200] or "no What was built"))
        built = b.get("## Build decisions", "")
        out.append(check("The decision reaches the pipeline's record file, Build decisions: each CSV starts with a byte order mark",
                         re.search(r"\bBOM\b|byte order mark|\\ufeff", built, re.I), built[:200] or "no Build decisions"))
        text = record.read_text() if record.exists() else ""
        entries = re.split(r"\n(?=- )", text)
        trap = [e for e in entries if re.search(r"Excel", e) and re.search(r"1252|Ã¼|\bBOM\b|byte order|UTF-8", e, re.I)]
        out.append(check("The trap reaches the pipeline's record file, in any section: Excel misreads a UTF-8 CSV without a byte order mark",
                         trap, trap[0][:200] if trap else "no entry names Excel with the encoding"))
        state = re.search(r"^State:.*$", text, re.M)
        out.append(check("The pipeline's record file's State stays in progress",
                         state and state.group(0).startswith("State: in progress"), state.group(0) if state else "no State line"))
        labels = re.findall(r"\bQ\d+\b|\b[Ii]teration \d", text)
        out.append(check("No question numbers or iteration labels in the pipeline's record file", text and not labels,
                         f"found: {labels[:5] or 'none'}"))
    if case == 14:
        out += [code_changed, red_check(run)]
        monthly = csv_views(pr, True)
        v = next(iter(monthly.values()), {})
        body = (v.get("finance", {}).get("body") or "") if v else ""
        ok = (v and "csv" in (v.get("finance", {}).get("content_type") or "")
              and "csv" in (v.get("admin", {}).get("content_type") or "") and v.get("staff", {}).get("error") == "Forbidden"
              and body.startswith("\ufeff"))
        out.append(check("The monthly CSV exists for finance and admins, refuses staff and starts with the byte order mark",
                         ok, f"monthly CSV views: {list(monthly) or 'none'}; finance's file starts with {body[:12]!r}; "
                         f"staff: {v.get('staff') if v else '-'}"))
        out.append(done_and_moved(repo, "Monthly report", "2.1"))
        new = new_lines(repo, base, "*knowledge.md")
        decision = [l for l in new if re.search(r"\bBOM\b|byte order mark|\\ufeff|utf-8-sig", l, re.I) and "Decided" in l]
        out.append(check("The decision reaches the knowledge: each CSV starts with a byte order mark", decision,
                         decision[0][:200] if decision else "no new decision about the byte order mark"))
        # Counted, so that a decision rewritten or moved with the fixture's own number does not count as a new one.
        numbers = lambda root: Counter(re.findall(r"\bQ\d+\b", " ".join(p.read_text() for p in (root / BP).rglob("*knowledge.md"))))
        added = numbers(repo) - numbers(base)
        tagged = [l for l in new if re.search(r"\bQ\d+\b", l)]
        out.append(check("No new question number in the knowledge", not added,
                         f"added: {sorted(added) or 'none'}; in: {[l[:160] for l in tagged[:2]] or '-'}"))
        removed = numbers(base) - numbers(repo)
        out.append(check("No question number already in the knowledge is taken off", not removed,
                         f"taken off: {sorted(removed) or 'none'}"))
        comments = new_comments(repo, base)
        why = [c for c in comments if re.search(r"Excel|byte order|\bBOM\b|1252|UTF-8|ufeff", c, re.I)]
        out.append(check("A code comment gives the byte order mark's why", why,
                         why[0][:200] if why else f"new comments: {comments[:3] or 'none'}"))
        numbered = [c for c in comments if re.search(r"\bQ\d+\b", c)]
        out.append(check("No question number in the new code comments", not numbered,
                         f"found: {[c[:160] for c in numbered[:2]]}" if numbered else f"{len(comments)} new comments, none numbered"))
    if case == 13:
        current = blocks(repo / ".blueprints/region-filter/pipelines/01-region-filter/iterations.md").get("## Current", "")
        # The pipeline called done ("Pipeline 1 is done"), never "Done when"; a wait about another item does not count.
        done = re.search(r"\bpipeline\b[^.\n]{0,40}?(?<!not )\bdone\b(?!\s+when)", current, re.I)
        out.append(check("Current says the pipeline is done", done, current[:160] or "no Current"))
        record = repo / "docs/tars-reports/region-filter/01-region-filter.md"
        state = re.search(r"^State:.*$", record.read_text(), re.M) if record.exists() else None
        out.append(check("The pipeline's record file's State is done", state and state.group(0).startswith("State: done"),
                         state.group(0) if state else "no record file or no State line"))
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
