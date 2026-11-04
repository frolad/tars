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
move-module)
  echo "# shop" > README.md
  mkdir app; : > app/__init__.py
  echo "MAX_SLUG = 40" > app/config.py
  cat > app/slugs.py <<'PY'
import re
import unicodedata

from .config import MAX_SLUG


def slugify(title):
    """A URL slug: lower case ASCII words joined by dashes, at most MAX_SLUG characters."""
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(words)[:MAX_SLUG].rstrip("-")


def unique_slug(title, taken):
    # Numbered from 2, as the old PHP site did, so existing links keep working.
    base = slugify(title)
    slug, n = base, 2
    while slug in taken:
        slug = f"{base}-{n}"
        n += 1
    return slug
PY
  cat > app/pages.py <<'PY'
from app.slugs import slugify


def page_url(page):
    return f"/pages/{slugify(page['title'])}"
PY
  cat > app/feed.py <<'PY'
from .slugs import unique_slug


def feed_ids(posts):
    taken = set()
    ids = []
    for post in posts:
        slug = unique_slug(post["title"], taken)
        taken.add(slug)
        ids.append(slug)
    return ids
PY
  cat > tests/test_slugs.py <<'PY'
import unittest

from app.feed import feed_ids
from app.pages import page_url
from app.slugs import slugify, unique_slug


class SlugTest(unittest.TestCase):
    def test_slugify_strips_accents(self):
        self.assertEqual(slugify("Crème Brûlée!"), "creme-brulee")

    def test_unique_slug_numbers_from_two(self):
        self.assertEqual(unique_slug("Hello", {"hello"}), "hello-2")

    def test_page_url(self):
        self.assertEqual(page_url({"title": "About us"}), "/pages/about-us")

    def test_feed_ids(self):
        self.assertEqual(feed_ids([{"title": "A"}, {"title": "A"}]), ["a", "a-2"])


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
