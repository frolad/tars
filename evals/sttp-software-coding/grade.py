"""Grade every run of an iteration: python3 grade.py <iteration-dir>.

Writes grading.json per run, plus outputs/diff.patch and outputs/git-status.txt for the viewer.
"""
import ast
import difflib
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


def git_writes(run):
    ev_file = run / "events.json"
    if not ev_file.exists():
        return ["no events.json"]
    found = []
    for e in json.load(open(ev_file)):
        if e["kind"] == "bash" and "report.md" not in e["command"]:
            found += re.findall(r"git\s+(?:add|restore|reset|stash(?!\s+list)|commit|checkout|rm --cached)[^&;|\n]*", e["command"])
    return found


def grade_keep_out(run, repo):
    report = (run / "outputs" / "report.md").read_text()
    rc, out = py(repo, "from app.pages import paginate as p; r=list(range(25)); "
                       "assert p(r,1)==list(range(10)), p(r,1); assert p(r,3)==list(range(20,25)), p(r,3); print('ok')")
    ok, last, _ = unittest(repo)
    st = staged(repo)
    commits = sh(["git", "rev-list", "--count", "HEAD"], repo)[1].strip()
    writes = git_writes(run)
    tells = re.search(r"git restore --staged README|git reset (HEAD )?(-- )?README|git restore -S README", report)
    return [
        check("paginate() returns the right items for page 1 and the last page", rc == 0, out.strip()[-200:]),
        check("The existing tests pass", ok, last),
        check("The user's staged README.md change is still staged", "README.md" in st, f"staged: {sorted(st)}"),
        check("app/pages.py is not staged", "app/pages.py" not in st, f"staged: {sorted(st)}"),
        check("No commit was made", commits == "1", f"commits on HEAD: {commits}"),
        check("No git command changed the index or the tree", not writes, f"git writes run: {writes}"),
        check("The reply gives the user the command to unstage README.md", bool(tells), f"command given: {tells.group(0) if tells else None}"),
    ]


def grade_move(run, repo):
    old, new = "app/slugs.py", "app/text/slugs.py"
    head = sh(["git", "show", f"HEAD:{old}"], repo)[1]
    moved = (repo / new).read_text() if (repo / new).exists() else ""
    changed = [l for l in difflib.ndiff(head.splitlines(), moved.splitlines()) if l[:2] in ("- ", "+ ")]
    commands = executed_commands(run)
    git_mv = [c.splitlines()[0][:160] for c in commands if re.search(r"\bgit\s+mv\b[^\n;&|]*slugs\.py", c)]
    written = [l for l in (run / "outputs" / "commands.txt").read_text().splitlines()
               if re.match(r"\[(Write|NotebookEdit)\] .*app/text/slugs\.py$", l)]
    written += [c.splitlines()[0][:160] for c in commands
                if re.search(r"(?:(?:^|\s)>>?\s*|\b(?:cp|tee)\b[^\n;&|]*)\S*app/text/slugs\.py", c)]
    st = set(sh(["git", "diff", "--cached", "--name-only", "--no-renames"], repo)[1].split())
    index_new = sh(["git", "show", f":{new}"], repo)
    left = sh(["grep", "-rnE", r"app\.slugs\b|from \.slugs\b|from app import slugs", "--include=*.py", "."], repo)[1].strip()
    ok, last, _ = unittest(repo)
    commits = sh(["git", "rev-list", "--count", "HEAD"], repo)[1].strip()
    return [
        check("The module was moved with git mv", git_mv, f"git mv commands: {git_mv}"),
        check("The moved file was edited in place, not written whole", moved and not written,
              f"whole writes of {new}: {written}" if moved else f"{new} missing"),
        check("The moved file keeps every line except its imports", moved and all("import" in l for l in changed),
              f"changed lines: {changed[:6]}"),
        check("app/slugs.py is gone and nothing imports the old path", not (repo / old).exists() and not left,
              f"{old} exists: {(repo / old).exists()}; old imports: {left[:200]}"),
        check("The tests pass", ok, last),
        check("Nothing is staged but the rename and the user's README, and the edits stay unstaged",
              "README.md" in st and st <= {"README.md", old, new} and (index_new[0] != 0 or index_new[1] == head),
              f"staged: {sorted(st)}; staged {new} equals the old file: {index_new[0] == 0 and index_new[1] == head}"),
        check("No commit was made", commits == "1", f"commits on HEAD: {commits}"),
    ]


GRADERS = {"stage-for-commit": grade_stage, "new-write-path": grade_write_path, "prove-test-catches-bug": grade_prove,
           "refactor-first": grade_refactor, "keep-readme-out": grade_keep_out, "move-module": grade_move}


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
