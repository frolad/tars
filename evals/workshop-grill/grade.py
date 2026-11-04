"""Grade every run of an iteration: python3 grade.py <iteration-dir>.

Needs per run: outputs/final.md (the reply), outputs/commands.txt and metrics.json (extract.py), and optionally
judgement.json ([{"text", "passed", "evidence"}], graded by reading the reply). Writes grading.json per run.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
EMOJI = re.compile("[☀-➿\U0001f300-\U0001faff⬅-⬇⭐]")
LABEL = re.compile(r"\*\*Q\d+(?:\*\*)?\s*[-–—:]")
SHAPE_LABEL = re.compile(r"^❓ \*\*Q\d+\*\* - \*\*[^*\n]+\*\*:", re.M)
RECOMMENDED = re.compile(r"(^|\n)\s*➡")
LABEL_ONLY = re.compile(r"^(done when|item|check|criterion|#)?\s*\d+\W*$", re.I)


def check(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": evidence}


def questions(reply):
    starts = [m.start() for m in LABEL.finditer(reply)]
    return [reply[a:b] for a, b in zip(starts, starts[1:] + [len(reply)])]


def unchanged(repo, fixture):
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "repo"
        subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), fixture, str(fresh)], check=True,
                       capture_output=True)
        p = subprocess.run(["diff", "-rq", "-x", ".git", "-x", "__pycache__", str(fresh), str(repo)],
                           capture_output=True, text=True)
        return p.returncode == 0, (p.stdout.replace(str(fresh), "<fresh>").replace(str(repo), "<repo>").strip()
                                   or "no file differs from the fixture")


def reads(commands):
    return [l for l in commands.splitlines()
            if l.startswith("[Read]") or re.match(r"\$ .*\b(cat|grep|rg|sed|head|ls|find)\b", l)]


def common(run, commands, fixture):
    ok, ev = unchanged(run / "repo", fixture)
    # A read of a SKILL.md loads that skill; a listing, or a command's output, does not
    other = [l for l in commands.splitlines() if re.match(r"\[Read\] .*SKILL\.md|\$ .*\b(cat|head|tail|sed|less|more)\b"
                                                          r"[^;|&]*SKILL\.md", l) and "workshop-grill-iter" not in l
             and "upstream-grilling" not in l and "/skills/sttp/" not in l and "sttp-software-engineering" not in l]
    skill_calls = json.load(open(run / "metrics.json")).get("tool_calls", {}).get("Skill", 0)
    return [
        check("No file in the repo changed", ok, ev),
        check("No other skill was loaded", not other and not skill_calls,
              f"Skill tool calls: {skill_calls}; other SKILL.md reads: {other[:3]}"),
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


def grade(run, eval_name):
    reply = (run / "outputs/final.md").read_text()
    commands = (run / "outputs/commands.txt").read_text()
    qs = questions(reply)
    words = len(reply.split())
    fixture = {"eval-3": "light-clear", "eval-4": "light-decision", "eval-5": "self-check"}.get(eval_name[:6], "base")
    out = common(run, commands, fixture)
    if eval_name.startswith(("eval-1", "eval-2")):
        out += format_checks(reply, qs)
    if eval_name.startswith("eval-1"):
        r = reads(commands)
        out.append(check("Read the repo before replying (3+ reads)", len(r) >= 3, f"{len(r)} reads"))
    if eval_name.startswith("eval-2") and "iteration-1" not in str(run):
        new_q3 = [q.splitlines()[0][:80] for q in qs if re.match(r"\*\*Q3\b", q)
                  and not re.search(r"total", q.splitlines()[0], re.I)]
        out.append(check("No new question reuses the number of an answered one (Q3 was answered)", not new_q3,
                         f"labels: {[q.splitlines()[0][:40] for q in qs]}"))
    if eval_name.startswith("eval-3"):
        out.append(check("No question is put to the user", not qs and not RECOMMENDED.search(reply),
                         f"{len(qs)} labelled questions"))
        out.append(check("The reply is short: at most 80 words", words <= 80, f"{words} words"))
    if eval_name.startswith(("eval-3", "eval-4")):
        both = [p for p in ("pipeline.md", "knowledge.md") if any(p in l for l in commands.splitlines())]
        out.append(check("Read the pipeline and the knowledge file", len(both) == 2, f"read: {both}"))
    if eval_name.startswith("eval-4"):
        out += format_checks(reply, qs)
        out.append(check("One or two questions reach the user", 1 <= len(qs) <= 2, f"{len(qs)} questions"))
        access = [q for q in qs if re.search(r"access|finance|role|who (can|may)", q, re.I)]
        out.append(check("The access decision is asked", access, f"{len(access)} question(s) on access"))
        settled = [q.splitlines()[0][:80] for q in qs
                   if re.search(r"separator|semicolon|file ?name|header|totals? row|decimal|format_eur",
                                q.split("\n")[0], re.I)]
        out.append(check("No settled item is asked again (format, separator, file name, header, totals)",
                         not settled, f"re-asked: {settled or 'none'}"))
        out.append(check("The reply is one short message: at most 250 words", words <= 250, f"{words} words"))
    if eval_name.startswith("eval-5"):
        out += format_checks(reply, qs)
        nums = [int(n) for n in re.findall(r"\*\*Q(\d+)", reply)]
        out.append(check("Numbering continues after Q12", nums and min(nums) >= 13, f"numbers: {nums}"))
        titles = [re.sub(r"^\*\*Q\d+\s*-\s*", "", q.split("**:")[0].split("\n")[0]).strip("* ") for q in qs]
        bare = [t for t in titles if LABEL_ONLY.match(re.sub(r"[\"'`]", "", t)) or not re.findall(r"[A-Za-z]{3,}",
                re.sub(r"(?i)done when|item|check|\d+", "", t))]
        out.append(check("Every question's title names its subject, not only a label such as 'Done when 4'",
                         qs and not bare, f"titles: {titles}; label only: {bare or 'none'}"))
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
            p, t = grade(run, run.parent.parent.name)
            print(f"{run.relative_to(it)}: {p}/{t}")
