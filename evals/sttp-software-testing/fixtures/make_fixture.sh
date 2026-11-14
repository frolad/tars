#!/usr/bin/env bash
# make_fixture.sh <case> <dir>: a small git repo in the state the user left it.
set -euo pipefail
case_name=$1; dir=$2
rm -rf "$dir"; mkdir -p "$dir"; cd "$dir"
git init -q -b main
git config user.email user@example.com; git config user.name user
mkdir -p tests; : > tests/__init__.py
case $case_name in
stage-for-commit)
  echo "# pages" > README.md
  mkdir app; : > app/__init__.py
  cat > app/pages.py <<'PY'
def paginate(items, page, per_page=10):
    """Return the items on a 1-based page."""
    start = page * per_page
    return items[start:start + per_page]


def page_count(total, per_page=10):
    return (total + per_page - 1) // per_page
PY
  cat > tests/test_pages.py <<'PY'
import unittest

from app.pages import page_count, paginate


class PageCountTest(unittest.TestCase):
    def test_rounds_up(self):
        self.assertEqual(page_count(25), 3)

    def test_empty(self):
        self.assertEqual(page_count(0), 0)


class PaginateTest(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(paginate([], 1), [])


if __name__ == "__main__":
    unittest.main()
PY
  ;;
new-write-path)
  echo "# notes" > README.md
  mkdir notes; : > notes/__init__.py
  cat > notes/store.py <<'PY'
import json
from pathlib import Path

MAX_TITLE = 100


class NotFound(Exception):
    pass


class Forbidden(Exception):
    pass


def check_title(title):
    title = (title or "").strip()
    if not title:
        raise ValueError("title is empty")
    if len(title) > MAX_TITLE:
        raise ValueError(f"title is longer than {MAX_TITLE} characters")
    return title


class NoteStore:
    """Notes kept in one JSON file: {"next_id": int, "notes": {id: note}}."""

    def __init__(self, path):
        self.path = Path(path)

    def _load(self):
        if not self.path.exists():
            return {"next_id": 1, "notes": {}}
        return json.loads(self.path.read_text())

    def _save(self, data):
        self.path.write_text(json.dumps(data))

    def create_note(self, user, title, body=""):
        data = self._load()
        note_id = data["next_id"]
        data["notes"][str(note_id)] = {"id": note_id, "owner": user, "title": check_title(title), "body": body}
        data["next_id"] = note_id + 1
        self._save(data)
        return note_id

    def get_note(self, user, note_id):
        note = self._load()["notes"].get(str(note_id))
        if note is None:
            raise NotFound(note_id)
        if note["owner"] != user:
            raise Forbidden(note_id)
        return note
PY
  cat > tests/test_store.py <<'PY'
import tempfile
import unittest
from pathlib import Path

from notes.store import NotFound, NoteStore


class NoteStoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = NoteStore(Path(self.dir.name) / "notes.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_create_and_get(self):
        note_id = self.store.create_note("ann", "Groceries", "milk")
        self.assertEqual(self.store.get_note("ann", note_id)["title"], "Groceries")

    def test_get_missing(self):
        with self.assertRaises(NotFound):
            self.store.get_note("ann", 42)


if __name__ == "__main__":
    unittest.main()
PY
  ;;
prove-test-catches-bug)
  echo "# shop" > README.md
  mkdir shop; : > shop/__init__.py
  cat > shop/cart.py <<'PY'
def subtotal(items):
    """items: list of (price_cents, qty)."""
    return sum(price * qty for price, qty in items)


def total(items, discounts=()):
    """Cart total in cents after cart-wide discounts, never below zero."""
    amount = subtotal(items)
    off = 0
    for discount in discounts:
        off += discount
        amount -= discount
    return max(amount - off, 0)
PY
  cat > shop/shipping.py <<'PY'
FREE_FROM = 5000


def shipping(total_cents):
    return 0 if total_cents >= FREE_FROM else 499
PY
  cat > tests/test_cart.py <<'PY'
import unittest

from shop.cart import subtotal, total


class CartTest(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(subtotal([(250, 2), (100, 1)]), 600)

    def test_total_without_discounts(self):
        self.assertEqual(total([(250, 2)]), 500)


if __name__ == "__main__":
    unittest.main()
PY
  ;;
refactor-first)
  echo "# reports" > README.md
  mkdir reports; : > reports/__init__.py
  cat > reports/export.py <<'PY'
import json
import sqlite3


def export_orders_json(db_path, since):
    """Orders placed on or after `since` (YYYY-MM-DD), as a JSON string."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT o.id, c.name, o.total_cents, o.placed_on FROM orders o "
            "JOIN customers c ON c.id = o.customer_id "
            "WHERE o.placed_on >= ? AND o.status != 'cancelled' ORDER BY o.placed_on",
            (since,),
        ).fetchall()
    finally:
        conn.close()
    orders = []
    for order_id, customer, total_cents, placed_on in rows:
        orders.append({
            "id": order_id,
            "customer": customer,
            "total": f"{total_cents / 100:.2f}",
            "placed_on": placed_on,
        })
    return json.dumps(orders)
PY
  cat > tests/test_export.py <<'PY'
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from reports.export import export_orders_json


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = str(Path(self.dir.name) / "shop.db")
        conn = sqlite3.connect(self.db)
        conn.executescript("""
            CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, total_cents INTEGER,
                                 placed_on TEXT, status TEXT);
            INSERT INTO customers VALUES (1, 'Ann'), (2, 'Bob');
            INSERT INTO orders VALUES (10, 1, 1250, '2026-09-01', 'paid'),
                                      (11, 2, 999, '2026-09-02', 'cancelled'),
                                      (12, 2, 4000, '2026-09-03', 'paid');
        """)
        conn.commit()
        conn.close()

    def tearDown(self):
        self.dir.cleanup()

    def test_json_skips_cancelled(self):
        orders = json.loads(export_orders_json(self.db, "2026-09-01"))
        self.assertEqual([o["id"] for o in orders], [10, 12])
        self.assertEqual(orders[0], {"id": 10, "customer": "Ann", "total": "12.50", "placed_on": "2026-09-01"})


if __name__ == "__main__":
    unittest.main()
PY
  ;;
new-seam)
  echo "# rates" > README.md
  mkdir rates; : > rates/__init__.py
  cat > rates/client.py <<'PY'
import json
import urllib.request

RATES_URL = "https://rates.example.com/latest"


def fetch_rates(base="EUR"):
    """Latest exchange rates for `base`, as a dict of currency -> rate."""
    with urllib.request.urlopen(f"{RATES_URL}?base={base}", timeout=5) as response:
        return json.loads(response.read())["rates"]
PY
  cat > rates/convert.py <<'PY'
def convert(amount_cents, rate):
    """Amount in cents converted at `rate`, rounded to whole cents."""
    return round(amount_cents * rate)
PY
  cat > tests/test_convert.py <<'PY'
import unittest

from rates.convert import convert


class ConvertTest(unittest.TestCase):
    def test_rounds_to_cents(self):
        self.assertEqual(convert(1000, 1.0855), 1086)


if __name__ == "__main__":
    unittest.main()
PY
  ;;
cases-from-recon)
  echo "# media" > README.md
  mkdir media docs; : > media/__init__.py
  cat > media/images.py <<'PY'
PLACEHOLDER = "/img/missing.png"


def fix_image(entity, files):
    """An image whose own file is gone points at the placeholder."""
    src = entity["data"].get("src", "")
    if src.startswith("/files/") and src[len("/files/"):] not in files:
        return {**entity, "data": {**entity["data"], "src": PLACEHOLDER}}
    return entity
PY
  cat > media/citations.py <<'PY'
import re

DAY_MONTH_YEAR = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")


def fix_citation(entity):
    """A citation with its date as YYYY-MM-DD, which the Lexical importer reads; no date becomes "n.d."."""
    data = dict(entity["data"])
    date = (data.get("date") or "").strip()
    if not date:
        data["date"] = "n.d."
    else:
        match = DAY_MONTH_YEAR.match(date)
        if match:
            day, month, year = match.groups()
            data["date"] = f"{year}-{int(month):02d}-{int(day):02d}"
    return {**entity, "data": data}
PY
  cat > media/fix.py <<'PY'
from media.images import fix_image


def fix_document(doc, files):
    """A copy of a Draft.js document with its entities fixed, the ones inside a note's own document too."""
    entity_map = {}
    for key, entity in doc.get("entityMap", {}).items():
        if entity.get("type") == "note":
            entity = {**entity, "data": {**entity["data"], "doc": fix_document(entity["data"]["doc"], files)}}
        elif entity.get("type") == "image":
            entity = fix_image(entity, files)
        entity_map[key] = entity
    return {**doc, "entityMap": entity_map}
PY
  cat > docs/recon.md <<'MD'
# Dry run of fix_document on the production copy, 2026-11-10

52,310 documents. What the run found, by entity:

## Images

- 4,120 images point at a file that is no longer in `files`: fixed to the placeholder.
- 312 of them sit inside a note's own document: fixed too.

## Citations (not fixed yet: fix_document doesn't call fix_citation)

- 1,204 citations have their date as day/month/year, such as `03/04/2021`, `31/12/2019` and `1/2/2020`. The
  Lexical importer reads only `YYYY-MM-DD`, so these fail to import.
- 88 citations have no date at all; the importer fails on them too.
- 97 of these broken citations sit inside a note's own document, not at the top level.
- The other 5,930 citations already have `YYYY-MM-DD` dates.

## Videos

- 813 videos have no file. Not handled yet.
MD
  cat > tests/test_fix.py <<'PY'
import unittest

from media.fix import fix_document
from media.images import PLACEHOLDER


def image(src):
    return {"type": "image", "mutability": "IMMUTABLE", "data": {"src": src}}


class FixDocumentTest(unittest.TestCase):
    def test_missing_own_file_gets_the_placeholder(self):
        doc = {"blocks": [], "entityMap": {"0": image("/files/abc")}}
        self.assertEqual(fix_document(doc, files=set())["entityMap"]["0"]["data"]["src"], PLACEHOLDER)

    def test_existing_own_file_is_kept(self):
        doc = {"blocks": [], "entityMap": {"0": image("/files/abc")}}
        self.assertEqual(fix_document(doc, files={"abc"})["entityMap"]["0"]["data"]["src"], "/files/abc")

    def test_image_inside_a_note_is_fixed(self):
        note = {"type": "note", "data": {"doc": {"blocks": [], "entityMap": {"0": image("/files/gone")}}}}
        doc = {"blocks": [], "entityMap": {"0": note}}
        fixed = fix_document(doc, files=set())
        self.assertEqual(fixed["entityMap"]["0"]["data"]["doc"]["entityMap"]["0"]["data"]["src"], PLACEHOLDER)


if __name__ == "__main__":
    unittest.main()
PY
  ;;
*) echo "unknown case $case_name" >&2; exit 1 ;;
esac
git add -A; git commit -qm "Initial"
# The user's own state: one reviewed change staged, and for the cart case unstaged work in progress.
echo "Run the tests: python3 -m unittest" >> README.md; git add README.md
if [ "$case_name" = prove-test-catches-bug ]; then
  printf '\n\ndef item_count(items):\n    return sum(qty for _, qty in items)\n' >> shop/cart.py
  sed -i 's/FREE_FROM = 5000/FREE_FROM = 4000/' shop/shipping.py
fi
