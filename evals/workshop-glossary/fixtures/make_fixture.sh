#!/usr/bin/env bash
# make_fixture.sh <fixture> <dir>: workshop-forge's reports repo with a project glossary and one ADR committed in docs/.
# merge: workshop-forge's pipeline-done, plus the drift test the scope's Risks name, so every check is met; the
# blueprint's 00-knowledge.md has Terms for pipelines 1, 2 and 3.
# merge-asked: merge, after the turn that proposed the merge: an ADR the pipeline supersedes, the decision naming it,
# and Current waiting on the user's answers.
# iteration: workshop-forge's csv-done, the next iteration being the sales list CSV; the blueprint has no Terms.
# craft, direct: workshop-forge's ready.
# merge-bare, craft-bare: merge and craft in a project with no glossary and no ADRs; merge-bare's Finance user term
# has no Changes the glossary line, since there is no glossary to change.
set -euo pipefail
fixture=$1; dir=$2
case $fixture in
  merge|merge-asked|merge-bare) base=pipeline-done ;;
  iteration) base=csv-done ;;
  craft|direct|craft-bare) base=ready ;;
  *) echo "unknown fixture: $fixture" >&2; exit 2 ;;
esac
here=$(cd "$(dirname "$0")" && pwd)
bash "$here/../../workshop-forge/fixtures/make_fixture.sh" "$base" "$dir"
cd "$dir"
if [[ $fixture != *-bare ]]; then
mkdir -p docs/adrs
cat > docs/GLOSSARY.md <<'MD'
# Glossary

**Sale**: one sale recorded by sales staff: a product, the units, the amount and the day it was sold.
_Avoid_: order, transaction

**Region**: the sales territory a sale belongs to, as sales staff type it.

**Monthly report**: the month's sales by region and product; finance uses it for the month-end close.
_Avoid_: monthly statement

**Finance user**: a member of the finance team; sees the reports of their own region only.
MD
cat > docs/adrs/money-amounts-in-cents.md <<'MD'
# Amounts are kept in cents and turned into euros only where they are shown

Why: sums of floats drift, and finance reconciles to the cent.
Rules out: floats in the models and the queries; formatting amounts before the last step.
Decided by the team on 2026-03-02.
MD
if [[ $fixture == merge-asked ]]; then
  cat > docs/adrs/exports-json-only.md <<'MD'
# Reports are exported as JSON only

Why: the only reader of the exports was the BI import, which reads JSON.
Rules out: CSV and PDF exports.
Decided by the team on 2026-03-02.
MD
fi
git add docs; git commit -qm "Add the project glossary and the first ADR"
fi

if [[ $fixture == merge || $fixture == merge-asked || $fixture == merge-bare ]]; then
  # The check the scope's Risks name for a file and its page drifting apart, done and left uncommitted.
  cat > tests/test_drift.py <<'PY'
import unittest
from datetime import date

from reports.admin_views import all_sales, all_sales_csv
from reports.models import Sale
from reports.money import format_eur
from reports.views import monthly_report, monthly_report_csv

REQUEST = {"user": {"roles": ["finance"]},
           "sales": [Sale(1, "North", "Widget", 3, 1234, date(2026, 8, 3)), Sale(2, "South", "Gadget", 1, 500, date(2026, 8, 9))]}


class MonthlyDriftTest(unittest.TestCase):
    def test_the_csv_has_the_page_rows_and_amounts(self):
        page = monthly_report(REQUEST, 2026, 8)["context"]["rows"]
        csv = monthly_report_csv(REQUEST, 2026, 8)["body"].splitlines()[1:]
        self.assertEqual(csv, [f"{r['region']},{r['product']},{r['units']},{format_eur(r['amount_cents'])}" for r in page])


class SalesListDriftTest(unittest.TestCase):
    def test_the_csv_has_the_page_rows_and_amounts(self):
        page = all_sales(REQUEST)["context"]["sales"]
        csv = all_sales_csv(REQUEST)["body"].splitlines()[1:]
        self.assertEqual(csv, [f"{s.sold_on.isoformat()},{s.region},{s.product},{s.units},{format_eur(s.amount_cents)}"
                               for s in page])


if __name__ == "__main__":
    unittest.main()
PY
  its=.blueprints/finance-exports/pipelines/01-csv-downloads/iterations.md
  sed -i 's/^Sales list, iteration 3\.2: done; it was the last iteration of the pipeline\.$/Amount checks, iteration 4.1: done; it was the last iteration of the pipeline./' $its
  printf '\n### Amount checks\n- Iteration 4.1: a test that compares the rows and amounts of each CSV with its page\n  (tests/test_drift.py).\n' >> $its
  sed -i 's/^| Sales list | 3.2 | sales list for finance | DONE |$/&\n| Amount checks | 4.1 | CSV amounts match pages | DONE |/' $its
  cat >> .blueprints/finance-exports/00-knowledge.md <<'MD'

## Terms

- **Sales list**: the admin page of every sale, with its date, region, product, units and amount.
  _Avoid_: all sales page, sales table.
- **Finance user**: a user with the finance role; gets the report downloads and the sales list, for every region.
  Changes the glossary: a member of the finance team who sees the reports of their own region only.
  Decided by the user on 2026-09-30.
- **Printable copy**: the PDF of a report that finance files with the month-end close.
  _Avoid_: printout, hard copy.
- **Download link**: the link on a report page that starts its download, shown to finance and admins only.
MD
fi
if [[ $fixture == merge-bare ]]; then
  sed -i '/^  Changes the glossary: /,/^  Decided by the user on 2026-09-30\.$/d' .blueprints/finance-exports/00-knowledge.md
fi
if [[ $fixture == merge-asked ]]; then
  python3 - <<'PY'
from pathlib import Path
bp = Path(".blueprints/finance-exports")
k = bp / "00-knowledge.md"
k.write_text(k.read_text().replace("  Rules out: downloads of other pages.\n", "  Rules out: downloads of other pages.\n"
    "  Changes the ADR: `docs/adrs/exports-json-only.md`, which goes: the reports are no longer exported as JSON only.\n", 1))
i = bp / "pipelines/01-csv-downloads/iterations.md"
i.write_text(i.read_text().replace("Amount checks, iteration 4.1: done; it was the last iteration of the pipeline.",
    "End of the pipeline: waiting on the user for the glossary merge, entries 1 to 3."))
PY
fi
