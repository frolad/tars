#!/usr/bin/env bash
# make_fixture.sh <case> <dir>: the reports repo; light-* cases add a pipeline, self-check a scope to re-read.
set -euo pipefail
case_name=$1; dir=$2
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
if [[ $case_name == light-* ]]; then
  cat >> reports/export.py <<'PY'


def to_csv(rows):
    """Semicolon-separated, header row, amounts in euros with a dot."""
    lines = ["Region;Product;Units;Amount (EUR)"]
    for r in rows:
        lines.append(f"{r['region']};{r['product']};{r['units']};{format_eur(r['amount_cents'])}")
    return "\n".join(lines) + "\n"
PY
  cat >> tests/test_export.py <<'PY'


class ToCsvTest(unittest.TestCase):
    def test_header_and_row(self):
        from reports.export import to_csv
        rows = [{"region": "North", "product": "Widget", "units": 3, "amount_cents": 1234}]
        self.assertEqual(to_csv(rows), "Region;Product;Units;Amount (EUR)\nNorth;Widget;3;12.34\n")
PY
  mkdir -p .blueprints/csv-export
  echo ".blueprints/" >> .gitignore
  if [[ $case_name == light-clear ]]; then
    ACCESS='- Access: the CSV follows the JSON view, any logged-in staff member (decided with the user, 2026-09-22).'
    IT2='Add `monthly_report_csv` in `reports/views.py` next to `monthly_report_json`: same access rule, returns `to_csv(rows)` as `text/csv` with the file name below. One test in `tests/test_views.py`, like the JSON view tests.'
  else
    ACCESS='- Access: finance team only (scope, Done when 3). Other staff keep the page and the JSON.'
    IT2='Add a CSV download of the monthly report: a view next to `monthly_report_json` that returns `to_csv(rows)` as `text/csv` with the file name below, and its tests.'
  fi
  cat > .blueprints/csv-export/pipeline.md <<MD
# Pipeline: csv-export

Goal: finance downloads the monthly sales report as a CSV they open in Excel for the month-end close.

Current: iteration 2. Iteration 1 is done and reviewed.

## Iterations

1. Done. \`to_csv(rows)\` in \`reports/export.py\`, with its test.
2. Current. $IT2
3. Preliminary. A "CSV" link next to the JSON link on the monthly page.
MD
  cat > .blueprints/csv-export/knowledge.md <<MD
# Knowledge: csv-export

- Amounts: euros with a dot and two decimals, through \`money.format_eur\` (decided with the user, 2026-09-20).
- Separator: \`;\`, because finance opens the file in Excel with a German locale (decided, 2026-09-20).
- Header row: \`Region;Product;Units;Amount (EUR)\`. No totals row: finance sums in Excel (decided, 2026-09-20).
- File name: \`sales-YYYY-MM.csv\`, sent as \`Content-Disposition: attachment\` (decided, 2026-09-21).
$ACCESS
- Views return \`response(body, content_type, headers)\` from \`reports/views.py\`; tests call views directly
  with a request dict (\`tests/test_views.py\`).
MD
fi
if [[ $case_name == self-check ]]; then
  mkdir -p .blueprints/csv-export
  echo ".blueprints/" >> .gitignore
  cat > .blueprints/csv-export/02-scope.md <<'MD'
# Scope: csv-export

Current: every section approved (Q1-Q12). Next: the self-check of the scope, then the split.

## Task
Finance closes each month from the monthly sales report, and today copies the page's table into Excel by hand.
We add a CSV download of the monthly report that opens in Excel as it is.

## Current state
The monthly report is a page and a JSON export, both open to any logged-in staff member. Amounts are stored in
cents and shown in euros with a dot.

## Goal
Finance downloads the month's report as a file and opens it in Excel without retyping anything.

## Done when
1. The monthly report page has a "CSV" link next to the "JSON" link.
2. The CSV opens correctly in Excel.
3. Every amount in the CSV is the same as on the page, in euros with a dot.
4. Finance can download it.
5. The old exports still work.
6. The tests pass.

## In scope
- A CSV download of the monthly report, and its link on the page.

## Out of scope
- Other reports, and a totals row: finance sums in Excel. Decided by the user on 2026-09-20.

## Approach
- The CSV is built from the same rows as the page and the JSON (`monthly_sales`), amounts through `format_eur`.

## Constraints
- No new dependency.
MD
  cat > .blueprints/csv-export/00-knowledge.md <<'MD'
# Knowledge: csv-export

## Decisions
- Q4, 2026-09-20: separator `;`, because finance opens the file in Excel with a German locale.
- Q5, 2026-09-20: header row `Region;Product;Units;Amount (EUR)`, one row per region and product, no totals row.
- Q7, 2026-09-21: access follows the JSON view: any logged-in staff member. No new role.
- Q9, 2026-09-21: file name `sales-YYYY-MM.csv`, sent as an attachment.

## Facts
- Roles in `reports/auth.py`: `staff` and `admin`. There is no finance role.
- `monthly_report` and `monthly_report_json` in `reports/views.py` both use `require_login`; their tests are in
  `tests/test_views.py`.
MD
fi
git add -A; git commit -qm "initial"
