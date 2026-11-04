#!/usr/bin/env bash
# make_fixture.sh <fixture> <dir>: the reports repo, built by real commits so the tests pass at HEAD.
# base: no blueprint, .blueprints not ignored. ready, access-done, wrong-fact, inline-csv, csv-done, pipeline-done:
# .blueprints ignored, and workshop-craft's finished blueprint .blueprints/finance-exports/ at the state the code is in.
# broken-helper: csv-done, plus a test helper whose data file was renamed without it, which the next iteration uses.
# record: access-done, plus pipeline 1's file of the task's TARS Blueprint Record,
# docs/tars-reports/finance-exports/01-csv-downloads.md, committed.
# tagged: access-done, with a question number after every decision of the blueprint's knowledge, as real blueprints
# have them: "Decided by the user on 2026-09-30 (Q3).".
# region-done: another task, started from a session: a region filter on the monthly report, its one pipeline's
# iterations all done and committed, in .blueprints/region-filter/, and its record committed.
set -euo pipefail
fixture=$1; dir=$2
broken=; record=; tagged=
if [[ $fixture == broken-helper ]]; then broken=1; fixture=csv-done; fi
if [[ $fixture == record ]]; then record=1; fixture=access-done; fi
if [[ $fixture == tagged ]]; then tagged=1; fixture=access-done; fi
here=$(cd "$(dirname "$0")" && pwd)
if [[ $fixture == research ]]; then
  rm -rf "$dir"; mkdir -p "$dir"; cd "$dir"
  cat > notes.md <<'MD'
# Team notes

We run a small Python reports app (Python 3.12). Servers install with pip only: no system packages.
Finance wants PDF copies of two reports. Nobody on the team has picked a PDF library before.
Region and product names are typed by sales staff in several countries.
MD
  exit 0
fi
case $fixture in research|base|ready|access-done|wrong-fact|inline-csv|csv-done|pipeline-done|region-done) ;; *) echo "unknown fixture: $fixture" >&2; exit 2;; esac
rm -rf "$dir"; mkdir -p "$dir"; cd "$dir"
git init -q -b main
git config user.email user@example.com; git config user.name user
mkdir -p reports tests templates
: > reports/__init__.py; : > tests/__init__.py
echo "__pycache__/" > .gitignore
cat > README.md <<'MD'
# reports

Internal sales reports. Staff see them after login; the finance team uses the monthly report for the
month-end close.

Run the tests: `python3 -m unittest`
MD
cat > reports/models.py <<'PY'
from dataclasses import dataclass
from datetime import date


@dataclass
class Sale:
    id: int
    region: str
    product: str
    units: int
    amount_cents: int
    sold_on: date
PY
cat > reports/money.py <<'PY'
def format_eur(cents):
    """12345 -> '123.45'"""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"
PY
cat > reports/queries.py <<'PY'
def monthly_sales(sales, year, month):
    """One row per region and product: {"region", "product", "units", "amount_cents"}."""
    rows = {}
    for s in sales:
        if s.sold_on.year != year or s.sold_on.month != month:
            continue
        row = rows.setdefault((s.region, s.product),
                              {"region": s.region, "product": s.product, "units": 0, "amount_cents": 0})
        row["units"] += s.units
        row["amount_cents"] += s.amount_cents
    return sorted(rows.values(), key=lambda r: (r["region"], r["product"]))


def total_cents(rows):
    return sum(r["amount_cents"] for r in rows)
PY
cat > reports/auth.py <<'PY'
ROLES = {"staff", "admin"}


class Forbidden(Exception):
    pass


def has_role(user, role):
    return role in user.get("roles", ())


def require_login(view):
    def wrapped(request, *args, **kwargs):
        if not request.get("user"):
            raise Forbidden("login required")
        return view(request, *args, **kwargs)
    return wrapped


def require_role(role):
    def decorate(view):
        def wrapped(request, *args, **kwargs):
            user = request.get("user")
            if not user or not has_role(user, role):
                raise Forbidden(f"{role} role required")
            return view(request, *args, **kwargs)
        return wrapped
    return decorate
PY
cat > reports/export.py <<'PY'
import json

from .money import format_eur


def to_json(rows):
    return json.dumps([{**r, "amount": format_eur(r["amount_cents"])} for r in rows])
PY
cat > reports/views.py <<'PY'
from .auth import require_login
from .export import to_json
from .queries import monthly_sales, total_cents


def render(template, **context):
    return {"template": template, "context": context}


def response(body, content_type, headers=None):
    return {"body": body, "content_type": content_type, "headers": headers or {}}


@require_login
def monthly_report(request, year, month):
    rows = monthly_sales(request["sales"], year, month)
    return render("monthly.html", rows=rows, total=total_cents(rows), year=year, month=month)


@require_login
def monthly_report_json(request, year, month):
    rows = monthly_sales(request["sales"], year, month)
    return response(to_json(rows), "application/json")
PY
cat > reports/admin_views.py <<'PY'
from .auth import require_role
from .views import render


@require_role("admin")
def all_sales(request):
    return render("all_sales.html", sales=request["sales"])
PY
cat > templates/monthly.html <<'HTML'
<h1>Sales {{ year }}-{{ month }}</h1>
<table>
  <tr><th>Region</th><th>Product</th><th>Units</th><th>Amount (EUR)</th></tr>
  {% for r in rows %}
  <tr><td>{{ r.region }}</td><td>{{ r.product }}</td><td>{{ r.units }}</td><td>{{ r.amount_cents|eur }}</td></tr>
  {% endfor %}
  <tr><td colspan="3">Total</td><td>{{ total|eur }}</td></tr>
</table>
<a href="/reports/{{ year }}/{{ month }}.json">JSON</a>
HTML
cat > tests/test_export.py <<'PY'
import json
import unittest

from reports.export import to_json


class ToJsonTest(unittest.TestCase):
    def test_amount_is_formatted(self):
        rows = [{"region": "North", "product": "Widget", "units": 3, "amount_cents": 1234}]
        self.assertEqual(json.loads(to_json(rows))[0]["amount"], "12.34")


if __name__ == "__main__":
    unittest.main()
PY
cat > tests/test_views.py <<'PY'
import unittest
from datetime import date

from reports.auth import Forbidden
from reports.models import Sale
from reports.views import monthly_report_json

SALES = [Sale(1, "North", "Widget", 3, 1234, date(2026, 8, 3))]


class MonthlyJsonTest(unittest.TestCase):
    def test_needs_login(self):
        with self.assertRaises(Forbidden):
            monthly_report_json({"sales": SALES}, 2026, 8)

    def test_returns_json(self):
        r = monthly_report_json({"user": {"roles": ["staff"]}, "sales": SALES}, 2026, 8)
        self.assertEqual(r["content_type"], "application/json")


if __name__ == "__main__":
    unittest.main()
PY
cat > templates/all_sales.html <<'HTML'
<h1>All sales</h1>
<table>
  <tr><th>Date</th><th>Region</th><th>Product</th><th>Units</th><th>Amount (EUR)</th></tr>
  {% for s in sales %}
  <tr><td>{{ s.sold_on }}</td><td>{{ s.region }}</td><td>{{ s.product }}</td><td>{{ s.units }}</td><td>{{ s.amount_cents|eur }}</td></tr>
  {% endfor %}
</table>
HTML
cat > tests/test_auth.py <<'PY'
import unittest

from reports.auth import Forbidden, require_role


def view(request):
    return "ok"


class RequireRoleTest(unittest.TestCase):
    def test_admin_passes(self):
        self.assertEqual(require_role("admin")(view)({"user": {"roles": ["admin"]}}), "ok")

    def test_staff_is_refused(self):
        with self.assertRaises(Forbidden):
            require_role("admin")(view)({"user": {"roles": ["staff"]}})


if __name__ == "__main__":
    unittest.main()
PY
git add -A; git commit -qm "initial"
if [[ $fixture == base ]]; then
  exit 0
fi

echo ".blueprints/" >> .gitignore
git add -A; git commit -qm "Ignore .blueprints"
base_commit=$(git rev-parse HEAD)

if [[ $fixture == region-done ]]; then
  python3 - <<'PY'
from pathlib import Path
p = Path("reports/queries.py"); t = p.read_text()
t = t.replace('''def monthly_sales(sales, year, month):
    """One row per region and product: {"region", "product", "units", "amount_cents"}."""
    rows = {}
    for s in sales:
        if s.sold_on.year != year or s.sold_on.month != month:
            continue''', '''def monthly_sales(sales, year, month, region=None):
    """One row per region and product: {"region", "product", "units", "amount_cents"}, of one region, in any case,
    when it is given."""
    rows = {}
    for s in sales:
        if s.sold_on.year != year or s.sold_on.month != month:
            continue
        if region and s.region.casefold() != region.casefold():
            continue''')
p.write_text(t)
Path("tests/test_queries.py").write_text('''import unittest
from datetime import date

from reports.models import Sale
from reports.queries import monthly_sales, total_cents

SALES = [Sale(1, "North", "Widget", 3, 1234, date(2026, 8, 3)), Sale(2, "South", "Gadget", 1, 500, date(2026, 8, 9))]


class RegionTest(unittest.TestCase):
    def test_only_the_region_asked_for_in_any_case(self):
        self.assertEqual([r["region"] for r in monthly_sales(SALES, 2026, 8, "north")], ["North"])

    def test_a_region_with_no_sales_has_no_rows_and_a_zero_total(self):
        rows = monthly_sales(SALES, 2026, 8, "West")
        self.assertEqual((rows, total_cents(rows)), ([], 0))

    def test_every_region_without_one(self):
        self.assertEqual(len(monthly_sales(SALES, 2026, 8)), 2)


if __name__ == "__main__":
    unittest.main()
''')
PY
  git add -A; git commit -qm "Filter, iteration 1.1: monthly_sales keeps one region"
  python3 - <<'PY'
from pathlib import Path
p = Path("reports/views.py"); t = p.read_text()
t = t.replace('''def monthly_report(request, year, month):
    rows = monthly_sales(request["sales"], year, month)
    return render("monthly.html", rows=rows, total=total_cents(rows), year=year, month=month)''', '''def monthly_report(request, year, month, region=None):
    rows = monthly_sales(request["sales"], year, month, region)
    return render("monthly.html", rows=rows, total=total_cents(rows), year=year, month=month, region=region)''')
t = t.replace('''def monthly_report_json(request, year, month):
    rows = monthly_sales(request["sales"], year, month)''', '''def monthly_report_json(request, year, month, region=None):
    rows = monthly_sales(request["sales"], year, month, region)''')
p.write_text(t)
p = Path("tests/test_views.py"); t = p.read_text()
t = t.replace("import unittest\n", "import json\nimport unittest\n", 1)
t = t.replace('''

if __name__ == "__main__":''', '''
    def test_json_keeps_the_region_asked_for(self):
        r = monthly_report_json({"user": {"roles": ["staff"]}, "sales": SALES}, 2026, 8, "NORTH")
        self.assertEqual([row["region"] for row in json.loads(r["body"])], ["North"])


if __name__ == "__main__":''')
p.write_text(t)
PY
  git add -A; git commit -qm "Filter, iteration 1.2: the monthly page and its JSON take a region"
  mkdir -p .blueprints/region-filter/pipelines/01-region-filter docs/tars-reports/region-filter
  cat > .blueprints/region-filter/pipelines/01-region-filter/iterations.md <<MD
# Pipeline 1: region filter

Goal: finance looks at one region at a time on the monthly report and its JSON.
Done when:
- The monthly page and its JSON show only the region asked for, matched in any case.
- A region with no sales shows no rows and a total of 0.00.
- Without a region, both show every region, as before.
Iteration size: one behaviour per iteration, with its test. Suggested by workshop-forge, confirmed by the user on
2026-10-20.
Base: $base_commit, HEAD when the first iteration started.

## Current

The end of the pipeline: every Done when item is met, everything since Base is committed, and the review
(code-review) found one thing; waiting on the user's answer on finding 1.

## Status

| Category | #   | Title                 | Status |
|----------|-----|-----------------------|--------|
| Filter   | 1.1 | region in the query   | DONE   |
| Filter   | 1.2 | the page and its JSON | DONE   |

## Iterations

### Filter
- Iteration 1.1: \`monthly_sales\` keeps only the region asked for, in any case; no rows for a region with no sales
  (\`reports/queries.py\`).
- Iteration 1.2: the monthly page and its JSON take the region (\`reports/views.py\`).
MD
  cat > .blueprints/region-filter/pipelines/01-region-filter/knowledge.md <<'MD'
# Knowledge: pipeline 1, region filter

## Terms

- **Region**: the sales region typed on each sale, such as North or South. _In the code_: `Sale.region`.

## Facts

### Queries
- `monthly_sales` builds the rows of the monthly page and of its JSON; both views call it.
  Source: reports/queries.py:1, reports/views.py:14, read 2026-10-20.

## Decisions

- A region matches in any case: `north` finds North.
  Why: region names are typed by people.
  Rules out: an exact match.
  Decided by the user on 2026-10-20.
- A region with no sales gives no rows and a total of 0.00, not an error.
  Why: finance checks every region each month, and an empty one is an answer.
  Rules out: an error for an empty region.
  Decided by the user on 2026-10-20.
MD
  cat > docs/tars-reports/region-filter/01-region-filter.md <<'MD'
# TARS Blueprint Record: region filter on the monthly report: the filter

The code is the source of truth: check anything here against the code before relying on it.

State: built on main.

## Why
Finance looks at one region at a time on the monthly report. The page and its JSON showed every region of the month.

## Planning decisions
- A region matches in any case: `north` finds North.
  Why: region names are typed by people.
  Rules out: an exact match.
- A region with no sales gives no rows and a total of 0.00, not an error.
  Why: finance checks every region each month, and an empty one is an answer.
  Rules out: an error for an empty region.

## What was built
- The monthly page and its JSON take a region and show only its rows; without one, they show every region as before
  (`reports/queries.py`, `reports/views.py`).
MD
  git add docs; git commit -qm "Blueprint record: region filter"
  exit 0
fi

# Code states, each a real commit, so the tests pass at HEAD.
if [[ $fixture != ready ]]; then
  python3 - <<'PY'
from pathlib import Path
p = Path("reports/auth.py"); t = p.read_text()
t = t.replace('ROLES = {"staff", "admin"}', 'ROLES = {"staff", "admin", "finance"}')
t = t.replace('''def require_role(role):
    def decorate(view):
        def wrapped(request, *args, **kwargs):
            user = request.get("user")
            if not user or not has_role(user, role):
                raise Forbidden(f"{role} role required")''', '''def require_role(*roles):
    def decorate(view):
        def wrapped(request, *args, **kwargs):
            user = request.get("user")
            if not user or not any(has_role(user, role) for role in roles):
                raise Forbidden(f"{' or '.join(roles)} role required")''')
p.write_text(t)
p = Path("tests/test_auth.py"); t = p.read_text()
t = t.replace('''

if __name__ == "__main__":''', '''
    def test_finance_passes(self):
        self.assertEqual(require_role("finance", "admin")(view)({"user": {"roles": ["finance"]}}), "ok")

    def test_admin_passes_either_role(self):
        self.assertEqual(require_role("finance", "admin")(view)({"user": {"roles": ["admin"]}}), "ok")

    def test_staff_is_refused_by_either_role(self):
        with self.assertRaises(Forbidden):
            require_role("finance", "admin")(view)({"user": {"roles": ["staff"]}})


if __name__ == "__main__":''')
p.write_text(t)
PY
  git add -A; git commit -qm "Access, iteration 1.1: a finance role; require_role takes several roles"
fi

if [[ $fixture == wrong-fact || $fixture == inline-csv || $fixture == csv-done || $fixture == pipeline-done ]]; then
  if [[ $fixture == inline-csv ]]; then
    cat >> reports/views.py <<'PY'


@require_role("finance", "admin")
def monthly_report_csv(request, year, month):
    rows = monthly_sales(request["sales"], year, month)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Region", "Product", "Units", "Amount (EUR)"])
    for r in rows:
        writer.writerow([r["region"], r["product"], r["units"], format_eur(r["amount_cents"])])
    filename = f"sales-{year}-{month:02d}.csv"
    return response(out.getvalue(), "text/csv", {"Content-Disposition": f"attachment; filename={filename}"})
PY
    python3 - <<'PY'
from pathlib import Path
p = Path("reports/views.py"); t = p.read_text()
t = t.replace("from .auth import require_login\n", "import csv\nimport io\n\nfrom .auth import require_login, require_role\n")
t = t.replace("from .export import to_json\n", "from .export import to_json\nfrom .money import format_eur\n")
p.write_text(t)
PY
  else
    cat >> reports/export.py <<'PY'


def to_csv(header, rows):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(header)
    writer.writerows(rows)
    return out.getvalue()
PY
    if [[ $fixture == csv-done ]]; then
      amount='Amount'; month='{month}'; disposition='inline'
    else
      amount='Amount (EUR)'; month='{month:02d}'; disposition='attachment'
    fi
    if [[ $fixture == wrong-fact ]]; then
      total='    lines.append(["Total", "", "", format_eur(total_cents(rows))])
'
    else
      total=''
    fi
    cat >> reports/views.py <<PY


MONTHLY_HEADER = ["Region", "Product", "Units", "$amount"]


@require_role("finance", "admin")
def monthly_report_csv(request, year, month):
    rows = monthly_sales(request["sales"], year, month)
    lines = [[r["region"], r["product"], r["units"], format_eur(r["amount_cents"])] for r in rows]
${total}    filename = f"sales-{year}-$month.csv"
    return response(to_csv(MONTHLY_HEADER, lines), "text/csv", {"Content-Disposition": f"$disposition; filename={filename}"})
PY
    python3 - <<'PY'
from pathlib import Path
p = Path("reports/export.py"); t = p.read_text()
p.write_text(t.replace("import json\n", "import csv\nimport io\nimport json\n", 1))
p = Path("reports/views.py"); t = p.read_text()
t = t.replace("from .auth import require_login\n", "from .auth import require_login, require_role\n")
t = t.replace("from .export import to_json\n", "from .export import to_csv, to_json\nfrom .money import format_eur\n")
p.write_text(t)
PY
  fi
  python3 - "$fixture" <<'PY'
import sys
from pathlib import Path
fixture = sys.argv[1]
p = Path("tests/test_views.py"); t = p.read_text()
t = t.replace("from reports.views import monthly_report_json\n", "from reports.views import monthly_report_csv, monthly_report_json\n")
total = '''
    def test_total_row(self):
        r = monthly_report_csv({"user": {"roles": ["finance"]}, "sales": SALES}, 2026, 8)
        self.assertIn("Total,,,12.34", r["body"].splitlines())
''' if fixture == "wrong-fact" else ""
t = t.replace('''

if __name__ == "__main__":''', '''

class MonthlyCsvTest(unittest.TestCase):
    def test_finance_gets_the_rows(self):
        r = monthly_report_csv({"user": {"roles": ["finance"]}, "sales": SALES}, 2026, 8)
        self.assertIn("North,Widget,3,12.34", r["body"].splitlines())

    def test_admin_gets_a_csv(self):
        r = monthly_report_csv({"user": {"roles": ["admin"]}, "sales": SALES}, 2026, 8)
        self.assertEqual(r["content_type"], "text/csv")

    def test_staff_is_refused(self):
        with self.assertRaises(Forbidden):
            monthly_report_csv({"user": {"roles": ["staff"]}, "sales": SALES}, 2026, 8)
''' + total + '''

if __name__ == "__main__":''')
p.write_text(t)
PY
  git add -A; git commit -qm "Monthly report, iteration 2.1: the monthly report as a CSV download"
fi

# pipeline-done: Sales list, iterations 1 and 2, done and left uncommitted; the user committed partway through.
# With them, the test the scope's drift risk names: each CSV's amounts against its page.
if [[ $fixture == pipeline-done ]]; then
  cat > reports/admin_views.py <<'PY'
from .auth import require_role
from .export import to_csv
from .money import format_eur
from .views import render, response

SALES_HEADER = ["Date", "Region", "Product", "Units", "Amount (EUR)"]


@require_role("finance", "admin")
def all_sales(request):
    return render("all_sales.html", sales=request["sales"])


@require_role("finance", "admin")
def all_sales_csv(request):
    lines = [[s.sold_on.isoformat(), s.region, s.product, s.units, format_eur(s.amount_cents)]
             for s in request["sales"]]
    return response(to_csv(SALES_HEADER, lines), "text/csv",
                    {"Content-Disposition": "attachment; filename=all-sales.csv"})
PY
  cat > tests/test_admin_views.py <<'PY'
import unittest
from datetime import date

from reports.admin_views import all_sales, all_sales_csv
from reports.auth import Forbidden
from reports.models import Sale

SALES = [Sale(1, "North", "Widget", 3, 1234, date(2026, 8, 3))]


class SalesListPageTest(unittest.TestCase):
    def test_finance_opens_the_page(self):
        r = all_sales({"user": {"roles": ["finance"]}, "sales": SALES})
        self.assertEqual(r["template"], "all_sales.html")

    def test_staff_cannot_open_the_page(self):
        with self.assertRaises(Forbidden):
            all_sales({"user": {"roles": ["staff"]}, "sales": SALES})


class SalesListCsvTest(unittest.TestCase):
    def test_finance_gets_every_sale(self):
        r = all_sales_csv({"user": {"roles": ["finance"]}, "sales": SALES})
        self.assertEqual(r["body"].splitlines(),
                         ["Date,Region,Product,Units,Amount (EUR)", "2026-08-03,North,Widget,3,12.34"])

    def test_admin_gets_a_csv(self):
        r = all_sales_csv({"user": {"roles": ["admin"]}, "sales": SALES})
        self.assertEqual(r["content_type"], "text/csv")

    def test_staff_is_refused(self):
        with self.assertRaises(Forbidden):
            all_sales_csv({"user": {"roles": ["staff"]}, "sales": SALES})


if __name__ == "__main__":
    unittest.main()
PY
  cat > tests/test_files_match_pages.py <<'PY'
import csv
import unittest
from datetime import date

from reports.admin_views import all_sales, all_sales_csv
from reports.models import Sale
from reports.money import format_eur
from reports.views import monthly_report, monthly_report_csv

SALES = [Sale(1, "North", "Widget", 3, 1234, date(2026, 8, 3)),
         Sale(2, "South", "Gadget", 10, 123450, date(2026, 8, 20)),
         Sale(3, "North", "Widget", 1, 99, date(2026, 7, 31))]
FINANCE = {"user": {"roles": ["finance"]}, "sales": SALES}


def amounts(csv_response):
    return [row[-1] for row in list(csv.reader(csv_response["body"].splitlines()))[1:]]


# The pages show amounts through the template's eur filter, which is format_eur.
class FilesMatchPagesTest(unittest.TestCase):
    def test_the_monthly_csv_has_the_amounts_of_its_page(self):
        page = monthly_report(FINANCE, 2026, 8)["context"]["rows"]
        self.assertEqual(amounts(monthly_report_csv(FINANCE, 2026, 8)),
                         [format_eur(r["amount_cents"]) for r in page])

    def test_the_sales_list_csv_has_the_amounts_of_its_page(self):
        page = all_sales(FINANCE)["context"]["sales"]
        self.assertEqual(amounts(all_sales_csv(FINANCE)), [format_eur(s.amount_cents) for s in page])


if __name__ == "__main__":
    unittest.main()
PY
fi

if [[ -n $broken ]]; then
  mkdir -p tests/data
  cat > tests/helpers.py <<'PY'
import json
from datetime import date
from pathlib import Path

from reports.models import Sale

DATA = Path(__file__).parent / "data" / "sales.json"


def sample_sales():
    """The sales the admin pages show in the demo: July and August 2026."""
    return [Sale(s["id"], s["region"], s["product"], s["units"], s["amount_cents"], date.fromisoformat(s["sold_on"]))
            for s in json.loads(DATA.read_text())]
PY
  python3 - <<'PY'
import json
rows = []
for i, (region, product) in enumerate([("North", "Widget"), ("South", "Gadget"), ("East", "Widget"), ("West", "Gizmo")] * 3):
    rows.append({"id": i + 1, "region": region, "product": product, "units": i % 4 + 1, "amount_cents": 1250 + 75 * i,
                 "sold_on": f"2026-{7 + i % 2:02d}-{i + 3:02d}"})
open("tests/data/sales.json", "w").write(json.dumps(rows, indent=1) + "\n")
PY
  git add -A; git commit -qm "Sample sales for the tests"
  git mv tests/data/sales.json tests/data/sample-sales.json
  git commit -qm "Rename the sample data file"
fi

# The blueprint workshop-craft wrote, at the state the code is in. .blueprints is ignored, so it is not committed.
bp=.blueprints/finance-exports
mkdir -p $bp/pipelines/01-csv-downloads $bp/pipelines/02-pdf-downloads $bp/pipelines/03-download-links

cat > $bp/00-knowledge.md <<'MD'
# Knowledge

## Facts

### Reports and views
- The monthly report is a page and a JSON view, both open to any logged-in user.
  Source: reports/views.py:14, reports/views.py:20, read 2026-09-30.
- The admin sales list is a page of every sale, open to the admin role only.
  Source: reports/admin_views.py:5, templates/all_sales.html, read 2026-09-30.
- Views return `response(body, content_type, headers)`, so a download can set its own headers.
  Source: reports/views.py:10, read 2026-09-30.
- Tests call views and decorators directly with a request dict: `tests/test_views.py`, `tests/test_auth.py`.
  Source: tests/test_views.py:12, tests/test_auth.py:10, read 2026-09-30.

### Amounts
- Amounts are stored in cents and shown in euros with two decimals through `format_eur`; the JSON export
  uses it too.
  Source: reports/money.py:1, reports/export.py:7, read 2026-09-30.

### Access
- A user's roles arrive with the request; the login that sets them is not in this repo.
  Source: reports/auth.py:9, read 2026-09-30.

## Decisions

- The task covers two reports, the monthly report and the admin sales list, each as CSV and PDF.
  Why: the finance team uses them for the month-end close.
  Rules out: downloads of other pages.
  Decided by the user on 2026-09-30.
- Finance and admins get the downloads and the sales list page; everyone else keeps what they see today.
  Why: admins see the sales list today and need the same files; finance prints the page it downloads.
  Rules out: downloads for every logged-in user.
  Decided by the user on 2026-09-30.
- One access rule: `require_role` takes one or more roles, and the downloads use
  `require_role("finance", "admin")`. `finance` is added to `ROLES`; `require_role("admin")` keeps working.
  Why: one access check for every view.
  Rules out: a second decorator next to `require_role`.
  Decided by the user on 2026-09-30.
- Giving people the finance role is not part of the task.
  Why: roles come from the login, which is managed outside this repo.
  Rules out: a role admin page or a role table in this repo.
  Decided by the user on 2026-09-30.
- The files are built from the same rows the pages show.
  Why: a file must never disagree with its page.
  Rules out: a separate query for the exports.
  Decided by the user on 2026-09-30.
- The task is split by concern into three pipelines: CSV downloads, PDF downloads, and download links.
  Why: the PDF library is the least known part, and this cut lets it start as soon as the access rule exists.
  Rules out: one pipeline per report; one pipeline for everything.
  Known cost: two waits between pipelines, and a work map to keep up.
  Decided by the user on 2026-09-30.
MD

cat > $bp/02-scope.md <<'MD'
# Scope: finance exports

Confirmed on: 2026-09-30

## Task
Finance and admins get the monthly sales report and the admin sales list as CSV and PDF downloads. Why: the
finance team works with the numbers in Excel and files a printable copy with the month-end close. Today the
monthly report is a page and a JSON view, and the sales list is a page for admins only.

## Current state
The monthly report is a page and a JSON view that any logged-in user can open. The admin sales list is a page
of every sale, for admins only. Amounts are stored in cents and shown in euros with two decimals. There are two
roles, staff and admin, and a view can require only one of them. Nothing produces a CSV or a PDF today, and the
repo has no dependencies.

## Goal
Finance and admins download both reports as CSV and PDF; everyone else sees what they see today.

## Done when
1. A finance user downloads the monthly report as CSV and as PDF.
2. A finance user downloads the admin sales list as CSV and as PDF.
3. An admin gets the same four downloads.
4. A logged-in user without the finance or admin role gets no download, and keeps the monthly page and its
   JSON.
5. Every amount in the files matches the amount on its page, in euros with two decimals.
6. The monthly page and the sales list show the download links to finance and admins only.
7. A finance user opens the sales list page; a user without the finance or admin role still cannot.

## In scope
- CSV and PDF downloads of the monthly report and of the admin sales list.
- A finance role, and an access rule that lets finance and admins through.
- The sales list page opens for finance as well as admins.
- Download links on the monthly page and on the sales list, shown to finance and admins only.

## Out of scope
- Giving people the finance role: roles come from the login, managed outside this repo. Decided by the user on
  2026-09-30.
- Downloads of any other page. Decided by the user on 2026-09-30.
- Scheduled or emailed reports. Decided by the user on 2026-09-30.

## Approach
- The files are built from the same rows the pages show, so a file never disagrees with its page.
- One access rule for all four downloads and the sales list page, checked in the view, the way the sales list
  checks its role today.
- The PDF comes from a library added for it; which one is decided in its own iteration, before the first PDF.

## Constraints
- The tests run with `python3 -m unittest`; a new dependency must install with pip.

## Risks
- The PDF library needs system fonts or a renderer the servers lack. How we would notice: the first PDF test
  fails on a fresh install.
- A file and its page drift apart when one of them changes later. How we would notice: a test that compares
  the amounts of each file with its page.

## Sources
- The request in chat, 2026-09-30.
- The repo's README: the finance team uses the monthly report for the month-end close.
MD

cat > $bp/03-workmap.md <<'MD'
# Work map: finance exports

## Pipelines

1. Pipeline 1: CSV downloads (pipelines/01-csv-downloads/)
   The finance role and the access rule that lets finance and admins through, then the CSV download of the
   monthly report and of the admin sales list, each built from the rows its page shows, and the sales list page
   opened to finance.
   Waits for: nothing.
2. Pipeline 2: PDF downloads (pipelines/02-pdf-downloads/)
   Choosing and adding the PDF library, then the PDF of each report, with the same rows and total as its page.
   Waits for: pipeline 1, Access, iteration 1.1 (release point).
   Hands over: the access rule for finance and admins, ready for the PDF views.
3. Pipeline 3: Download links (pipelines/03-download-links/)
   The download links on the monthly page and on the sales list, shown to finance and admins only.
   Waits for: pipelines 1 and 2 to finish.

## Order (derived from the waits above)

Wave 1: pipeline 1.
Wave 2: pipeline 2, once pipeline 1, Access, iteration 1.1 is done.
Wave 3: pipeline 3, once pipelines 1 and 2 are finished.
Critical path: pipeline 1 up to Access, iteration 1.1, then pipeline 2, then pipeline 3.
MD

# Pipeline 1: the lines that change with the state.
case $fixture in
  ready)
    current="Access, iteration 1.1: preliminary, the first to run; waits for nothing."
    access="- Iteration 1.1, preliminary: a finance role, and \`require_role\` lets a view through for any of several
  roles: \`require_role(\"finance\", \"admin\")\` admits finance and admins and refuses everyone else with
  \`Forbidden\`. Release point for pipeline 2."
    monthly="- Iteration 2.1, preliminary: the monthly report as a CSV download for finance and admins, with the rows the
  page shows."
    ;;
  access-done)
    current="Monthly report, iteration 2.1: next; waits for nothing."
    monthly="- Iteration 2.1, next: the monthly report as a CSV download for finance and admins, with the rows the page
  shows."
    ;;
  *)
    current="Sales list, iteration 3.1: next; waits for nothing."
    monthly="- Iteration 2.1, done: the monthly report as a CSV download for finance and admins (reports/views.py)."
    ;;
esac
sales2="- Iteration 3.2, preliminary: the sales list page opens for finance as well as admins."
base_line=""
if [[ $fixture == pipeline-done ]]; then
  current="Sales list, iteration 3.2: done; it was the last iteration of the pipeline."
  sales2="- Iteration 3.2, done: the sales list page opens for finance as well as admins (reports/admin_views.py)."
  base_line="
Base: $base_commit, HEAD when the first iteration started."
fi
if [[ $fixture != ready ]]; then
  access="- Iteration 1.1, done: a finance role, and \`require_role\` lets a view through for any of several roles
  (reports/auth.py). Release point for pipeline 2."
fi
case $fixture in
  wrong-fact)
    sales="- Iteration 3.1, next: the admin sales list as a CSV download for finance and admins: every sale the page
  shows, then the total row the page shows under them."
    ;;
  inline-csv)
    sales="- Iteration 3.1, next: the admin sales list as a CSV download for finance and admins, through the same CSV
  writer as the monthly report: every sale the page shows."
    ;;
  pipeline-done)
    sales="- Iteration 3.1, done: the admin sales list as a CSV download for finance and admins (reports/admin_views.py)."
    ;;
  *)
    sales="- Iteration 3.1, preliminary: the admin sales list as a CSV download for finance and admins, with every sale
  the page shows."
    [[ $fixture == csv-done ]] && sales="${sales/preliminary/next}"
    [[ -n $broken ]] && sales="${sales%.}; its test takes the sales from \`sample_sales()\` in tests/helpers.py."
    ;;
esac

cat > $bp/pipelines/01-csv-downloads/iterations.md <<MD
# Pipeline 1: CSV downloads

Goal: finance and admins download the monthly report and the admin sales list as CSV, through one access rule
that lets finance and admins through and refuses everyone else.
Done when: scope 1, 2, 3, 4, 5, for the CSV files, and scope 7.
Iteration size: one download, one rule or one page's access per iteration, with its test. Suggested by workshop-craft,
confirmed by the user on 2026-09-30.
Releases: pipeline 2, when Access, iteration 1.1 is done.$base_line

## Current

$current

## Iterations

### Access
$access

### Monthly report
$monthly

### Sales list
$sales
$sales2
MD

if [[ $fixture == wrong-fact ]]; then
  csv_rows="- Each CSV has one header row with the page's column names, the page's rows, and the total row the page
  shows under them.
  Why: the file is the page in Excel; finance checks the total against the page.
  Rules out: a CSV with other rows than its page.
  Decided by the user on 2026-09-30."
  page_fact="### Sales list
- The sales list page shows a total row under its rows, as the monthly page does.
  Source: templates/all_sales.html, read 2026-09-30.

"
else
  csv_rows="- Each CSV has one header row with the page's column names, then the page's rows, and no total row.
  Why: finance sums the column in Excel; a total row would be counted twice.
  Rules out: a total row in the CSV.
  Decided by the user on 2026-09-30."
  page_fact=""
fi
if [[ -n $broken ]]; then
  page_fact="### Tests
- \`sample_sales()\` in tests/helpers.py gives the twelve sales the admin pages show in the demo, over July and
  August 2026.
  Source: tests/helpers.py, read 2026-09-30.

"
fi
cat > $bp/pipelines/01-csv-downloads/knowledge.md <<MD
# Knowledge: pipeline 1, CSV downloads

## Facts

${page_fact}### CSV
- Python's \`csv\` module is in the standard library; the repo needs no dependency for the CSV files.
  Source: Python standard library, checked 2026-09-30.

## Decisions

- The CSV uses a comma separator and amounts with a dot, through \`format_eur\`, as the page shows them.
  Why: the finance team's Excel uses English settings; the user said so on 2026-09-30.
  Rules out: semicolons and decimal commas.
  Decided by the user on 2026-09-30.
$csv_rows
- The monthly file is named \`sales-YYYY-MM.csv\` and the sales list file \`all-sales.csv\`, both sent with
  \`Content-Disposition: attachment\`.
  Why: the files are kept per close, and the browser saves them instead of showing them.
  Decided by the user on 2026-09-30.
- The CSV views return \`response(body, "text/csv", headers)\`, behind \`require_role("finance", "admin")\`:
  the monthly one next to the JSON view in \`reports/views.py\`, the sales list one next to \`all_sales\` in
  \`reports/admin_views.py\`.
  Decided by the user on 2026-09-30.
MD

if [[ $fixture == ready ]]; then
  pdf_current="Library, iteration 1.1: preliminary; waits for pipeline 1, Access, iteration 1.1."
  pdf_library="- Iteration 1.1, preliminary: the PDF library, chosen with the user and added so it installs with pip, with a"
else
  pdf_current="Library, iteration 1.1: next; pipeline 1, Access, iteration 1.1 is done, so nothing is waited for."
  pdf_library="- Iteration 1.1, next: the PDF library, chosen with the user and added so it installs with pip, with a"
fi
cat > $bp/pipelines/02-pdf-downloads/iterations.md <<MD
# Pipeline 2: PDF downloads

Goal: finance and admins download the monthly report and the admin sales list as PDF, each a printable copy of
its page.
Done when: scope 1, 2, 3, 4, 5, for the PDF files.
Iteration size: one download, one rule or one page's access per iteration, with its test. Suggested by workshop-craft,
confirmed by the user on 2026-09-30.

## Current

$pdf_current

## Iterations

### Library
$pdf_library
  first test that renders a PDF, so a missing system font or renderer shows up here and not in a report.

### Monthly report
- Iteration 2.1, preliminary: the monthly report as a PDF download for finance and admins: the same rows and total
  as the page, amounts in euros with two decimals.

### Sales list
- Iteration 3.1, preliminary: the admin sales list as a PDF download for finance and admins: every sale the page
  shows, amounts in euros with two decimals.
MD

cat > $bp/pipelines/02-pdf-downloads/knowledge.md <<'MD'
# Knowledge: pipeline 2, PDF downloads

## Facts

### Dependencies
- The repo has no dependency file and no PDF library; the tests run with `python3 -m unittest`.
  Source: README.md:6, no requirements file, checked 2026-09-30.
- The pages are rendered outside this repo: `render` returns the template name and its context, so a PDF is
  built from the rows the page gets, not from the page's HTML.
  Source: reports/views.py:6, read 2026-09-30.

## Decisions

- The PDF is a printable copy of its page: the same heading, columns, rows and total, nothing else.
  Why: finance files it with the month-end close.
  Rules out: logos, summaries or anything the page does not show.
  Decided by the user on 2026-09-30.
MD

cat > $bp/pipelines/03-download-links/iterations.md <<'MD'
# Pipeline 3: Download links

Goal: the monthly page and the sales list show their download links to finance and admins only.
Done when: scope 6.
Iteration size: one download, one rule or one page's access per iteration, with its test. Suggested by workshop-craft,
confirmed by the user on 2026-09-30.

## Current

Pages, iteration 1.1: preliminary; waits for pipelines 1 and 2 to finish.

## Iterations

### Pages
- Iteration 1.1, preliminary: the monthly page shows its CSV and PDF links to finance and admins, and no download
  link to any other user; the JSON link stays as it is.
- Iteration 1.2, preliminary: the sales list shows its CSV and PDF links to finance and admins.
MD

# The lines above keep the state word they started with; this moves it into each file's status table.
python3 "$here/status_table.py" $bp/pipelines/*/iterations.md

# Numbered in file order, as one grill would have asked them: Q1 to Q6 in 00-knowledge.md, then the pipelines'.
# Then the answers to Access, iteration 1.1's mini grill, numbered by the forge session that asked them.
if [[ -n $tagged ]]; then
  perl -pi -e 's/^(  Decided by the user on [\d-]+)\.$/"$1 (Q" . ++$n . ")."/e' $bp/00-knowledge.md $bp/pipelines/*/knowledge.md
  cat >> $bp/pipelines/01-csv-downloads/knowledge.md <<'MD'
- A refused user's error names every role the view accepts: `finance or admin role required`.
  Why: support can tell from the message which roles open the view.
  Rules out: one message for every refusal.
  Decided by the user on 2026-10-01 (Q1).
- `require_role` keeps its name and takes the roles as separate arguments: `require_role("finance", "admin")`.
  Why: every `require_role("admin")` in the code keeps working as it is.
  Rules out: a list of roles; a new decorator name.
  Decided by the user on 2026-10-01 (Q2).
MD
fi

if [[ -n $record ]]; then
  mkdir -p docs/tars-reports/finance-exports
  cat > docs/tars-reports/finance-exports/01-csv-downloads.md <<'MD'
# TARS Blueprint Record: finance exports: CSV downloads

The code is the source of truth: check anything here against the code before relying on it.

State: in progress on main.

## Why
The finance team works with the monthly sales numbers in Excel and files a printable copy with the month-end close.
Finance and admins get the monthly report and the admin sales list as CSV and PDF downloads; the monthly report was a
page and a JSON view, and the sales list a page for admins only.

## Planning decisions
- The task covers two reports, the monthly report and the admin sales list, each as CSV and PDF.
  Why: the finance team uses them for the month-end close.
  Rules out: downloads of other pages.
- Finance and admins get the downloads and the sales list page; everyone else keeps what they see today.
  Why: admins see the sales list today and need the same files; finance prints the page it downloads.
  Rules out: downloads for every logged-in user.
- One access rule for every view: `require_role` takes one or more roles.
  Why: one access check for every view.
  Rules out: a second decorator next to `require_role`.
- The files are built from the same rows the pages show.
  Why: a file must never disagree with its page.
  Rules out: a separate query for the exports.
- Each CSV has a header row with the page's column names, then the page's rows, and no total row, with a comma
  separator and amounts with a dot, as the page shows them.
  Why: finance sums the column in Excel, which runs with English settings; a total row would be counted twice.
  Rules out: a total row; semicolons and decimal commas.
- The monthly file is named `sales-YYYY-MM.csv` and the sales list file `all-sales.csv`, both sent as attachments.
  Why: the files are kept per close, and the browser saves them instead of showing them.

## Not in this task
- Giving people the finance role. Why: roles come from the login, which is managed outside this repository.
- Downloads of any other page. Why: finance asked for these two reports.
- Scheduled or emailed reports. Why: finance downloads the files itself.

## What was built
- A finance role, and an access rule for one or more roles: `require_role("finance", "admin")` lets finance and admins
  through and refuses everyone else (`reports/auth.py`).
MD
  git add docs; git commit -qm "Blueprint record: finance exports"
fi
