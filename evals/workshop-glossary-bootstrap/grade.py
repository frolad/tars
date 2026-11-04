"""Grade every run of an iteration: python3 grade.py <iteration-dir>.

Needs per run what workshop-forge's grader needs: outputs/final.md, outputs/commands.txt, and optionally judgement.json
([{"text", "passed", "evidence"}], the checks graded by reading the reply). Writes grading.json per run. Reuses the
helpers of `../workshop-forge/grade.py`.
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
check, git_state, blocks, tests_pass = fg.check, fg.git_state, fg.blocks, fg.tests_pass
WORK = Path(".blueprints/glossary-bootstrap")
EVALS = {e["id"]: e for e in json.load(open(HERE / "evals.json"))["evals"]}
CATALOG = ["Tool", "Category", "Condition", "Deposit", "Kit", "Retired tool"]
LATER = ["Member", "Household", "Volunteer", "Induction", "Member number", "Loan", "Hold", "Reservation", "Late fee"]


def fresh(fixture):
    tmp = tempfile.TemporaryDirectory()
    repo = Path(tmp.name) / "repo"
    subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), fixture, str(repo)], check=True, capture_output=True)
    return tmp, repo


def diff(base, repo, *skip):
    """The files that differ between the fresh fixture and the run's repo, outside .git and the paths skipped."""
    args = ["diff", "-rq", "-x", ".git", "-x", "__pycache__"]
    for s in skip:
        args += ["-x", s]
    p = subprocess.run(args + [str(base), str(repo)], capture_output=True, text=True)
    return p.stdout.replace(str(base), "<fresh>").replace(str(repo), "<repo>").strip()


def entries_of(path):
    """{term: its entry text} of a glossary file, an entry being a bold term and the lines up to the next blank line."""
    if not path.exists():
        return {}
    out = {}
    for block in re.split(r"\n\s*\n", path.read_text()):
        m = re.match(r"\*\*(.+?)\*\*", block.strip())
        if m:
            out[m.group(1)] = block.strip()
    return out


def proposed_entries(reply):
    """The glossary entries a reply shows: lines that start a bold term with a colon, the questions left out."""
    return re.findall(r"(?m)^\s*(?:\d+\.\s+)?(?:New:\s*)?\*\*(?!Q\d)([^*\n]+)\*\*:", reply)


def code_names(reply):
    """The names the reply's `_In the code_` lines give, apart from Tool's Item, which the earlier turn settled."""
    return [n for n in re.findall(r"_In the code_:\s*`?([^`\n]+?)`?\s*$", reply, re.M) if n != "Item"]


def adr_check(repo, text):
    """The one ADR in docs/adrs/ is the one shown in the proposal, with the fields of an old decision."""
    adrs = sorted((repo / "docs/adrs").glob("*.md")) if (repo / "docs/adrs").exists() else []
    adr = adrs[0].read_text() if len(adrs) == 1 else ""
    ok = (adr.startswith("# Tools are retired, never deleted") and "Decided by the team on 2025-03-14." in adr
          and "Confirmed by the user on 2026-10-01." in adr and "insurer" in adr)
    return check(text, ok, f"{[p.name for p in adrs]}: {adr[:200]!r}" if adrs else "no ADR")


def current(repo):
    wf = repo / WORK / "bootstrap.md"
    text = wf.read_text() if wf.exists() else ""
    m = re.search(r"(?m)^Current:.*$", text)
    return text, (m.group(0) if m else "")


def grade(run, case):
    reply = (run / "outputs/final.md").read_text()
    commands = (run / "outputs/commands.txt").read_text()
    repo = run / "repo"
    tmp, base = fresh(EVALS[case]["fixture"])
    state, want = git_state(repo), git_state(base)
    read_glossary = [l for l in commands.splitlines() if l.startswith(("$ ", "[Read]")) and re.search(
        r"workshop-glossary/SKILL\.md|workshop-glossary/?\s*&&\s*(cat|head|sed)\b[^;|]*\bSKILL\.md|"
        r"workshop-glossary/?;[^|]*?\b(cat|head|sed)\b[^;|]*\$\{?\w+\}?/SKILL\.md", l)]
    loaded = check("workshop-glossary was loaded", read_glossary,
                   read_glossary[0][:120] if read_glossary else "workshop-glossary/SKILL.md not read")
    out = [check("Git untouched: same commits and branches as the fixture, clean index, no stash, no extra worktree",
                 state == want, json.dumps(state) if state != want else "same as the fixture")]

    if case == 1:
        d = diff(base, repo)
        out.append(check("Nothing written: no file created or changed in the repo", not d, d or "none"))
        out.append(loaded)
        named = [a for a in ("catalog", "members", "loans") if not re.search(rf"\b{a}\b", reply, re.I)]
        out.append(check("The plan names the three areas: catalog, members and loans", not named,
                         f"missing: {named}" if named else "all three named"))
        out.append(check("The plan names where the glossary goes (docs/GLOSSARY.md)", "GLOSSARY.md" in reply,
                         "named" if "GLOSSARY.md" in reply else "not named"))

    if case == 2:
        docs = (repo / "docs").exists()
        out.append(check("Nothing under docs/: no glossary or ADR written before an answer", not docs,
                         "docs/ exists" if docs else "no docs/"))
        d = diff(base, repo, ".blueprints")
        out.append(check("No file outside .blueprints changed", not d, d or "none"))
        text, cur = current(repo)
        out.append(check("The working file exists in .blueprints/glossary-bootstrap/ with a Current line", cur,
                         cur or f"files: {sorted(str(p.relative_to(repo)) for p in (repo / '.blueprints').rglob('*'))}"
                         if (repo / ".blueprints").exists() else "no .blueprints"))
        out.append(loaded)
        n = proposed_entries(reply)
        out.append(check("The proposal holds at most 10 entries", 0 < len(n) <= 10, f"{len(n)}: {n}"))
        m = re.search(r"_In the code_:\s*`?Item\b", reply)
        out.append(check("The Tool entry carries `_In the code_: Item`", m, m.group(0) if m else "not shown"))

    if case == 3:
        ok, last = tests_pass(repo)
        out.append(check("The tests pass", ok, last))
        d = diff(base, repo, ".blueprints", "docs")
        out.append(check("No file outside .blueprints and docs/ changed", not d, d or "none"))
        g = entries_of(repo / "docs/GLOSSARY.md")
        missing = [t for t in CATALOG if t not in g]
        out.append(check("docs/GLOSSARY.md has Tool, Category, Condition, Deposit, Kit and Retired tool, and no Power tool",
                         not missing and "Power tool" not in g, f"terms: {list(g)}"))
        tool = g.get("Tool", "")
        out.append(check("The Tool entry carries `_In the code_: Item`", re.search(r"_In the code_:\s*`?Item\b", tool),
                         tool[:160] or "no Tool entry"))
        bad = [t for t in CATALOG if t in g and not re.match(rf"\*\*{t}\*\*:\s+\S", g[t])]
        out.append(check("The entries are in workshop-glossary's format: the bold term, a colon and its meaning on one line",
                         g and not bad, f"not in format: {bad}" if bad else "all in format"))
        out.append(adr_check(repo, "The ADR is written as shown: decided by the team on 2025-03-14, confirmed by "
                                         "the user on 2026-10-01"))
        early = [t for t in LATER if t in g]
        out.append(check("No member or loan term written to the glossary yet", not early, f"written: {early}" if early
                         else "none"))
        text, cur = current(repo)
        out.append(check("The working file's Current line moved on to Members", re.search(r"\bMembers?\b", cur),
                         cur or "no Current line"))
        m = re.search(r"(?i)rename[\s\S]{0,400}?\bItem\b", text)
        out.append(check("The working file keeps Tool's code name Item as a rename candidate", m,
                         m.group(0)[-120:] if m else "no rename candidate"))
        names = code_names(reply)
        out.append(check("Every `_In the code_` line of the members' proposal names a thing (Account), not a flag such "
                         "as is_staff", bool(names) and all(n == "Account" for n in names), f"names: {names}"))
        offer = re.search(r"[^.\n]{0,60}\b((shall|should|can|may) I commit|I('ll| will) commit|want me to commit)"
                          r"[^.\n]{0,40}", reply, re.I)
        out.append(check("Does not commit or offer to commit", not offer and state == want,
                         offer.group(0).strip() if offer else "no commit, no offer"))

    if case == 4:
        d = diff(base, repo, ".blueprints", "docs", "CONTEXT.md")
        out.append(check("No file outside .blueprints, docs/ and CONTEXT.md changed", not d, d or "none"))
        g_md = (repo / "docs/GLOSSARY.md").exists()
        out.append(check("No docs/GLOSSARY.md: the glossary stays CONTEXT.md", not g_md,
                         "docs/GLOSSARY.md created" if g_md else "none"))
        ctx = (repo / "CONTEXT.md").read_text()
        g, want_g = entries_of(repo / "CONTEXT.md"), entries_of(base / "CONTEXT.md")
        rel = ctx.find("## Relationships")
        bad = [t for t in ("Category", "Power tool", "Kit", "Retired tool")
               if t not in g or not re.match(rf"\*\*{t}\*\*:\s*\n\S", g[t]) or ctx.find(f"**{t}**") > rel]
        out.append(check("CONTEXT.md has Category, Power tool, Kit and Retired tool, each in its format: the bold term "
                         "on its own line, the meaning on the next", not bad,
                         f"missing or not in format: {bad}" if bad else "all four, under Language"))
        cond = g.get("Condition", "")
        ok = ctx.count("**Condition**") == 1 and "Fair" in cond and "Good or Worn." not in ctx
        out.append(check("Condition is replaced in place: one entry, with Fair, the old text gone", ok, cond[:160]))
        tool, want_tool = g.get("Tool", ""), want_g["Tool"]
        same = [t for t in ("Deposit", "Member") if g.get(t) != want_g[t]]
        rel_same = blocks(repo / "CONTEXT.md").get("## Relationships") == blocks(base / "CONTEXT.md").get("## Relationships")
        ok = (re.search(r"_In the code_:\s*`?Item\b", tool) and tool.startswith(want_tool) and not same and rel_same)
        out.append(check("Tool gains `_In the code_: Item`; Deposit, Member and the Relationships section are unchanged",
                         ok, f"Tool: {tool[-80:]!r}; changed: {same}; Relationships same: {rel_same}"))
        out.append(adr_check(repo, "The ADR is written in docs/adrs/: decided by the team on 2025-03-14, confirmed "
                                         "by the user on 2026-10-01"))
        text, cur = current(repo)
        out.append(check("The working file's Current line moved on to Members", re.search(r"\bMembers?\b", cur),
                         cur or "no Current line"))
        names = code_names(reply)
        out.append(check("Every `_In the code_` line of the members' proposal names a thing (Account), not a flag such "
                         "as is_staff", bool(names) and all(n == "Account" for n in names), f"names: {names}"))

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
