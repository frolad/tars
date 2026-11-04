"""status_table.py <iterations.md>...: puts the fixture's pipeline files in the form of workshop-craft's format
(skills/workshop-craft/formats/iterations.md): each line's state word moves into a status table after the Current section."""
import re
import sys
from pathlib import Path

STATUS = {"done": "DONE", "current": "CURRENT", "next": "PLANNED", "preliminary": "PLANNED", "dropped": "WONT-DO",
          "reverted": "REVERTED", "split": "SPLIT"}
TITLES = {("01", "Access", "1.1"): "finance role", ("01", "Monthly report", "2.1"): "monthly report CSV",
          ("01", "Sales list", "3.1"): "sales list CSV", ("01", "Sales list", "3.2"): "sales list for finance",
          ("02", "Library", "1.1"): "PDF library", ("02", "Monthly report", "2.1"): "monthly report PDF",
          ("02", "Sales list", "3.1"): "sales list PDF",
          ("03", "Pages", "1.1"): "monthly page links", ("03", "Pages", "1.2"): "sales list links"}
LINE = re.compile(r"^- Iteration (\d+\.\d+), (%s)\b(,[^:]*)?:" % "|".join(STATUS))

for path in map(Path, sys.argv[1:]):
    rows, category, lines = [], "", []
    for line in path.read_text().splitlines():
        if line.startswith("### "):
            category = line[4:].strip()
        m = LINE.match(line)
        if m:
            n = m.group(1)
            rows.append(f"| {category} | {n} | {TITLES[path.parent.name[:2], category, n]} | {STATUS[m.group(2)]} |")
            line = f"- Iteration {n}{m.group(3) or ''}:{line[m.end():]}"
        lines.append(line)
    head, rest = re.match(r"(.*?^## Current\n\n.*?\n)(?=\n## )(.*)", "\n".join(lines) + "\n", re.S | re.M).groups()
    head = head.replace("preliminary", "PLANNED").replace(": next;", ": PLANNED, the next to run;")
    table = "\n## Status\n\n| Category | # | Title | Status |\n|---|---|---|---|\n" + "\n".join(rows) + "\n"
    path.write_text(head + table + rest)
