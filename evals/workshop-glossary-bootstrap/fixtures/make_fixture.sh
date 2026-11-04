#!/usr/bin/env bash
# make_fixture.sh <fixture> <dir>: the toolshed repo, a tool library's app with three areas (catalog, members,
# loans), built by dated commits so the tests pass at HEAD and git shows when and why tools stopped being deleted.
# bare: no glossary, no decision records, .blueprints ignored.
# proposed: bare after the turn that proposed the catalog's first group: the working file at Catalog, group 1.
# context: bare with a CONTEXT.md glossary committed, after the turn that proposed the catalog's first group for it.
set -euo pipefail
fixture=$1; dir=$2
case $fixture in bare|proposed|context) ;; *) echo "unknown fixture: $fixture" >&2; exit 2 ;; esac
here=$(cd "$(dirname "$0")" && pwd)
rm -rf "$dir"; mkdir -p "$dir"; cd "$dir"
git init -q -b main
git config user.email sam@example.com; git config user.name Sam
commit() {  # commit <date> <message>
  git add -A; GIT_AUTHOR_DATE="$1T10:00:00+00:00" GIT_COMMITTER_DATE="$1T10:00:00+00:00" git commit -qm "$2"
}
mkdir -p catalog members loans templates/catalog templates/members templates/loans tests
: > catalog/__init__.py; : > members/__init__.py; : > loans/__init__.py; : > tests/__init__.py
printf '__pycache__/\n.blueprints/\n' > .gitignore
cat > README.md <<'MD'
# toolshed

The web app of the Riverside Tool Library. Members borrow tools for a week at a time; volunteers run the shed
on Saturdays.

Run the tests: `python3 -m unittest`
MD
cat > web.py <<'PY'
def render(template, **context):
    return {"template": template, "context": context}


def eur(cents):
    return f"{cents // 100}.{cents % 100:02d}"
PY
cat > catalog/models.py <<'PY'
from dataclasses import dataclass

CONDITIONS = ("good", "fair", "worn")


@dataclass
class Category:
    id: int
    name: str


@dataclass
class Kit:
    id: int
    name: str


@dataclass
class Item:
    id: int
    name: str
    category_id: int
    condition: str
    deposit_cents: int
    powered: bool = False
    kit_id: int | None = None
PY
cat > catalog/store.py <<'PY'
def by_category(items, category_id):
    return [i for i in items if i.category_id == category_id]


def kit_items(items, kit_id):
    return [i for i in items if i.kit_id == kit_id]


def remove(items, item):
    items.remove(item)
PY
cat > catalog/views.py <<'PY'
from web import render

from .store import by_category, remove


def browse(request, category_id=None):
    items = request["items"] if category_id is None else by_category(request["items"], category_id)
    return render("catalog/browse.html", items=items, categories=request["categories"])


def item_detail(request, item):
    return render("catalog/item.html", item=item)


def remove_item(request, item):
    remove(request["items"], item)
    return render("catalog/removed.html", item=item)
PY
cat > templates/catalog/browse.html <<'HTML'
<h1>Browse tools</h1>
<nav>{% for c in categories %}<a href="?category={{ c.id }}">{{ c.name }}</a>{% endfor %}</nav>
<table>
  <tr><th>Tool</th><th>Condition</th><th>Deposit (EUR)</th></tr>
  {% for i in items %}
  <tr><td><a href="/tools/{{ i.id }}">{{ i.name }}</a>{% if i.kit_id %} (part of a kit){% endif %}</td>
      <td>{{ i.condition|title }}</td><td>{{ i.deposit_cents|eur }}</td></tr>
  {% endfor %}
</table>
<a href="/tools/new">Add a tool</a>
HTML
cat > templates/catalog/item.html <<'HTML'
<h1>{{ item.name }}</h1>
<p>Condition: {{ item.condition|title }}. Deposit: {{ item.deposit_cents|eur }} EUR.</p>
{% if item.powered %}<p>Power tool: you need the induction before you can borrow it.</p>{% endif %}
{% if item.kit_id %}<p>Lent as a kit: every tool of the kit goes out and comes back together.</p>{% endif %}
<form method="post" action="/tools/{{ item.id }}/remove"><button>Remove tool</button></form>
HTML
cat > templates/catalog/add.html <<'HTML'
<h1>Add a tool</h1>
<form method="post">
  <label>Name <input name="name"></label>
  <label>Category <select name="category_id"></select></label>
  <label>Condition <select name="condition"><option>Good</option><option>Fair</option><option>Worn</option></select></label>
  <label>Deposit (EUR) <input name="deposit"></label>
  <label><input type="checkbox" name="powered"> Power tool</label>
  <label>Kit <select name="kit_id"></select></label>
</form>
HTML
cat > templates/catalog/removed.html <<'HTML'
<p>{{ item.name }} is removed.</p>
HTML
cat > tests/test_catalog.py <<'PY'
import unittest

from catalog.models import Item
from catalog.store import by_category, kit_items
from catalog.views import browse

DRILL = Item(1, "Cordless drill", 1, "good", 2000, powered=True)
SAW = Item(2, "Tenon saw", 1, "fair", 500)
CUTTER = Item(3, "Tile cutter", 2, "worn", 1500, kit_id=1)


class CatalogTest(unittest.TestCase):
    def test_browse_lists_a_category(self):
        self.assertEqual(by_category([DRILL, SAW, CUTTER], 2), [CUTTER])

    def test_a_kit_holds_its_tools(self):
        self.assertEqual(kit_items([DRILL, SAW, CUTTER], 1), [CUTTER])

    def test_browse_without_a_category_lists_every_tool(self):
        page = browse({"items": [DRILL, SAW], "categories": []})
        self.assertEqual(page["context"]["items"], [DRILL, SAW])


if __name__ == "__main__":
    unittest.main()
PY
commit 2024-05-02 "Catalog: browse, add and remove tools"

cat > members/models.py <<'PY'
from dataclasses import dataclass
from datetime import date


@dataclass
class Household:
    id: int
    address: str


@dataclass
class Account:
    id: int
    email: str
    name: str
    member_no: int
    joined_on: date
    household_id: int | None = None
    is_staff: bool = False
    inducted_on: date | None = None
PY
cat > members/store.py <<'PY'
def household_members(accounts, household_id):
    return [a for a in accounts if a.household_id == household_id]


def volunteers(accounts):
    return [a for a in accounts if a.is_staff]


def next_member_no(accounts):
    return max((a.member_no for a in accounts), default=1000) + 1
PY
cat > members/views.py <<'PY'
from web import render

from .store import household_members, volunteers


def join(request):
    return render("members/join.html")


def profile(request):
    account = request["user"]
    others = [a for a in household_members(request["accounts"], account.household_id) if a.id != account.id] \
        if account.household_id else []
    return render("members/profile.html", account=account, household=others)


def volunteer_list(request):
    return render("members/volunteers.html", volunteers=volunteers(request["accounts"]))
PY
cat > templates/members/join.html <<'HTML'
<h1>Become a member</h1>
<p>One membership covers your household: add the people you live with, and each gets a member number.</p>
<form method="post">
  <label>Name <input name="name"></label>
  <label>Email <input name="email"></label>
  <label>People you live with <textarea name="household"></textarea></label>
</form>
HTML
cat > templates/members/profile.html <<'HTML'
<h1>My membership</h1>
<p>Member number: {{ account.member_no }}. Member since {{ account.joined_on }}.</p>
{% if account.inducted_on %}<p>Induction: done on {{ account.inducted_on }}. You can borrow power tools.</p>
{% else %}<p>Induction: not yet. Book one on a Saturday to borrow power tools.</p>{% endif %}
{% if household %}<p>Your household: {% for a in household %}{{ a.name }} {% endfor %}</p>{% endif %}
HTML
cat > templates/members/volunteers.html <<'HTML'
<h1>Volunteers</h1>
<ul>{% for a in volunteers %}<li>{{ a.name }}</li>{% endfor %}</ul>
HTML
cat > tests/test_members.py <<'PY'
import unittest
from datetime import date

from members.models import Account
from members.store import household_members, next_member_no, volunteers

ANA = Account(1, "ana@example.com", "Ana", 1001, date(2024, 6, 1), household_id=7, is_staff=True)
BEN = Account(2, "ben@example.com", "Ben", 1002, date(2024, 6, 1), household_id=7)


class MembersTest(unittest.TestCase):
    def test_a_household_lists_its_members(self):
        self.assertEqual(household_members([ANA, BEN], 7), [ANA, BEN])

    def test_volunteers_are_staff_accounts(self):
        self.assertEqual(volunteers([ANA, BEN]), [ANA])

    def test_member_numbers_count_up(self):
        self.assertEqual(next_member_no([ANA, BEN]), 1003)


if __name__ == "__main__":
    unittest.main()
PY
commit 2024-06-10 "Members: join, profile and volunteers"

cat > loans/models.py <<'PY'
from dataclasses import dataclass
from datetime import date


@dataclass
class Loan:
    id: int
    item_id: int
    account_id: int
    out_on: date
    due_on: date
    returned_on: date | None = None


@dataclass
class Reservation:
    id: int
    item_id: int
    account_id: int
    placed_on: date
PY
cat > loans/rules.py <<'PY'
from datetime import timedelta

LOAN_DAYS = 7
MAX_OUT = 3
LATE_FEE_CENTS_PER_DAY = 50


def due_date(out_on):
    return out_on + timedelta(days=LOAN_DAYS)


def can_borrow(account, item, open_loans):
    if item.powered and account.inducted_on is None:
        return False
    return len(open_loans) < MAX_OUT


def late_fee(loan, today):
    days = ((loan.returned_on or today) - loan.due_on).days
    return max(days, 0) * LATE_FEE_CENTS_PER_DAY
PY
cat > loans/views.py <<'PY'
from web import render

from .rules import can_borrow


def my_loans(request):
    mine = [l for l in request["loans"] if l.account_id == request["user"].id]
    return render("loans/mine.html", loans=mine)


def borrow(request, item):
    open_loans = [l for l in request["loans"] if l.account_id == request["user"].id and l.returned_on is None]
    return render("loans/borrow.html", item=item, allowed=can_borrow(request["user"], item, open_loans))


def place_hold(request, item):
    return render("loans/hold.html", item=item)
PY
cat > templates/loans/mine.html <<'HTML'
<h1>My loans</h1>
<table>
  <tr><th>Tool</th><th>Out since</th><th>Return by</th><th>Late fee (EUR)</th></tr>
  {% for l in loans %}<tr><td>{{ l.item_id }}</td><td>{{ l.out_on }}</td><td>{{ l.due_on }}</td><td>{{ l|late_fee|eur }}</td></tr>{% endfor %}
</table>
HTML
cat > templates/loans/borrow.html <<'HTML'
<h1>Borrow {{ item.name }}</h1>
{% if allowed %}<p>Return it within a week. Leave the deposit at the shed when you pick it up.</p>
{% else %}<p>You can't borrow it yet: you have three tools out, or it is a power tool and you need the induction.</p>{% endif %}
<a href="/tools/{{ item.id }}/hold">Place a hold</a>
HTML
cat > templates/loans/hold.html <<'HTML'
<h1>Hold placed</h1>
<p>We keep {{ item.name }} for you when it comes back. You'll get an email.</p>
HTML
cat > tests/test_loans.py <<'PY'
import unittest
from datetime import date

from catalog.models import Item
from loans.models import Loan
from loans.rules import can_borrow, due_date, late_fee
from members.models import Account

DRILL = Item(1, "Cordless drill", 1, "good", 2000, powered=True)
SAW = Item(2, "Tenon saw", 1, "fair", 500)
NEW = Account(1, "ana@example.com", "Ana", 1001, date(2024, 6, 1))


class LoansTest(unittest.TestCase):
    def test_a_loan_is_due_a_week_later(self):
        self.assertEqual(due_date(date(2024, 9, 7)), date(2024, 9, 14))

    def test_no_power_tool_before_the_induction(self):
        self.assertFalse(can_borrow(NEW, DRILL, []))
        self.assertTrue(can_borrow(NEW, SAW, []))

    def test_three_tools_out_at_most(self):
        self.assertFalse(can_borrow(NEW, SAW, [object()] * 3))

    def test_late_fee_per_day(self):
        loan = Loan(1, 2, 1, date(2024, 9, 7), date(2024, 9, 14), returned_on=date(2024, 9, 17))
        self.assertEqual(late_fee(loan, date(2024, 9, 20)), 150)


if __name__ == "__main__":
    unittest.main()
PY
commit 2024-09-01 "Loans: borrow, holds and late fees"

# Tools stop being deleted: the why is only in this commit's message.
python3 - <<'PY'
from pathlib import Path
m = Path("catalog/models.py")
m.write_text(m.read_text().replace("    kit_id: int | None = None\n", "    kit_id: int | None = None\n    retired: bool = False\n"))
Path("catalog/store.py").write_text('''def lendable(items):
    return [i for i in items if not i.retired]


def by_category(items, category_id):
    return [i for i in lendable(items) if i.category_id == category_id]


def kit_items(items, kit_id):
    return [i for i in items if i.kit_id == kit_id]


def retire(item):
    item.retired = True
''')
v = Path("catalog/views.py")
v.write_text(v.read_text().replace("from .store import by_category, remove", "from .store import by_category, lendable, retire")
    .replace('items = request["items"] if', 'items = lendable(request["items"]) if')
    .replace("def remove_item(request, item):\n    remove(request[\"items\"], item)\n    return render(\"catalog/removed.html\", item=item)",
             "def retire_item(request, item):\n    retire(item)\n    return render(\"catalog/retired.html\", item=item)"))
i = Path("templates/catalog/item.html")
i.write_text(i.read_text().replace('/remove"><button>Remove tool</button>', '/retire"><button>Retire tool</button>'))
Path("templates/catalog/removed.html").unlink()
Path("templates/catalog/retired.html").write_text("<p>{{ item.name }} is retired: it is no longer lent, and its loans stay on record.</p>\n")
l = Path("loans/rules.py")
l.write_text(l.read_text().replace("def can_borrow(account, item, open_loans):\n", "def can_borrow(account, item, open_loans):\n    if item.retired:\n        return False\n"))
t = Path("tests/test_catalog.py")
t.write_text(t.read_text().replace("from catalog.store import by_category, kit_items", "from catalog.store import by_category, kit_items, retire")
    .replace("\n\nif __name__", '''
    def test_a_retired_tool_is_no_longer_listed(self):
        saw = Item(4, "Hand saw", 1, "good", 500)
        retire(saw)
        self.assertEqual(browse({"items": [DRILL, saw], "categories": []})["context"]["items"], [DRILL])


if __name__'''))
PY
commit 2025-03-14 "Retire tools instead of deleting them

The insurer asks for the loan history of every tool for six years, and a deleted tool takes its loans with it."

python3 -m unittest -q 2>/dev/null || { echo "fixture tests fail" >&2; exit 1; }
find . -name __pycache__ -prune -exec rm -rf {} +

if [[ $fixture == context ]]; then
  cat > CONTEXT.md <<'MD'
# Riverside Tool Library

The language of the tool library's app.

## Language

**Tool**:
Anything the library lends, such as a drill, a ladder or a tile cutter.
_Avoid_: item, equipment

**Deposit**:
The money a member leaves when borrowing a tool, paid back when the tool comes back undamaged.

**Condition**:
How worn a tool is: Good or Worn.

**Member**:
A person who has joined the library and may borrow tools.
_Avoid_: user, customer

## Relationships

- A **Member** borrows a **Tool** and leaves its **Deposit**.
MD
  commit 2025-06-02 "Add CONTEXT.md"
fi

if [[ $fixture == proposed || $fixture == context ]]; then
  mkdir -p .blueprints/glossary-bootstrap
  cp "$here/$fixture-bootstrap.md" .blueprints/glossary-bootstrap/bootstrap.md
fi
