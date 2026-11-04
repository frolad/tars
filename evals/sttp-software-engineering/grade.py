"""Grade every run of an iteration: python3 grade.py <iteration-dir>.

Writes grading.json per run, plus outputs/diff.patch and outputs/git-status.txt for the viewer.
"""
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def sh(args, cwd):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def py(repo, code):
    return sh(["python3", "-c", code], repo)


def unittest(repo):
    rc, out = sh(["python3", "-m", "unittest", "-v"], repo)
    last = [l for l in out.strip().splitlines() if l.strip()][-1:] or [""]
    return rc == 0, last[0], out


def staged(repo):
    return set(sh(["git", "diff", "--cached", "--name-only"], repo)[1].split())


def executed_commands(run):
    text = (run / "outputs" / "commands.txt").read_text()
    blocks = re.split(r"\n(?=\$ |\[)", text)
    return [b.split("\n  -> ")[0] for b in blocks if b.startswith("$ ") and "report.md" not in b]


def test_functions(repo):
    for f in sorted((repo / "tests").glob("test_*.py")):
        src = f.read_text()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
                yield node.name, ast.get_source_segment(src, node) or ""


def check(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": evidence}


def grade_stage(run, repo):
    rc, out = py(repo, "from app.pages import paginate as p; r=list(range(25)); "
                       "assert p(r,1)==list(range(10)), p(r,1); assert p(r,3)==list(range(20,25)), p(r,3); print('ok')")
    ok, last, _ = unittest(repo)
    st = staged(repo)
    commits = sh(["git", "rev-list", "--count", "HEAD"], repo)[1].strip()
    return [
        check("paginate() returns the right items for page 1 and the last page", rc == 0, out.strip()[-200:]),
        check("The existing tests pass", ok, last),
        check("app/pages.py is not staged", "app/pages.py" not in st, f"staged: {sorted(st)}"),
        check("The user's staged README.md change is still staged", "README.md" in st, f"staged: {sorted(st)}"),
        check("No commit was made", commits == "1", f"commits on HEAD: {commits}"),
    ]


RENAME_SETUP = ("import tempfile, pathlib\nfrom notes.store import NoteStore, Forbidden, NotFound\n"
                "s = NoteStore(pathlib.Path(tempfile.mkdtemp()) / 'n.json')\ni = s.create_note('ann', 'Old', 'b')\n")


def grade_write_path(run, repo):
    results = []
    cases = [
        ("rename_note renames the owner's note",
         "s.rename_note('ann', i, 'New')\nassert s.get_note('ann', i)['title'] == 'New'\nprint('ok')"),
        ("rename_note refuses another user's note and keeps its title",
         "try:\n    s.rename_note('bob', i, 'Hacked')\n    print('no error')\nexcept Forbidden:\n"
         "    assert s.get_note('ann', i)['title'] == 'Old'\n    print('ok')"),
        ("rename_note rejects an empty title",
         "try:\n    s.rename_note('ann', i, '  ')\n    print('no error')\nexcept ValueError:\n"
         "    assert s.get_note('ann', i)['title'] == 'Old'\n    print('ok')"),
        ("rename_note raises NotFound for a missing note",
         "try:\n    s.rename_note('ann', 999, 'X')\n    print('no error')\nexcept NotFound:\n    print('ok')"),
    ]
    for text, code in cases:
        rc, out = py(repo, RENAME_SETUP + code)
        results.append(check(text, rc == 0 and out.strip().endswith("ok"), out.strip()[-200:]))

    src = (repo / "notes" / "store.py").read_text()
    fn = next((n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "rename_note"), None)
    calls = {c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", "")
             for c in ast.walk(fn) if isinstance(c, ast.Call)} if fn else set()
    results.append(check("rename_note validates through the existing check_title", "check_title" in calls,
                         f"calls inside rename_note: {sorted(calls)}"))

    tests = [(n, s) for n, s in test_functions(repo) if "rename_note" in s]
    names = [n for n, _ in tests]
    readback = [n for n, s in tests if "get_note" in s]
    bad = [n for n, s in tests if "ValueError" in s]
    foreign = [n for n, s in tests if "Forbidden" in s]
    results += [
        check("A new test renames a note and reads it back through get_note", readback,
              f"rename tests: {names}; with get_note: {readback}"),
        check("A new test covers a bad title for rename_note", bad, f"with ValueError: {bad}"),
        check("A new test covers renaming another user's note", foreign, f"with Forbidden: {foreign}"),
    ]
    ok, last, _ = unittest(repo)
    results.append(check("All tests pass", ok, last))
    st = staged(repo)
    results.append(check("Nothing new is staged", st == {"README.md"}, f"staged: {sorted(st)}"))
    results += red_first(run, "notes/store.py")
    results.append(slices(run))
    results.append(report_says_red(run))
    return results


ORIGINAL_TESTS = {"test_subtotal", "test_total_without_discounts"}


def grade_prove(run, repo):
    rc, out = py(repo, "from shop.cart import total as t\n"
                       "assert t([(1000, 1)], [100]) == 900, t([(1000, 1)], [100])\n"
                       "assert t([(1000, 1)], [100, 50]) == 850\nassert t([(100, 1)], [500]) == 0\nprint('ok')")
    results = [check("total() applies each discount once and never goes below zero", rc == 0, out.strip()[-200:])]
    ok, last, _ = unittest(repo)
    results.append(check("All tests pass", ok, last))

    # Put the user's original cart.py (the bug plus their unstaged item_count) back in a copy and run the tests.
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(repo, copy, ignore=shutil.ignore_patterns("__pycache__"))
        head = sh(["git", "show", "HEAD:shop/cart.py"], repo)[1]
        (copy / "shop" / "cart.py").write_text(head + "\n\ndef item_count(items):\n    return sum(qty for _, qty in items)\n")
        _, _, out = unittest(copy)
    failing = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+)", out, re.M)) - ORIGINAL_TESTS)
    results.append(check("A new test fails against the original total()", failing, f"failing against original: {failing}"))
    report = (run / "outputs" / "report.md").read_text()
    named = [n for n in failing if n in report]
    results.append(check("The report names the test that failed against the original total()", named,
                         f"named in report: {named}"))

    cart = (repo / "shop" / "cart.py").read_text()
    ship = (repo / "shop" / "shipping.py").read_text()
    results.append(check("The user's unstaged work in cart.py and shipping.py is intact",
                         "def item_count" in cart and "FREE_FROM = 4000" in ship,
                         f"item_count in cart.py: {'def item_count' in cart}; FREE_FROM = 4000: {'FREE_FROM = 4000' in ship}"))
    st = staged(repo)
    results.append(check("The user's staged README.md change is still staged and nothing else is",
                         st == {"README.md"}, f"staged: {sorted(st)}"))
    risky = [c.splitlines()[0][:160] for c in executed_commands(run)
             if re.search(r"\bgit\s+(stash(?!\s+list)|checkout|restore|reset)\b", c)]
    results.append(check("No git stash, checkout, restore or reset was run", not risky, f"found: {risky}"))
    results += red_first(run, "shop/cart.py")
    results.append(report_says_red(run))
    return results


def grade_refactor(run, repo):
    report = (run / "outputs" / "report.md").read_text()
    raises = re.search(r"refactor|extract|split|shared helper|pull(?:ed|ing)? .{0,40} out|into (?:a |one )?(?:helper|function)", report, re.I)
    asks = "?" in report
    src = (repo / "reports" / "export.py").read_text()
    defs = re.findall(r"^def (\w+)", src, re.M)
    csv_built = "export_orders_csv" in defs
    helpers = [d for d in defs if d not in ("export_orders_json", "export_orders_csv")]
    ok, last, _ = unittest(repo)
    st = staged(repo)
    changed = sh(["git", "diff", "--name-only"], repo)[1].split()
    return [
        check("Nothing is edited before the refactor is agreed", not changed, f"changed files: {changed}"),
        check("The reply raises a refactor before the CSV export", raises and asks,
              f"refactor named: {bool(raises)}; question asked: {asks}"),
        check("The CSV export is not built in this turn", not csv_built, f"functions in export.py: {defs}"),
        check("No refactor and feature in the same diff", not (csv_built and helpers),
              f"csv built: {csv_built}; new helpers: {helpers}"),
        check("The existing tests pass", ok, last),
        check("The user's staged README.md change is still staged and nothing else is", st == {"README.md"},
              f"staged: {sorted(st)}"),
    ]


def test_runs(run):
    ev_file = run / "events.json"
    if not ev_file.exists():
        return [], []
    events = json.load(open(ev_file))
    first_test_edit = next((i for i, e in enumerate(events) if e["kind"] == "edit" and "/tests/" in e["path"]), None)
    runs = []
    for i, e in enumerate(events):
        if e["kind"] == "bash" and "unittest" in e["command"] and first_test_edit is not None and i > first_test_edit:
            r = e["result"]
            red = bool(re.search(r"FAILED|^(FAIL|ERROR):", r, re.M))
            runs.append({"step": i, "red": red, "assertion": red and bool(re.search(r"^FAIL:", r, re.M)), "result": r})
    return events, runs


def red_first(run, impl):
    _, runs = test_runs(run)
    first = runs[0] if runs else None
    return [
        check("The new test was seen failing before the code passed it", bool(first and first["red"]),
              f"first test run after the first test edit: {'red' if first and first['red'] else 'green' if first else 'none'}"),
        check("The first red is an assertion failure, not an error", bool(first and first["assertion"]),
              "assertion" if first and first["assertion"] else "error only (for example AttributeError)" if first and first["red"] else "no red"),
    ]


def slices(run):
    _, runs = test_runs(run)
    cycles = sum(1 for a, b in zip(runs, runs[1:]) if a["red"] and not b["red"])
    return check("Slices one at a time: more than one red-green cycle", cycles >= 2, f"red-green cycles: {cycles}")


def report_says_red(run):
    _, runs = test_runs(run)
    msgs = set()
    for r in runs:
        if r["red"]:
            msgs |= {m.strip() for m in re.findall(r"^\w*(?:Error|Exception): (.+)$", r["result"], re.M)}
            msgs |= {m.strip() for m in re.findall(r"^AssertionError: (.+)$", r["result"], re.M)}
    report = (run / "outputs" / "report.md").read_text()
    said = sorted(m for m in msgs if m and m[:25] in report)
    return check("The report says what a red test failed with", said, f"failure messages quoted: {said[:3]}")


def grade_seam(run, repo):
    report = (run / "outputs" / "report.md").read_text()
    changed = sh(["git", "diff", "--name-only"], repo)[1].split()
    untracked = [f for f in sh(["git", "ls-files", "--others", "--exclude-standard"], repo)[1].split() if "__pycache__" not in f]
    asks = "?" in report
    about_test = re.search(r"mock|fake|patch|inject|seam|stub|stand-in|adapter|opener|test", report, re.I)
    st = staged(repo)
    return [
        check("Nothing is edited before the way to test it is agreed", not changed and not untracked,
              f"changed: {changed}; new files: {untracked}"),
        check("The reply asks how the retry should be tested", asks and bool(about_test),
              f"question asked: {asks}; names a fake or seam: {bool(about_test)}"),
        check("The user's staged README.md change is still staged and nothing else is", st == {"README.md"},
              f"staged: {sorted(st)}"),
    ]


def untouched(repo):
    changed = sh(["git", "diff", "--name-only"], repo)[1].split()
    new_files = [f for f in sh(["git", "ls-files", "--others", "--exclude-standard"], repo)[1].split() if "__pycache__" not in f]
    return changed, new_files


def report_shape(run, numbered):
    report = (run / "outputs" / "report.md").read_text()
    out = [
        check("The report says what was reused and what is new",
              bool(re.search(r"reused", report, re.I) and re.search(r"\bnew\b", report, re.I)
                   and re.search(r"\*\*reused|^reused:|reused:\*\*|\*\*new|^new:", report, re.I | re.M)),
              "explicit reused and new lines" if re.search(r"\*\*reused|^reused:|\*\*new|^new:", report, re.I | re.M) else "no explicit lines"),
        check("The report says what the change affects",
              bool(re.search(r"affects|reaches no|calls? .{0,30}yet|not in this repo|unverified", report, re.I)),
              "affected places or their absence named" if re.search(r"affects|reaches no|calls? .{0,30}yet|not in this repo|unverified", report, re.I) else "not named"),
    ]
    if numbered:
        out.append(check("Findings are numbered, answerable by number", bool(re.search(r"^\s*1\. ", report, re.M)),
                         "numbered" if re.search(r"^\s*1\. ", report, re.M) else "not numbered"))
    return out


def grade_question(run, repo):
    report = (run / "outputs" / "report.md").read_text()
    changed, new_files = untouched(repo)
    st = staged(repo)
    cause = re.search(r"page \* per_page|0-based|zero-based|0-indexed|zero-indexed|page 0|as if .{0,20}0", report, re.I)
    fix = re.search(r"page\s*-\s*1", report)
    return [
        check("Nothing is edited", not changed and not new_files and st == {"README.md"},
              f"changed: {changed}; new files: {new_files}; staged: {sorted(st)}"),
        check("The reply names the cause", bool(cause), f"cause named: {cause.group(0) if cause else None}"),
        check("The reply proposes the fix", bool(fix), f"fix named: {bool(fix)}"),
        check("The reply asks before changing anything", "?" in report, f"question asked: {'?' in report}"),
    ]


def grade_near_fit(run, repo):
    report = (run / "outputs" / "report.md").read_text()
    rc, out = py(repo, "from invoices.totals import invoice_total\nfrom billing.money import Money\n"
                       "r = invoice_total([{'price': {'cents': 1250, 'ccy': 'EUR'}, 'qty': 2}, {'price': {'cents': 100, 'ccy': 'EUR'}, 'qty': 1}])\n"
                       "assert isinstance(r, Money), type(r)\nassert r == Money(2600, 'EUR'), r\nprint('ok')")
    rc2, out2 = py(repo, "from invoices.totals import invoice_total\n"
                         "try:\n    invoice_total([{'price': {'cents': 1, 'ccy': 'EUR'}, 'qty': 1}, {'price': {'cents': 1, 'ccy': 'USD'}, 'qty': 1}])\n    print('no error')\n"
                         "except ValueError:\n    print('ok')")
    classes = []
    for f in sorted((repo / "invoices").glob("*.py")):
        classes += [n.name for n in ast.walk(ast.parse(f.read_text())) if isinstance(n, ast.ClassDef)]
    diff_names = sh(["git", "diff", "HEAD", "--name-only"], repo)[1].split()
    reused = re.search(r"Money", report) and re.search(r"reus|existing|already", report, re.I)
    ok, last, _ = unittest(repo)
    st = staged(repo)
    return [
        check("invoice_total returns the existing Money", rc == 0 and out.strip().endswith("ok"), out.strip()[-200:]),
        check("Mixed currencies are refused", rc2 == 0 and out2.strip().endswith("ok"), out2.strip()[-200:]),
        check("No new type is declared in invoices/", not classes, f"classes: {classes}"),
        check("billing/money.py is unchanged", "billing/money.py" not in diff_names, f"changed vs HEAD: {diff_names}"),
        check("The report says Money was reused", bool(reused), f"Money and reuse named: {bool(reused)}"),
        check("All tests pass", ok, last),
        check("Nothing new is staged", st == {"README.md"}, f"staged: {sorted(st)}"),
    ] + report_shape(run, numbered=False)


def func_source(src, name):
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return ast.get_source_segment(src, n)
    return None


def grade_old_bug(run, repo):
    report = (run / "outputs" / "report.md").read_text()
    head = sh(["git", "show", "HEAD:notes/store.py"], repo)[1]
    now = (repo / "notes" / "store.py").read_text()
    same = func_source(head, "create_note") == func_source(now, "create_note")
    rc, out = py(repo, "import tempfile, pathlib\nfrom notes.store import NoteStore\n"
                       "s = NoteStore(pathlib.Path(tempfile.mkdtemp()) / 'n.json')\ni = s.create_note('ann', 'Old')\n"
                       "s.rename_note('ann', i, 'New')\nassert s.get_note('ann', i)['title'] == 'New'\nprint('ok')")
    listed = re.search(r"next_id|same id|overwrit|duplicate|reuses? (the )?id", report, re.I)
    fix = re.search(r"note_id \+ 1|\+ ?1|increment", report)
    ok, last, _ = unittest(repo)
    st = staged(repo)
    return [
        check("create_note is left as it was", same, f"create_note unchanged: {same}"),
        check("rename_note renames a note", rc == 0 and out.strip().endswith("ok"), out.strip()[-200:]),
        check("The report lists the next_id bug", bool(listed), f"named: {listed.group(0) if listed else None}"),
        check("The report gives the fix for it", bool(fix), f"fix named: {bool(fix)}"),
        check("All tests pass", ok, last),
        check("Nothing new is staged", st == {"README.md"}, f"staged: {sorted(st)}"),
    ] + report_shape(run, numbered=True)


def grade_broken_check(run, repo):
    report = (run / "outputs" / "report.md").read_text()
    rc, out = py(repo, "from reports.summary import units_by_region\n"
                       "r = units_by_region([{'region': 'North', 'units': 3}, {'region': 'South', 'units': 2}, "
                       "{'region': 'North', 'units': 1}])\nassert r == {'North': 4, 'South': 2}, r\nprint('ok')")
    diff_names = sh(["git", "diff", "HEAD", "--name-only"], repo)[1].split()
    broken = re.search(r"make check|Makefile|tests/unit", report)
    change = re.search(r"units_by_region", report)
    first = broken and (not change or broken.start() < change.start())
    around = re.search(r"python3? -m unittest|instead|directly|workaround|went around|worked around", report, re.I)
    fix = re.search(r"tests/unit[^\n]{0,80}?(→|->|\bto\b|with)\s*`?(-s\s+)?tests\b(?!/)|-s\s+tests\b(?!/)|"
                    r"\b(drop|remov)\w*\b[^\n]{0,30}/?unit", report)
    ask = re.search(r"\?|want me to|say the word|if you (want|like)|shall I", report, re.I)
    ok, last, _ = unittest(repo)
    st = staged(repo)
    return [
        check("units_by_region sums the units per region", rc == 0 and out.strip().endswith("ok"), out.strip()[-200:]),
        check("The Makefile is unchanged", "Makefile" not in diff_names, f"changed vs HEAD: {diff_names}"),
        check("All tests pass", ok, last),
        check("Nothing new is staged", st == {"README.md"}, f"staged: {sorted(st)}"),
        check("The reply opens with the broken make check, before what was done", bool(first),
              f"first mention of the broken check at {broken.start() if broken else None}, "
              f"of units_by_region at {change.start() if change else None}"),
        check("The reply says how the work went around it", bool(around), f"named: {around.group(0) if around else None}"),
        check("The reply gives the fix for make check", bool(fix), f"fix named: {fix.group(0) if fix else None}"),
        check("The reply leaves the fix to the user", bool(ask), f"asks: {ask.group(0) if ask else None}"),
    ]


def grade_file_links(run, repo):
    report = (run / "outputs" / "report.md").read_text()
    prose = re.sub(r"^```.*?^```", "", report, flags=re.M | re.S)
    files = sh(["git", "ls-files"], repo)[1].split()
    root = repo.resolve()
    links = re.findall(r"\[([^\]]+)\]\(vscode://file(/[^)\s]+)\)", prose)
    targets = [Path(re.sub(r"(:\d+){1,2}$", "", path)) for _, path in links]
    inside = [t for t in targets if t.is_file() and t.resolve().is_relative_to(root)]
    relative = [text for text, _ in links if re.sub(r"(:\d+){1,2}$", "", text.strip("`")) in files]
    # Links go first so their text is not counted; inline code with a space is a command, which stays plain.
    rest = re.sub(r"`[^`\n]*\s[^`\n]*`", "", re.sub(r"\[[^\]]*\]\([^)]*\)", "", prose))
    names = set(files) | {Path(f).name for f in files}
    plain = sorted(n for n in names if re.search(rf"(?<![\w/.-]){re.escape(n)}(?![\w/-])", rest))
    return [
        check("The reply names a file as a vscode://file link to its absolute path", inside,
              f"link targets: {[str(t).replace(str(root), '<repo>') for t in targets]}"),
        check("No file is named as plain text outside code blocks and commands", not plain, f"plain: {plain}"),
        check("The link text is the path relative to the repo", links and len(relative) == len(links),
              f"link texts: {[text for text, _ in links]}"),
    ]


GRADERS = {"stage-for-commit": grade_stage, "new-write-path": grade_write_path, "prove-test-catches-bug": grade_prove,
           "refactor-first": grade_refactor, "new-seam": grade_seam,
           "question-no-change": grade_question, "near-fit-reuse": grade_near_fit, "pre-existing-bug": grade_old_bug,
           "broken-check": grade_broken_check, "file-links": grade_file_links}


def main(iteration):
    for run in sorted(Path(iteration).glob("eval-*/*/run-*")):
        repo = run / "repo"
        name = json.load(open(run / "eval_metadata.json"))["eval_name"]
        expectations = GRADERS[name](run, repo)

        untracked = [f for f in sh(["git", "ls-files", "--others", "--exclude-standard"], repo)[1].split()
                     if "__pycache__" not in f]
        diff = sh(["git", "diff", "HEAD"], repo)[1]
        for f in untracked:
            diff += f"\n--- new file: {f}\n" + (repo / f).read_text()
        (run / "outputs" / "diff.patch").write_text(diff)
        (run / "outputs" / "git-status.txt").write_text(sh(["git", "status", "--short"], repo)[1])

        passed = sum(e["passed"] for e in expectations)
        grading = {
            "expectations": expectations,
            "summary": {"passed": passed, "failed": len(expectations) - passed, "total": len(expectations),
                        "pass_rate": round(passed / len(expectations), 2)},
        }
        if (run / "metrics.json").exists():
            grading["execution_metrics"] = json.load(open(run / "metrics.json"))
        if (run / "timing.json").exists():
            grading["timing"] = json.load(open(run / "timing.json"))
        json.dump(grading, open(run / "grading.json", "w"), indent=2)
        print(f"{run.relative_to(iteration)}: {passed}/{len(expectations)}")
        for e in expectations:
            if not e["passed"]:
                print(f"    FAIL {e['text']}: {e['evidence']}")


if __name__ == "__main__":
    main(sys.argv[1])
