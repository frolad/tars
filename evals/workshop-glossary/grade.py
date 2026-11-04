"""Grade every run of an iteration: python3 grade.py <iteration-dir>.

Needs per run what workshop-forge's grader needs: outputs/final.md, outputs/commands.txt, events.json, metrics.json, and
optionally judgement.json ([{"text", "passed", "evidence"}], graded by reading the reply). Writes grading.json per
run. Reuses the helpers of `../workshop-forge/grade.py`.
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
check, git_state, blocks, tests_pass, outside_blueprints_diff = (fg.check, fg.git_state, fg.blocks, fg.tests_pass,
                                                                  fg.outside_blueprints_diff)
BP = Path(".blueprints/finance-exports")
P1 = BP / "pipelines/01-csv-downloads"
EVALS = {e["id"]: e for e in json.load(open(HERE / "evals.json"))["evals"]}


def fresh(fixture):
    tmp = tempfile.TemporaryDirectory()
    repo = Path(tmp.name) / "repo"
    subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), fixture, str(repo)], check=True, capture_output=True)
    return tmp, repo


COMMIT = re.compile(r"[^.\n]{0,80}(\b(suggest|recommend)\w*\s+(a\s+|you\s+|putting\s+[^.\n]{0,40}in\s+(one|a)\s+)?commit|"
                    r"\b(you\s+(can|could|may|might|should)|please|worth)\s+commit|"
                    r"\bcommit\w*\b[^.\n]{0,60}\b(before the review|first)\b|\bbefore the review\b[^.\n]{0,20}\bcommit\b)"
                    r"[^.\n]{0,80}", re.I)


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


def no_code_lines(text):
    """The text without `_In the code_` lines, which workshop-forge adds to a term as a fact at any time."""
    return "\n".join(l for l in text.splitlines() if not l.strip().startswith("_In the code_"))


def tree(root):
    return {str(p.relative_to(root)): p.read_text() for p in sorted(root.rglob("*")) if p.is_file()} \
        if root.exists() else {}


def grade(run, case):
    reply = (run / "outputs/final.md").read_text()
    commands = (run / "outputs/commands.txt").read_text()
    repo = run / "repo"
    tmp, base = fresh(EVALS[case]["fixture"])
    state, want = git_state(repo), git_state(base)
    read_glossary = [l for l in commands.splitlines() if l.startswith(("$ ", "[Read]")) and re.search(
        r"workshop-glossary/SKILL\.md|workshop-glossary/?\s*&&\s*(cat|head|sed)\b[^;|]*\bSKILL\.md|"
        r"workshop-glossary/?;[^|]*?\b(cat|head|sed)\b[^;|]*\$\{?\w+\}?/SKILL\.md", l)]
    records = {str(p.relative_to(repo / "docs")) for p in fg.record_files(repo)}
    docs_same = {k: v for k, v in tree(repo / "docs").items() if k not in records} == tree(base / "docs")
    diff = outside_blueprints_diff(base, repo)
    out = [check("Git untouched: same commits and branches as the fixture, clean index, no stash, no extra worktree",
                 state == want, json.dumps(state) if state != want else "same as the fixture")]
    if case != 5:  # the approval turn writes docs/
        out.append(check("Nothing under docs/ changed but the TARS Blueprint Record", docs_same,
                         "docs/ as in the fixture" if docs_same else "docs/ changed"))

    if case == 1:
        ok, last = tests_pass(repo)
        out.append(check("The tests pass", ok, last))
        out.append(check("No file outside .blueprints changed", not diff, diff or "none"))
        out.append(check("workshop-glossary was loaded", read_glossary, read_glossary[0][:120] if read_glossary
                         else "workshop-glossary/SKILL.md not read"))
        terms, want_terms = (no_code_lines(blocks(r / BP / "00-knowledge.md").get("## Terms", "")) for r in (repo, base))
        out.append(check("The blueprint's Terms are unchanged: nothing moved before the user's answer",
                         terms == want_terms, "same Terms, apart from _In the code_ lines" if terms == want_terms
                         else terms[:200]))
        listed = re.search(r"mattpocock", reply, re.I)
        out.append(check("The turn ends on the merge: no review skills listed yet", not listed,
                         "review skills listed" if listed else "no review list"))
    if case == 2:
        new = sorted(set(tree(repo / ".blueprints")) - set(tree(base / ".blueprints")))
        out.append(check("No file written: no new blueprint file, nothing outside .blueprints changed",
                         not new and not diff, f"new: {new[:3]}; changed: {diff or 'none'}"))
        out.append(check("workshop-glossary was loaded", read_glossary, read_glossary[0][:120] if read_glossary
                         else "workshop-glossary/SKILL.md not read"))
    if case == 3:
        out.append(check("No code written: nothing outside .blueprints changed while the question is open", not diff,
                         diff or "none"))
        out.append(check("workshop-glossary was not loaded", not read_glossary,
                         read_glossary[0][:120] if read_glossary else "not read"))
        current = blocks(repo / P1 / "iterations.md").get("## Current", "")
        out.append(check("Current says the pipeline waits on the user",
                         re.search(r"wait\w*\s+(on|for)\s+(the\s+)?user", current, re.I), current[:200] or "no Current"))
    if case == 4:
        out.append(check("No file outside .blueprints changed", not diff, diff or "none"))
        named = re.search(r"\bSale\b", reply)
        out.append(check("The reply names the glossary's Sale term", named, "Sale named" if named else "Sale not named"))

    if case == 5:
        ok, last = tests_pass(repo)
        out.append(check("The tests pass", ok, last))
        d = subprocess.run(["diff", "-rq", "-x", ".git", "-x", "__pycache__", "-x", ".blueprints", "-x", "docs",
                            str(base), str(repo)], capture_output=True, text=True).stdout.strip()
        out.append(check("No file outside .blueprints and docs/ changed", not d, d.replace(str(repo), "<repo>") or "none"))
        g, want_g = (entries_of(r / "docs/GLOSSARY.md") for r in (repo, base))
        sales = g.get("Sales list", "")
        out.append(check("The glossary has the Sales list entry as approved, without an _Avoid_ line",
                         sales and "_Avoid_" not in sales and "every sale" in sales, sales[:160] or "no Sales list entry"))
        text = (repo / "docs/GLOSSARY.md").read_text() if (repo / "docs/GLOSSARY.md").exists() else ""
        fin = g.get("Finance user", "")
        ok = (text.count("**Finance user**") == 1 and "for every region" in fin and "own region only" not in text
              and not re.search(r"\b20\d\d-\d\d-\d\d\b|amend|updated|changed on", fin, re.I))
        out.append(check("Finance user is replaced in place: one entry, the new text, the old text gone, no date or "
                         "amendment added", ok, fin[:200] or "no Finance user entry"))
        others = [k for k in want_g if k != "Finance user" and g.get(k) != want_g[k]]
        out.append(check("The glossary's other entries are unchanged", not others, f"changed: {others}" if others else "unchanged"))
        adrs = repo / "docs/adrs"
        money_same = (adrs / "money-amounts-in-cents.md").exists() and \
            (adrs / "money-amounts-in-cents.md").read_text() == (base / "docs/adrs/money-amounts-in-cents.md").read_text()
        gone = not (adrs / "exports-json-only.md").exists()
        out.append(check("The superseded ADR is deleted and the money ADR is unchanged", gone and money_same,
                         f"exports-json-only.md deleted: {gone}; money ADR unchanged: {money_same}; "
                         f"files: {sorted(p.name for p in adrs.glob('*'))}"))
        terms = blocks(repo / BP / "00-knowledge.md").get("## Terms", "")
        ok = ("**Sales list**" not in terms and "**Finance user**" not in terms and "**Printable copy**" in terms
              and "**Download link**" in terms)
        out.append(check("The merged terms left the blueprint's Terms; Printable copy and Download link stay", ok,
                         terms[:240] or "no Terms section"))
        m = COMMIT.search(reply)
        out.append(check("The reply suggests a commit", m, m.group(0).strip() if m else "no commit suggested"))
        offer = re.search(r"[^.\n]{0,60}\b((shall|should|can|may) I commit|I('ll| will) commit|want me to commit)[^.\n]{0,40}",
                          reply, re.I)
        out.append(check("Does not offer to commit for the user", not offer, offer.group(0).strip() if offer else "no offer"))
        builtin = re.search(r"(?<![\w:-])/?code-review\b", reply.replace("mattpocock-skills:code-review", ""))
        matt = "mattpocock" in reply.lower()
        out.append(check("The reply lists the review skills the session shows", builtin and matt,
                         f"built-in: {bool(builtin)}; mattpocock: {matt}"))

    if case == 6:
        ok, last = tests_pass(repo)
        out.append(check("The tests pass", ok, last))
        out.append(check("No file outside .blueprints changed", not diff, diff or "none"))
        out.append(check("workshop-glossary was not loaded", not read_glossary,
                         read_glossary[0][:120] if read_glossary else "not read"))
        terms, want_terms = (blocks(r / BP / "00-knowledge.md").get("## Terms", "") for r in (repo, base))
        out.append(check("The blueprint's Terms are unchanged", terms == want_terms,
                         "same Terms" if terms == want_terms else terms[:200]))
        # The run's own folder, in the reply's file links, is named after this skill in the test workspaces
        said = re.search(r"[^.\n]{0,60}(glossar\w*|\bADRs?\b)[^.\n]{0,60}", reply.replace(str(run.resolve()), "<run>"),
                         re.I)
        out.append(check("The reply says nothing about a glossary or ADRs", not said,
                         said.group(0).strip() if said else "not mentioned"))
        m = COMMIT.search(reply)
        out.append(check("The reply suggests a commit", m, m.group(0).strip() if m else "no commit suggested"))
        builtin = re.search(r"(?<![\w:-])/?code-review\b", reply.replace("mattpocock-skills:code-review", ""))
        matt = "mattpocock" in reply.lower()
        out.append(check("The reply lists the review skills the session shows", builtin and matt,
                         f"built-in: {bool(builtin)}; mattpocock: {matt}"))
    if case == 7:
        new = sorted(set(tree(repo / ".blueprints")) - set(tree(base / ".blueprints")))
        out.append(check("No file written: no new blueprint file, nothing outside .blueprints changed",
                         not new and not diff, f"new: {new[:3]}; changed: {diff or 'none'}"))
        out.append(check("workshop-glossary was not loaded", not read_glossary,
                         read_glossary[0][:120] if read_glossary else "not read"))
        push = next((m for m in re.finditer(r"[^.\n]{0,60}\b(build|creat|start|set\w* up|add|keep|bootstrap)\w*\b"
                                            r"[^.\n]{0,40}\bglossar\w*[^.\n]{0,60}", reply, re.I)
                     if not re.search(r"\btask'?s?\b[^.\n]{0,15}glossar", m.group(0), re.I)), None)
        out.append(check("Does not suggest building or creating a glossary", not push,
                         push.group(0).strip() if push else "no suggestion"))
        named = re.search(r"\bSale\b", reply)
        out.append(check("The reply names the code's Sale", named, "Sale named" if named else "Sale not named"))

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
