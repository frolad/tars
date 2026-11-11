"""The grader's own checks: python3 -m unittest discover -s evals/workshop-forge"""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("forge_grade", HERE / "grade.py")
grader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)
COMMIT = "The reply suggests a commit"
STORED = "A sale a till posts is stored in SQLite, and not in the file"
NEXT = "In iterations.md, the iteration that is NEXT deletes the file store"
PLAN = ".blueprints/sales-sqlite/pipelines/01-sales-sqlite/iterations.md"
WAITS = "Writers, iteration 3.1 is not done in iterations.md and Current says the pipeline waits on the user"
UNCHANGED = "No file outside .blueprints changed but the TARS Blueprint Record"
IN_BOTH = "A sale a till posts is stored in SQLite and in the file"
STORE_KEPT = "reports/store.py is as the fixture left it: the write to both stores needs no change in the file store"
INTAKE_MOVED = '''from datetime import date

from .sqlite_store import add_sale


def record_sale(payload):
    return add_sale(payload["region"], payload["product"], int(payload["units"]), int(payload["amount_cents"]),
                    date.fromisoformat(payload["sold_on"]))
'''


INTAKE_BOTH = '''from datetime import date

from .sqlite_store import add_sale
from .store import append_sale


def record_sale(payload):
    sale = add_sale(payload["region"], payload["product"], int(payload["units"]), int(payload["amount_cents"]),
                    date.fromisoformat(payload["sold_on"]))
    append_sale(sale)
    return sale
'''


def graded(case, reply, change=None):
    """The checks of one run of the case, by text: the case's fixture repo, untouched or as `change` leaves it, no
    command run, and the reply."""
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "with_skill" / "run-1"
        (run / "outputs").mkdir(parents=True)
        (run / "outputs/final.md").write_text(reply)
        (run / "outputs/commands.txt").write_text("")
        (run / "metrics.json").write_text(json.dumps({"tool_calls": {}}))
        (run / "events.json").write_text("[]")
        subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), grader.EVALS[case]["fixture"],
                        str(run / "repo")], check=True, capture_output=True)
        if change:
            change(run / "repo")
        grader.grade(run, case)
        return {c["text"]: c["passed"] for c in json.load(open(run / "grading.json"))["expectations"]}


def plan_with(*changes):
    """Changes the store fixture's plan: the intake's row done, and each (old, new) text replaced."""
    def change(repo):
        text = (repo / PLAN).read_text()
        for old, new in [("| intake                      | NEXT    |", "| intake                      | DONE    |"), *changes]:
            assert old in text, old
            text = text.replace(old, new)
        (repo / PLAN).write_text(text)
    return change


class Grade(unittest.TestCase):
    def test_a_commit_asked_for_before_the_review_is_a_suggestion(self):
        reply = "Before the review, commit the pipeline's work, because some review skills read only commits."
        self.assertTrue(graded(9, reply)[COMMIT])

    def test_a_commit_put_off_is_not_a_suggestion(self):
        reply = "The commit and the review wait until both drift tests are done. Continue with iteration 4.1?"
        self.assertFalse(graded(9, reply)[COMMIT])

    def test_a_sale_the_moved_intake_stores_is_in_sqlite_only(self):
        self.assertTrue(graded(15, "", lambda repo: (repo / "reports/intake.py").write_text(INTAKE_MOVED)).get(STORED))

    def test_the_planned_cleanup_marked_next_is_the_delete(self):
        change = plan_with(("| file store deleted          | PLANNED |", "| file store deleted          | NEXT    |"))
        self.assertTrue(graded(15, "", change).get(NEXT))

    def test_a_new_iteration_whose_line_names_the_delete_is_the_delete(self):
        change = plan_with(
            ("| Sales by month | 4.1 |", "| Writers        | 3.3 | cleanup                     | NEXT    |\n| Sales by month | 4.1 |"),
            ("\n### Sales by month", "- Iteration 3.3, spawned by iteration 3.2: `reports/store.py` and "
                                     "`tests/test_store.py` removed.\n\n### Sales by month"))
        self.assertTrue(graded(15, "", change).get(NEXT))

    def test_the_sales_list_by_month_marked_next_is_not_the_delete(self):
        change = plan_with(("| a month's sales from SQLite | PLANNED |", "| a month's sales from SQLite | NEXT    |"))
        self.assertIs(graded(15, "", change).get(NEXT), False)

    def test_a_current_line_waiting_on_the_users_pick_waits_on_the_user(self):
        def change(repo):
            plan = (repo / PLAN).read_text()
            assert "Writers, iteration 3.1: NEXT; waits for nothing." in plan
            (repo / PLAN).write_text(plan.replace(
                "Writers, iteration 3.1: NEXT; waits for nothing.",
                "Writers, iteration 3.1: CURRENT; waiting on the user's pick: the write to the file, or a skip."))
        self.assertTrue(graded(16, "", change).get(WAITS))

    def test_an_iteration_done_that_waits_for_continue_does_not_wait_on_the_user(self):
        def change(repo):
            plan = (repo / PLAN).read_text()
            for old, new in [("| intake                     | NEXT    |", "| intake                     | DONE    |"),
                             ("Writers, iteration 3.1: NEXT; waits for nothing.",
                              'Writers, iteration 3.2: NEXT; waiting on the user\'s "continue".')]:
                assert old in plan, old
                plan = plan.replace(old, new)
            (repo / PLAN).write_text(plan)
        self.assertIs(graded(16, "", change).get(WAITS), False)

    def test_the_write_to_both_stores_built_before_the_pick_is_a_file_changed(self):
        def change(repo):
            intake = repo / "reports/intake.py"
            intake.write_text(intake.read_text().replace("    append_sale(sale)\n",
                                                         "    add_sale(sale)\n    append_sale(sale)\n"))
        self.assertIs(graded(16, "", change).get(UNCHANGED), False)

    def test_a_question_about_a_missed_caller_before_any_code_waits_on_the_user_with_no_file_changed(self):
        def change(repo):
            plan = (repo / PLAN).read_text()
            assert "Writers, iteration 3.1: NEXT; waits for nothing." in plan
            (repo / PLAN).write_text(plan.replace(
                "Writers, iteration 3.1: NEXT; waits for nothing.",
                "Writers, iteration 3.1: CURRENT; waiting on the user: what to do with jobs/stock_alert.py."))
        checks = graded(18, "", change)
        self.assertEqual((checks.get(WAITS), checks.get(UNCHANGED)), (True, True))

    def test_a_sale_the_intake_writes_to_both_stores_is_in_both(self):
        self.assertTrue(graded(17, "", lambda repo: (repo / "reports/intake.py").write_text(INTAKE_BOTH)).get(IN_BOTH))

    def test_a_sale_stored_in_sqlite_only_is_not_in_both(self):
        sqlite_only = lambda repo: (repo / "reports/intake.py").write_text(INTAKE_MOVED)
        self.assertIs(graded(17, "", sqlite_only).get(IN_BOTH), False)

    def test_a_file_store_with_a_new_function_is_not_as_the_fixture_left_it(self):
        def change(repo):
            with (repo / "reports/store.py").open("a") as f:
                f.write("\n\ndef append_sales(sales):\n    for sale in sales:\n        append_sale(sale)\n")
        self.assertIs(graded(17, "", change).get(STORE_KEPT), False)


if __name__ == "__main__":
    unittest.main()
