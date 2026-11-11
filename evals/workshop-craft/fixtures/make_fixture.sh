#!/usr/bin/env bash
# make_fixture.sh <fixture> <dir>: the reports repo. base: .blueprints is not ignored by git. ignored: it is, and
# there is no blueprint yet. scope-started, scope-approved, split-proposed, review: .blueprints is ignored, and
# .blueprints/finance-exports/ holds what workshop-craft has written by that point of the conversation in the case's
# prompt. store-approved: sales kept in a JSON-lines file store, .blueprints ignored, and .blueprints/sales-sqlite/,
# a move to SQLite, with In scope approved.
set -euo pipefail
fixture=$1; dir=$2
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
if [[ $fixture == base ]]; then
  git add -A; git commit -qm "initial"
  exit 0
fi

echo ".blueprints/" >> .gitignore
if [[ $fixture == ignored ]]; then
  git add -A; git commit -qm "initial"
  exit 0
fi
if [[ $fixture == store-approved ]]; then
  printf 'data/\nbackups/\n' >> .gitignore
  mkdir -p jobs; : > jobs/__init__.py
  cat > reports/store.py <<'PY'
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .models import Sale

SALES_FILE = Path("data/sales.jsonl")


def _line(sale):
    return json.dumps({**asdict(sale), "sold_on": sale.sold_on.isoformat()}) + "\n"


def load_sales():
    if not SALES_FILE.exists():
        return []
    rows = [json.loads(l) for l in SALES_FILE.read_text().splitlines() if l.strip()]
    return [Sale(**{**r, "sold_on": date.fromisoformat(r["sold_on"])}) for r in rows]


def append_sale(sale):
    SALES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SALES_FILE.open("a") as f:
        f.write(_line(sale))


def correct_sale(sale_id, **fields):
    sales = [Sale(**{**asdict(s), **fields}) if s.id == sale_id else s for s in load_sales()]
    SALES_FILE.write_text("".join(_line(s) for s in sales))
PY
  cat > reports/app.py <<'PY'
from .store import load_sales


def handle(view, request, *args):
    """Every page gets the sales from the store before its view runs."""
    request["sales"] = load_sales()
    return view(request, *args)
PY
  cat > reports/intake.py <<'PY'
from datetime import date

from .models import Sale
from .store import append_sale, load_sales


def record_sale(payload):
    """A sale posted by a shop's till."""
    next_id = max((s.id for s in load_sales()), default=0) + 1
    sale = Sale(next_id, payload["region"], payload["product"], int(payload["units"]),
                int(payload["amount_cents"]), date.fromisoformat(payload["sold_on"]))
    append_sale(sale)
    return sale
PY
  cat >> reports/admin_views.py <<'PY'


@require_role("admin")
def correct_sale_view(request, sale_id):
    form = request["form"]
    correct_sale(sale_id, units=int(form["units"]), amount_cents=int(form["amount_cents"]))
    return {"redirect": "/admin/sales"}
PY
  sed -i 's/^from .views import render$/from .store import correct_sale\nfrom .views import render/' reports/admin_views.py
  cat > jobs/weekly_digest.py <<'PY'
from collections import defaultdict

from reports.money import format_eur
from reports.store import load_sales


def digest_text():
    """The body of the weekly email to the regional managers: sales per region."""
    totals = defaultdict(int)
    for s in load_sales():
        totals[s.region] += s.amount_cents
    return "\n".join(f"{region}: {format_eur(c)} EUR" for region, c in sorted(totals.items()))
PY
  cat > jobs/accounting_export.py <<'PY'
import csv
import io

from reports.money import format_eur
from reports.store import load_sales


def accounting_csv():
    """The file the accounting system imports every night."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "sold_on", "region", "product", "units", "amount"])
    for s in load_sales():
        w.writerow([s.id, s.sold_on.isoformat(), s.region, s.product, s.units, format_eur(s.amount_cents)])
    return out.getvalue()
PY
  cat > jobs/backup.py <<'PY'
import shutil
from datetime import date
from pathlib import Path

from reports import store


def backup(to=Path("backups")):
    """Runs every night: a dated copy of the sales."""
    to.mkdir(exist_ok=True)
    shutil.copy(store.SALES_FILE, to / f"sales-{date.today().isoformat()}.jsonl")
PY
  cat > tests/test_store.py <<'PY'
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from jobs.accounting_export import accounting_csv
from jobs.weekly_digest import digest_text
from reports import store
from reports.intake import record_sale


class StoreTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patcher = mock.patch.object(store, "SALES_FILE", Path(tmp.name) / "sales.jsonl")
        patcher.start()
        self.addCleanup(patcher.stop)
        record_sale({"region": "North", "product": "Widget", "units": "3", "amount_cents": "1234",
                     "sold_on": "2026-08-03"})

    def test_recorded_sale_is_loaded(self):
        self.assertEqual(store.load_sales()[0].sold_on, date(2026, 8, 3))

    def test_correction_replaces_the_amount(self):
        store.correct_sale(1, amount_cents=1000)
        self.assertEqual(store.load_sales()[0].amount_cents, 1000)

    def test_digest_has_region_totals(self):
        self.assertEqual(digest_text(), "North: 12.34 EUR")

    def test_accounting_csv_has_the_sale(self):
        self.assertIn("1,2026-08-03,North,Widget,3,12.34", accounting_csv())


if __name__ == "__main__":
    unittest.main()
PY
  bp=.blueprints/sales-sqlite
  mkdir -p $bp
  cat > $bp/00-knowledge.md <<'MD'
# Knowledge

## Facts

### The file store
- Sales are kept as JSON lines in `data/sales.jsonl`, through `load_sales`, `append_sale` and `correct_sale`;
  a correction rewrites the whole file.
  Source: reports/store.py, read 2026-11-02.
- Every page gets its sales from `load_sales` before its view runs: the monthly report, its JSON and the admin
  sales list.
  Source: reports/app.py:4, reports/views.py, reports/admin_views.py, read 2026-11-02.
- A till posts each sale to `record_sale`, which reads the file for the next id and appends the sale.
  Source: reports/intake.py:7, read 2026-11-02.
- An admin corrects a sale's units and amount through `correct_sale_view`.
  Source: reports/admin_views.py, read 2026-11-02.

### Other users of the store
- Besides the pages, the intake and the admin correction, three jobs use the store: the weekly digest emails the
  sales per region to the regional managers, the accounting export writes the CSV the accounting system imports
  every night, and the backup copies `data/sales.jsonl` to `backups/` every night.
  Source: jobs/weekly_digest.py, jobs/accounting_export.py, jobs/backup.py, read 2026-11-02.

### Tests and dependencies
- The tests run with `python3 -m unittest`; `tests/test_store.py` records a sale and reads it back through the
  store, the digest and the accounting CSV. The repo has no dependencies; `sqlite3` is in Python's standard
  library.
  Source: README.md:6, tests/test_store.py, read 2026-11-02.

## Decisions

- Sales are kept in SQLite, in `data/sales.db`, through Python's `sqlite3`.
  Why: two tills now post sales at the same time, and appends to the JSON-lines file can interleave.
  Rules out: a database server; another file format.
  Decided by the user on 2026-11-02.
- The weekly digest is removed.
  Why: the regional managers stopped reading it; finance confirmed nobody needs it.
  Rules out: moving it to SQLite.
  Decided by the user on 2026-11-02.
- The accounting export and the backup read SQLite: the export with the same columns, the backup copying the
  database.
  Why: accounting imports the file every night, and the backup must hold every sale.
  Decided by the user on 2026-11-02.
- The file store, `reports/store.py`, is deleted, and nothing reads or writes `data/sales.jsonl` once the task is
  done.
  Why: one place for the sales.
  Decided by the user on 2026-11-02.
- Nothing ships until the whole task is done: the app is deployed once, when ops copies production's sales from
  the file into SQLite.
  Why: ops copies the sales once, with the app stopped.
  Rules out: a release partway through the task.
  Decided by the user on 2026-11-02.
MD
  cat > $bp/02-scope.md <<'MD'
# Scope: sales in SQLite

Current: Out of scope proposed (Q12); then the self-check and the split.

## Task
Sales move from the JSON-lines file `data/sales.jsonl` to SQLite. Why: two tills now post sales at the same time,
and appends to the file can interleave. Today the pages, the intake, the admin correction and three nightly or
weekly jobs all go through the file store, `reports/store.py`.

## Current state
Every page gets its sales from the file store before its view runs. The intake appends each sale a till posts, and
an admin's correction rewrites the whole file. The weekly digest, the nightly accounting export and the nightly
backup read the file too. Nothing uses SQLite today, and the repo has no dependencies.

## Goal
Every sale is stored and read in SQLite, and the file store is gone.

## Done when
1. The monthly report, its JSON and the admin sales list show the sales stored in SQLite.
2. A sale a till posts, and an admin's correction, are stored in SQLite.
3. The nightly accounting CSV comes from SQLite, with the same columns as today.
4. The nightly backup copies the SQLite database.
5. The weekly digest is gone.
6. `reports/store.py` is deleted, and nothing reads or writes `data/sales.jsonl`.

## In scope
- Sales kept in SQLite: the pages, the intake, the admin correction, the accounting export and the backup use it.
- The weekly digest removed: nobody reads it.
- The file store, `reports/store.py`, deleted.

## Approach
- One new module reads and writes the sales in SQLite with Python's `sqlite3`; the store's callers use it.

## Constraints
- The tests run with `python3 -m unittest`; SQLite comes from Python's standard library, so no new dependency.
- Nothing ships until the whole task is done: the app is deployed once, when ops copies production's sales into
  SQLite.

## Risks
- A caller of the file store is missed and breaks once the store is deleted. How we would notice: a search for
  `reports.store` and `sales.jsonl`, and the tests.
- The accounting system rejects the new CSV. How we would notice: a test that compares its columns with today's.

## Sources
- The request in chat, 2026-11-02.
MD
  git add -A; git commit -qm "initial"
  exit 0
fi
bp=.blueprints/finance-exports
mkdir -p $bp

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

### Amounts
- Amounts are stored in cents. The JSON export shows them in euros with two decimals through `format_eur`; the pages
  show them through an `eur` template filter that is not defined in this repo, so whether it formats like
  `format_eur` is unverified.
  Source: reports/money.py:1, reports/export.py:7, templates/monthly.html:5, 7, templates/all_sales.html:5, read
  2026-09-30.

### Access
- The roles are staff and admin; there is no finance role.
  Source: reports/auth.py:1, read 2026-09-30.
- `require_role` takes one role; nothing lets two roles through one view.
  Source: reports/auth.py:20, read 2026-09-30.
- A user's roles arrive with the request; the login that sets them is not in this repo.
  Source: reports/auth.py:9, read 2026-09-30.

### Dependencies
- The repo has no dependencies and no PDF library; the tests run with `python3 -m unittest`.
  Source: README.md:6, no requirements file, checked 2026-09-30.

## Decisions

- The task covers two reports, the monthly report and the admin sales list, each as CSV and PDF.
  Why: the finance team uses them for the month-end close.
  Rules out: downloads of other pages.
  Decided by the user on 2026-09-30.
- Finance and admins get the downloads; everyone else keeps what they see today.
  Why: admins see the sales list today and need the same files.
  Rules out: downloads for every logged-in user.
  Decided by the user on 2026-09-30.
- The CSV is for working with the numbers in Excel; the PDF is a printable copy of the page, with the same rows
  and total.
  Why: the user said so, 2026-09-30.
  Rules out: a PDF with other content than its page.
  Decided by the user on 2026-09-30.
MD

if [[ $fixture == scope-started ]]; then
  cat > $bp/02-scope.md <<'MD'
# Scope: finance exports

Current: asking what counts as done (Q4 to Q7); waiting on the user.
MD
  git add -A; git commit -qm "initial"
  exit 0
fi

cat >> $bp/00-knowledge.md <<'MD'
- Giving people the finance role is not part of the task.
  Why: roles come from the login, which is managed outside this repo.
  Rules out: a role admin page or a role table in this repo.
  Decided by the user on 2026-09-30.
- The files are built from the same rows the pages show.
  Why: a file must never disagree with its page.
  Rules out: a separate query for the exports.
  Decided by the user on 2026-09-30.
- The PDF library is chosen in its own iteration, before the first PDF.
  Why: it is the only new dependency of the task.
  Decided by the user on 2026-09-30.
- Finance can open the admin sales list page too, through the same access rule as the downloads.
  Why: its download links sit on that page, and the files hold the same rows as the page.
  Rules out: links to the sales list files on other pages.
  Decided by the user on 2026-09-30.
MD

if [[ $fixture == scope-approved ]]; then
  current="Current: Out of scope proposed (Q13); then the self-check and the split."
elif [[ $fixture == split-proposed ]]; then
  current="Current: the split is proposed (Q14 to Q16); waiting on the user to confirm it."
else
  current="Current: the blueprint is written; the review waits on the user."
fi
cat > $bp/02-scope.md <<MD
# Scope: finance exports

$current

MD
cat >> $bp/02-scope.md <<'MD'
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
2. A finance user opens the admin sales list and downloads it as CSV and as PDF.
3. An admin gets the same four downloads.
4. A logged-in user without the finance or admin role gets no download, and keeps the monthly page and its
   JSON.
5. Every amount in the files matches the amount on its page, in euros with two decimals.
6. The monthly page and the sales list show the download links to finance and admins only.

## In scope
- CSV and PDF downloads of the monthly report and of the admin sales list.
- A finance role, and an access rule that lets finance and admins through, to the downloads and to the admin
  sales list page.
- Download links on the monthly page and on the sales list, shown to finance and admins only.
MD
if [[ $fixture != scope-approved ]]; then
  cat >> $bp/02-scope.md <<'MD'

## Out of scope
- Giving people the finance role: roles come from the login, managed outside this repo. Decided by the user on
  2026-09-30.
- Downloads of any other page. Decided by the user on 2026-09-30.
- Scheduled or emailed reports. Decided by the user on 2026-09-30.
MD
fi
cat >> $bp/02-scope.md <<'MD'

## Approach
- The files are built from the same rows the pages show, so a file never disagrees with its page.
- One access rule for all four downloads and the admin sales list page, checked in the view, the way the sales
  list checks its role today.
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

if [[ $fixture == review ]]; then
  cat > $bp/03-workmap.md <<'MD'
# Work map: finance exports

## Pipelines

1. Pipeline 1: CSV downloads (pipelines/01-csv-downloads/)
   The finance role and the rule that lets finance and admins through, the admin sales list page included, then
   the CSV download of the monthly report and of the sales list.
   Waits for: nothing.
2. Pipeline 2: PDF downloads (pipelines/02-pdf-downloads/)
   Choosing and adding the PDF library, then the PDF of each report, with the same rows and total as its page.
   Waits for: pipeline 1, Access, iteration 1.1 (release point).
   Hands over: the access rule for finance and admins, ready for the PDF views.
3. Pipeline 3: Download links (pipelines/03-download-links/)
   The links on the monthly page and on the sales list, shown to finance and admins only.
   Waits for: pipelines 1 and 2 to finish.

## Order (derived from the waits above)

Wave 1: pipeline 1.
Wave 2: pipeline 2, once pipeline 1, Access, iteration 1.1 is done.
Wave 3: pipeline 3, once pipelines 1 and 2 are finished.
Critical path: pipeline 1 up to Access, iteration 1.1, then pipeline 2, then pipeline 3.
MD
  mkdir -p $bp/pipelines/01-csv-downloads $bp/pipelines/02-pdf-downloads $bp/pipelines/03-download-links
  cat > $bp/pipelines/01-csv-downloads/iterations.md <<'MD'
# Pipeline 1: CSV downloads

Goal: finance and admins download both reports as CSV.
Done when: scope 1, 2, 3, 4, 5.
Iteration size: one download, one rule or one link per iteration, with its test. Suggested by workshop-craft,
confirmed by the user on 2026-09-30.
Releases: pipeline 2, when Access, iteration 1.1 is done.

## Current

Not started: Access, iteration 1.1 is next.

## Status

| Category       | #   | Title                        | Status  |
|----------------|-----|------------------------------|---------|
| Access         | 1.1 | Finance role and access rule | PLANNED |
| Monthly report | 2.1 | Monthly report as CSV        | PLANNED |
| Sales list     | 3.1 | Sales list as CSV            | PLANNED |

## Iterations

### Access
- Iteration 1.1: a finance role, and one rule that lets finance and admins through the downloads and the admin
  sales list page (reports/auth.py, reports/admin_views.py).

### Monthly report
- Iteration 2.1: finance and admins download the monthly report as CSV, amounts as on the page (reports/views.py).

### Sales list
- Iteration 3.1: finance and admins download the admin sales list as CSV (reports/admin_views.py).
MD
  cat > $bp/pipelines/02-pdf-downloads/iterations.md <<'MD'
# Pipeline 2: PDF downloads

Goal: finance and admins download both reports as PDF, with the same rows and total as the page.
Done when: scope 1, 2, 3, 4, 5.
Iteration size: one download, one rule or one link per iteration, with its test. Suggested by workshop-craft,
confirmed by the user on 2026-09-30.

## Current

Not started: waits for pipeline 1, Access, iteration 1.1.

## Status

| Category       | #   | Title                  | Status  |
|----------------|-----|------------------------|---------|
| Library        | 1.1 | Choose the PDF library | PLANNED |
| Monthly report | 2.1 | Monthly report as PDF  | PLANNED |
| Sales list     | 3.1 | Sales list as PDF      | PLANNED |

## Iterations

### Library
- Iteration 1.1: the PDF library is chosen and added; it installs with pip on a fresh setup.

### Monthly report
- Iteration 2.1: finance and admins download the monthly report as PDF, same rows and total as the page.

### Sales list
- Iteration 3.1: finance and admins download the admin sales list as PDF.
MD
  cat > $bp/pipelines/03-download-links/iterations.md <<'MD'
# Pipeline 3: Download links

Goal: finance and admins see the download links on both pages; nobody else does.
Done when: scope 6.
Iteration size: one download, one rule or one link per iteration, with its test. Suggested by workshop-craft,
confirmed by the user on 2026-09-30.

## Current

Not started: waits for pipelines 1 and 2 to finish.

## Status

| Category | #   | Title                      | Status  |
|----------|-----|----------------------------|---------|
| Pages    | 1.1 | Links on the monthly page  | PLANNED |
| Pages    | 1.2 | Links on the sales list    | PLANNED |

## Iterations

### Pages
- Iteration 1.1: the monthly page shows the CSV and PDF links to finance and admins only (templates/monthly.html).
- Iteration 1.2: the sales list shows the CSV and PDF links to finance and admins only (templates/all_sales.html).
MD
fi
git add -A; git commit -qm "initial"
