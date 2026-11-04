"""Grade every run of an iteration: python3 grade.py <iteration-dir>.

Needs per run what workshop-forge's grader needs: outputs/final.md, and optionally judgement.json ([{"text", "passed",
"evidence"}], the checks graded by reading the reply). Writes grading.json per run. Reuses the helpers of
`../workshop-forge/grade.py`.
"""
import ast
import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("forge_grade", HERE.parent / "workshop-forge/grade.py")
fg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fg)
check, git_state, tests_pass = fg.check, fg.git_state, fg.tests_pass
EVALS = {e["id"]: e for e in json.load(open(HERE / "evals.json"))["evals"]}
SKILL = ".claude/skills/release/SKILL.md"
LEFT_OUT = ["uv.lock", "LICENSE", "docs/api.md", "CHANGELOG.md", "tests/fixtures/notes.md"]


def fresh(fixture):
    tmp = tempfile.TemporaryDirectory()
    repo = Path(tmp.name) / "repo"
    subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), fixture, str(repo)], check=True, capture_output=True)
    return tmp, repo


def changed(base, repo):
    """The files that differ between the fresh fixture and the run's repo, outside .git and caches."""
    p = subprocess.run(["diff", "-rq", "-x", ".git", "-x", "__pycache__", str(base), str(repo)],
                       capture_output=True, text=True)
    out = []
    for line in p.stdout.splitlines():
        m = re.match(r"Files (\S+) and \S+ differ", line)
        if m:
            out.append(str(Path(m.group(1)).relative_to(base)))
        else:
            out.append(line.replace(str(base), "<fresh>").replace(str(repo), "<repo>"))
    return sorted(out)


def code_tree(src):
    """The syntax tree of a module with its docstrings taken out."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) and isinstance(
                getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree)


def comments(src):
    return [t.string for t in tokenize.generate_tokens(io.StringIO(src).readline) if t.type == tokenize.COMMENT]


def missing(text, patterns):
    """The patterns, regexes matched without case, that the text does not hold."""
    return [p for p in patterns if not re.search(p, text, re.I | re.S)]


def present(text, patterns):
    return [p for p in patterns if re.search(p, text, re.I)]


def grade(run, case):
    reply = (run / "outputs/final.md").read_text()
    repo = run / "repo"
    tmp, base = fresh(EVALS[case]["fixture"])
    state, want = git_state(repo), git_state(base)
    out = [check("Git untouched: same commits and branches as the fixture, clean index, no stash, no extra worktree",
                 state == want, json.dumps(state) if state != want else "same as the fixture")]
    diff = changed(base, repo)
    offer = re.search(r"[^.\n]{0,60}\b((shall|should|can|may) I (commit|stage)|I('ll| will) (commit|stage)|want me to "
                      r"(commit|stage))[^.\n]{0,40}", reply, re.I)
    no_commit = check("Does not commit or offer to commit", not offer and state == want,
                      offer.group(0).strip() if offer else "no commit, no offer")

    if case == 1:
        out.append(check("Nothing written: no file created or changed in the repo", not diff, diff or "none"))
        named = [f for f in LEFT_OUT if f not in reply]
        out.append(check("Names the files left out: uv.lock, LICENSE, docs/api.md, CHANGELOG.md and "
                         "tests/fixtures/notes.md", not named, f"not named: {named}" if named else "all named"))

    if case == 2:
        ok, last = tests_pass(repo)
        out.append(check("The tests pass", ok, last))
        want_files = ["README.md", "brewlog/cli.py", "docs/usage.md"]
        out.append(check("Only README.md, docs/usage.md and brewlog/cli.py changed", diff == want_files,
                         f"changed: {diff}"))
        same = (repo / SKILL).read_text() == (base / SKILL).read_text()
        out.append(check("The release skill, left out by the user, is unchanged", same, "unchanged" if same else "changed"))
        src, old = (repo / "brewlog/cli.py").read_text(), (base / "brewlog/cli.py").read_text()
        try:
            same_code = code_tree(src) == code_tree(old)
        except SyntaxError as e:
            same_code = False
        out.append(check("The code is unchanged: the syntax tree without docstrings is identical, the printed messages "
                         "included", same_code, "identical" if same_code else "differs"))
        try:
            c = comments(src)
            gone = [x for x in ("create the table", "compute the cutoff", "ABV formula", "increment the counter",
                                "=====") if any(x in k for k in c)]
            why = any("fermentation" in k for k in c)
            found = f"left: {gone}; why comment kept: {why}"
        except (tokenize.TokenError, SyntaxError) as e:
            gone, why, found = None, False, f"brewlog/cli.py does not tokenize: {e}"
        out.append(check("The comments that restate the line and the banners are gone; the why comment on the empty ABV "
                         "stays", not gone and why, found))
        try:
            fn = next((n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "connect"), None)
            doc = (ast.get_docstring(fn) or "") if fn else "no connect function"
        except SyntaxError as e:
            doc = f"brewlog/cli.py does not parse: {e}"
        out.append(check("connect's docstring keeps only its first line", doc.strip() == "Connect to the database.",
                         repr(doc)))
        readme = (repo / "README.md").read_text()
        m = missing(readme, [r"3\.11", r"pip install -e \.", r"~/\.config/brewlog/config\.toml",
                             r"~/\.local/share/brewlog/brew\.db", r"400 days", r"brewlog list",
                             r"brewlog export --since 2025-01-01 out\.csv", r"overwrit", r"python3 -m unittest"])
        out.append(check("README.md keeps every fact: Python 3.11, pip install -e ., the config and database paths, 400 "
                         "days, archived batches left out of brewlog list, the export command, the overwrite warning, "
                         "the test command", not m, f"missing: {m}" if m else "all kept"))
        p = present(readme, [r"welcome", r"in this document", r"really simple", r"worth noting", r"\bsimply\b",
                             r"generally speaking", r"in summary", r"happy brewing", "🍺", "🍻", "⚠️"])
        out.append(check("README.md's filler, emoji and closing lines are gone", not p, f"left: {p}" if p else "gone"))
        table = re.search(r"(?m)^\| Command \|\s*$", readme)
        out.append(check("README.md keeps the commands table (4.1 not picked)", table, "kept" if table else "gone"))
        usage = (repo / "docs/usage.md").read_text()
        ok = "400 days" in usage and not re.search(r"one year|a year|12 months", usage, re.I)
        out.append(check("docs/usage.md says 400 days, and no longer one year", ok,
                         re.search(r"(?im)^.*archiv.*$", usage).group(0) if re.search(r"(?im)^.*archiv.*$", usage)
                         else "no archiving line"))
        n = len(re.findall(r"overwrit", usage, re.I))
        out.append(check("docs/usage.md states the overwrite once", n == 1, f"{n} times"))
        m = missing(usage, [r'brewlog add "Amber ale"', r"\bOG\b", r"today", r"--fg 1\.012", r"fermentation",
                            r"name, date, OG, FG and ABV", r"on or after", r"ABV column stays empty|empty ABV|ABV.{0,40}empty",
                            r"\| `brewlog list --all` \|"])
        out.append(check("docs/usage.md keeps every fact and its two-column table", not m,
                         f"missing: {m}" if m else "all kept"))
        out.append(no_commit)

    if case == 3:
        out.append(check("Only .claude/skills/release/SKILL.md changed", diff == [SKILL], f"changed: {diff}"))
        text, old = (repo / SKILL).read_text(), (base / SKILL).read_text()
        front = lambda t: t.split("---", 2)[1] if t.startswith("---") else ""
        out.append(check("The frontmatter is unchanged (6.1 left)", front(text) == front(old), front(text)[:160]))
        m = missing(text, [r"python3 -m unittest", r"red build", r"CHANGELOG\.md", r"Unreleased",
                           r"(no entr|empty).{0,80}stop.{0,40}ask|stop and ask", r"invent", r"pyproject\.toml",
                           r"bump-my-version bump patch", r"\bminor\b", r"by hand|manually",
                           r"v<major>\.<minor>\.<patch>", r"publish", r"PyPI", r"(second|same version).{0,80}(reject|refuse)|reject.{0,60}(second|same version)",
                           r"new patch version"])
        out.append(check("Every rule is kept: the tests first and never on a red build; Unreleased empty means stop and "
                         "ask, no invented entries; the version in pyproject.toml, bump patch or minor, not by hand; the "
                         "tag format; ask before pushing; the push publishes to PyPI; PyPI rejects a second upload, so "
                         "the fix is a new patch version", not m, f"missing: {m}" if m else "all kept"))
        pos = [re.search(p, text, re.I) for p in (r"python3 -m unittest", r"Unreleased", r"bump-my-version",
                                                     r"v<major>", r"before push|push.{0,80}ask|ask.{0,40}push")]
        order = all(pos) and [p.start() for p in pos] == sorted(p.start() for p in pos)
        out.append(check("The steps keep their order: tests, changelog, bump, tag, push", order,
                         str([p.start() if p else None for p in pos])))
        asks = [l for l in text.splitlines() if re.search(r"\bask", l, re.I) and re.search(r"push", l, re.I)]
        out.append(check("Asking before the push is stated once", len(asks) == 1, f"{len(asks)}: {asks}"))
        p = present(text, [r"really important", r"quality matters", r"worth noting", r"first of all", r"remember",
                           r"in summary", r"that's it", "🚀", "🎉", r"^## Summary", r"^## Introduction"])
        out.append(check("The motivating intro, the summary, the filler and the emoji are gone", not p,
                         f"left: {p}" if p else "gone"))
        ratio = len(text) / len(old)
        out.append(check("The file is at least 30% smaller", ratio <= 0.7,
                         f"{len(old) // 4} → {len(text) // 4} tokens ({1 - ratio:.0%} smaller)"))
        out.append(no_commit)

    j = run / "judgement.json"
    if j.exists():
        out += json.load(open(j))
    passed = sum(c["passed"] for c in out)
    json.dump({"expectations": out,
               "summary": {"passed": passed, "failed": len(out) - passed, "total": len(out),
                           "pass_rate": round(passed / len(out), 3)}},
              open(run / "grading.json", "w"), indent=2)
    tmp.cleanup()
    return passed, len(out)


if __name__ == "__main__":
    it = Path(sys.argv[1])
    for run in sorted(it.glob("eval-*/*/run-*")):
        if (run / "outputs/final.md").exists():
            p, t = grade(run, int(run.parent.parent.name.split("-")[1]))
            print(f"{run.relative_to(it)}: {p}/{t}")
