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
FIXES = "iterations.md has the header fix as a done iteration and the other two problems as iterations"
MOVED = "Writers, iteration 3.2 is done in iterations.md and Current moved on"
CSV_PLAN = ".blueprints/finance-exports/pipelines/01-csv-downloads/iterations.md"
IN_ORDER = "The names in the status table read in order from top to bottom"
PLACED = "The status table has one new row, right after Writers, iteration 3.1 and before Writers, iteration 3.2"
NAMED = "The new row is named after the iteration the fix came out of: 3.1.a"
ROW_DONE = "The new row is DONE, and the iteration has its line under Writers"
KEPT_19 = "Every row the plan had is still there under its name, and Writers, iteration 3.2 is not started"
SPLIT_31 = "Sales list, iteration 3.1 keeps its row and its name, with the status SPLIT"
PARTS_31 = "The parts of Sales list, iteration 3.1 are the rows right under it, named 3.1.a, 3.1.b and so on down the table"
KEPT_20 = "Every row the plan had is still there under its name, and Sales list, iteration 3.2 is not started"
SPLIT_31B = "Sales list, iteration 3.1.b keeps its row and its name, with the status SPLIT"
PARTS_31B = ("The parts of Sales list, iteration 3.1.b are the rows right under it, named 3.1.b.a, 3.1.b.b and so on down "
             "the table")
KEPT_21 = ("Every row the plan had is still there under its name, with Sales list, iteration 3.1 still SPLIT, 3.1.a "
           "still DONE and 3.2 not started")
DONE_11B = "Access, iteration 1.1.b is done in iterations.md and Current moved on"
SPLIT_11 = "Access, iteration 1.1 keeps its row and its name, with the status SPLIT"
RELEASE_LINES = "The Releases line and the work map's wait still name Access, iteration 1.1, and not its part 1.1.b"
STARTS = "The reply says pipeline 2 can start"
ROW_31 = "| Writers        | 3.1 | admin correction            | DONE    |\n"
ROW_32 = "| Writers        | 3.2 | intake                      | NEXT    |\n"
FIX_ROW = "| Writers        | {} | a missing sale's correction | DONE    |\n"
LINE_32 = "- Iteration 3.2: the intake stores"
FIX_LINE = "- Iteration {}, spawned by iteration 3.1: a correction of a sale that does not exist raises `LookupError`.\n"
SALES_31 = "| Sales list | 3.1 | sales list CSV | PLANNED |\n"
SALES_31B = "| Sales list | 3.1.b | sales list CSV | PLANNED |\n"
ACCESS_11B_DONE = [("| Access | 1.1.b | several roles pass | PLANNED |", "| Access | 1.1.b | several roles pass | DONE |"),
                   ("Access, iteration 1.1.b: PLANNED, the next to run; waits for nothing.",
                    'Monthly report, iteration 2.1: NEXT; waiting on the user\'s "continue".')]
PLAN = ".blueprints/sales-sqlite/pipelines/01-sales-sqlite/iterations.md"
WAITS = "Writers, iteration 3.1 is not done in iterations.md and Current says the pipeline waits on the user"
UNCHANGED = "No file outside .blueprints changed but the TARS Blueprint Record"
IN_BOTH = "A sale a till posts is stored in SQLite and in the file"
STORE_KEPT = "reports/store.py is as the fixture left it: the write to both stores needs no change in the file store"
REQUESTED = "The app got requests for the monthly page and for its JSON, each with a region"
NO_QA = "No QA ran: no request reached the app"
QA_NAMED = "The reply names both QA skills: dogfood and reports-local"
LINK = "The JSON link on a filtered page keeps the region, and without a region it has none"
RENDER = 'return render("monthly.html", rows=rows, total=total_cents(rows), year=year, month=month, region=region)'
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


def graded(case, reply, change=None, events=()):
    """The checks of one run of the case, by text: the case's fixture repo, untouched or as `change` leaves it, no
    command run, and the reply."""
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "with_skill" / "run-1"
        (run / "outputs").mkdir(parents=True)
        (run / "outputs/final.md").write_text(reply)
        (run / "outputs/commands.txt").write_text("")
        (run / "metrics.json").write_text(json.dumps({"tool_calls": {}}))
        (run / "events.json").write_text(json.dumps(list(events)))
        subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), grader.EVALS[case]["fixture"],
                        str(run / "repo")], check=True, capture_output=True)
        if change:
            change(run / "repo")
        grader.grade(run, case)
        return {c["text"]: c["passed"] for c in json.load(open(run / "grading.json"))["expectations"]}


def served_log(text):
    """Writes the app's request log of a region-served repo."""
    return lambda repo: (repo / "serve.log").write_text(text)


def link_kept(repo):
    """The monthly view hands the page its JSON link, with the region when one was asked for."""
    view = repo / "reports/views.py"
    view.write_text(view.read_text().replace(RENDER, 'json_url = f"/reports/{year}/{month}.json" + (f"?region={region}" '
                                             'if region else "")\n    ' + RENDER[:-1] + ", json_url=json_url)"))
    page = repo / "templates/monthly.html"
    page.write_text(page.read_text().replace('href="/reports/{{ year }}/{{ month }}.json"', 'href="{{ json_url }}"'))


def plan_with(*changes):
    """Changes the store fixture's plan: the intake's row done, and each (old, new) text replaced."""
    def change(repo):
        text = (repo / PLAN).read_text()
        for old, new in [("| intake                      | NEXT    |", "| intake                      | DONE    |"), *changes]:
            assert old in text, old
            text = text.replace(old, new)
        (repo / PLAN).write_text(text)
    return change


def changed(plan, *changes):
    """Changes a fixture's plan file: each (old, new) text replaced."""
    def change(repo):
        text = (repo / plan).read_text()
        for old, new in changes:
            assert old in text, old
            text = text.replace(old, new)
        (repo / plan).write_text(text)
    return change


class AddedIterations(unittest.TestCase):
    """The checks on the name and the place of an iteration added to a plan."""

    def checks(self, case, names, *changes, plan=CSV_PLAN, reply=""):
        got = graded(case, reply, changed(plan, *changes))
        return [got.get(name) for name in names]

    def test_a_fix_named_after_the_iteration_it_came_out_of_and_put_after_it(self):
        got = self.checks(19, (PLACED, NAMED, ROW_DONE, IN_ORDER, KEPT_19), (ROW_31, ROW_31 + FIX_ROW.format("3.1.a")),
                          (LINE_32, FIX_LINE.format("3.1.a") + LINE_32), plan=PLAN)
        self.assertEqual(got, [True, True, True, True, True])

    def test_a_fix_under_the_next_free_number_is_not_named_after_it_and_reads_out_of_order(self):
        got = self.checks(19, (PLACED, NAMED, IN_ORDER), (ROW_31, ROW_31 + FIX_ROW.format("3.3")),
                          (LINE_32, FIX_LINE.format("3.3") + LINE_32), plan=PLAN)
        self.assertEqual(got, [True, False, False])

    def test_a_fix_put_at_the_end_of_its_category_is_not_where_it_runs(self):
        got = self.checks(19, (PLACED, NAMED, IN_ORDER), (ROW_32, ROW_32 + FIX_ROW.format("3.3")),
                          (LINE_32, FIX_LINE.format("3.3") + LINE_32), plan=PLAN)
        self.assertEqual(got, [False, False, True])

    def test_a_fix_that_takes_the_next_iterations_name_leaves_a_row_of_the_plan_out(self):
        got = self.checks(19, (KEPT_19,), (ROW_32, FIX_ROW.format("3.2") + ROW_32.replace("3.2", "3.3")), plan=PLAN)
        self.assertEqual(got, [False])

    def test_an_iteration_split_with_its_parts_under_it(self):
        got = self.checks(20, (SPLIT_31, PARTS_31, IN_ORDER, KEPT_20),
                          (SALES_31, "| Sales list | 3.1 | sales list CSV | SPLIT |\n"
                                     "| Sales list | 3.1.a | CSV writer moved | DONE |\n"
                                     "| Sales list | 3.1.b | sales list CSV | NEXT |\n"))
        self.assertEqual(got, [True, True, True, True])

    def test_work_put_before_the_iteration_under_the_next_free_number_is_no_split(self):
        got = self.checks(20, (SPLIT_31, PARTS_31, IN_ORDER, KEPT_20),
                          (SALES_31, "| Sales list | 3.3 | CSV writer moved | DONE |\n" + SALES_31))
        self.assertEqual(got, [False, False, False, True])

    def test_parts_under_the_next_free_numbers_are_not_named_under_the_split_iteration(self):
        got = self.checks(20, (SPLIT_31, PARTS_31, IN_ORDER),
                          (SALES_31, "| Sales list | 3.1 | sales list CSV | SPLIT |\n"
                                     "| Sales list | 3.3 | CSV writer moved | DONE |\n"
                                     "| Sales list | 3.4 | sales list CSV | NEXT |\n"))
        self.assertEqual(got, [True, False, False])

    def test_a_part_split_with_its_own_parts_under_it(self):
        got = self.checks(21, (SPLIT_31B, PARTS_31B, IN_ORDER, KEPT_21),
                          (SALES_31B, "| Sales list | 3.1.b | sales list CSV | SPLIT |\n"
                                      "| Sales list | 3.1.b.a | writer takes the columns | DONE |\n"
                                      "| Sales list | 3.1.b.b | sales list CSV | NEXT |\n"))
        self.assertEqual(got, [True, True, True, True])

    def test_a_new_letter_put_before_the_part_is_no_split_and_reads_out_of_order(self):
        got = self.checks(21, (SPLIT_31B, PARTS_31B, IN_ORDER, KEPT_21),
                          (SALES_31B, "| Sales list | 3.1.c | writer takes the columns | DONE |\n" + SALES_31B))
        self.assertEqual(got, [False, False, False, True])

    def test_a_release_point_split_and_left_as_written_once_its_last_part_is_done(self):
        got = self.checks(22, (DONE_11B, SPLIT_11, RELEASE_LINES, STARTS, IN_ORDER), *ACCESS_11B_DONE,
                          reply="Access, iteration 1.1.b is done.\n\nPipeline 2, PDF downloads, can start now.")
        self.assertEqual(got, [True, True, True, True, True])

    def test_a_split_release_point_marked_done_does_not_keep_its_status(self):
        got = self.checks(22, (SPLIT_11,), *ACCESS_11B_DONE,
                          ("| Access | 1.1 | finance role | SPLIT |", "| Access | 1.1 | finance role | DONE |"))
        self.assertEqual(got, [False])

    def test_a_releases_line_rewritten_to_name_the_last_part_is_not_as_written(self):
        got = self.checks(22, (RELEASE_LINES,), *ACCESS_11B_DONE,
                          ("when Access, iteration 1.1 is done.", "when Access, iteration 1.1.b is done."))
        self.assertEqual(got, [False])


class Grade(unittest.TestCase):
    def test_a_commit_asked_for_before_the_review_is_a_suggestion(self):
        reply = "Before the review, commit the pipeline's work, because some review skills read only commits."
        self.assertTrue(graded(23, reply)[COMMIT])

    def test_a_commit_asked_for_before_the_code_review_is_a_suggestion(self):
        reply = "Two iterations are not committed yet: commit them before the code review, since some read only commits."
        self.assertTrue(graded(23, reply)[COMMIT])

    def test_a_commit_put_off_is_not_a_suggestion(self):
        reply = "The commit and the review wait until both drift tests are done. Continue with iteration 4.1?"
        self.assertFalse(graded(23, reply)[COMMIT])

    def test_a_signed_in_page_and_json_with_a_region_are_both_requested(self):
        log = ("GET /login?as=staff 302\nGET /reports/2026/8?region=north 200\n"
               "GET /reports/2026/8.json?region=North 200\n")
        checks = graded(26, "", served_log(log))
        self.assertEqual((checks.get(REQUESTED), checks.get(UNCHANGED)), (True, True))

    def test_the_page_alone_is_not_both_requested(self):
        self.assertIs(graded(26, "", served_log("GET /reports/2026/8?region=north 200\n")).get(REQUESTED), False)

    def test_a_refused_json_request_does_not_count(self):
        log = "GET /reports/2026/8?region=north 200\nGET /reports/2026/8.json?region=north 403\n"
        self.assertIs(graded(26, "", served_log(log)).get(REQUESTED), False)

    def test_a_request_to_the_app_before_the_pick_is_qa_run(self):
        self.assertIs(graded(24, "", served_log("GET /reports/2026/8 200\n")).get(NO_QA), False)

    def test_both_qa_skills_named_with_their_names(self):
        reply = "The QA skills this session lists:\n1. dogfood\n2. reports-local\n\nWhich one should run?"
        self.assertTrue(graded(24, reply)[QA_NAMED])

    def test_a_json_link_that_keeps_the_region_only_when_one_was_asked_for(self):
        self.assertTrue(graded(29, "", link_kept)[LINK])

    def test_the_json_link_as_the_fixture_has_it_drops_the_region(self):
        self.assertIs(graded(29, "")[LINK], False)

    def test_a_request_to_the_app_after_the_iteration_is_qa_run(self):
        self.assertIs(graded(29, "", served_log("GET /reports/2026/8?region=north 200\n")).get(NO_QA), False)

    def test_an_app_started_and_its_log_deleted_is_qa_run(self):
        events = [{"kind": "bash", "command": "cd <repo> && python3 /tmp/check.py; cat serve.log; rm -f serve.log",
                   "result": ""}]
        self.assertIs(graded(29, "", events=events).get(NO_QA), False)

    def test_reading_serve_py_is_no_qa_run(self):
        events = [{"kind": "bash", "command": "cd <repo> && cat -n serve.py", "result": ""}]
        self.assertTrue(graded(29, "", events=events).get(NO_QA))

    def test_one_qa_skill_named_is_not_both(self):
        self.assertIs(graded(24, "The QA skill this session lists: dogfood. Run it?")[QA_NAMED], False)

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

    def test_a_new_iteration_with_a_lettered_name_is_read_with_its_own_line(self):
        change = plan_with(
            ("| Sales by month | 4.1 |", "| Writers        | 3.2.a | cleanup                   | NEXT    |\n| Sales by month | 4.1 |"),
            ("\n### Sales by month", "- Iteration 3.2.a, spawned by iteration 3.2: `reports/store.py` and "
                                     "`tests/test_store.py` removed.\n\n### Sales by month"))
        self.assertTrue(graded(15, "", change).get(NEXT))

    def test_a_fix_with_a_lettered_name_whose_row_is_done_is_a_done_iteration(self):
        def change(repo):
            plan = repo / grader.P1 / "iterations.md"
            text = plan.read_text()
            for old, new in [("| Sales list | 3.1 |", "| Monthly report | 2.1.a | header | DONE |\n"
                                                      "| Monthly report | 2.1.b | file name | NEXT |\n"
                                                      "| Monthly report | 2.1.c | download | PLANNED |\n"
                                                      "| Sales list | 3.1 |"),
                             ("\n### Sales list", "- Iteration 2.1.a, spawned by iteration 2.1: the header says Amount "
                                                  "(EUR) (reports/export.py).\n"
                                                  "- Iteration 2.1.b, spawned by iteration 2.1: the file name has a "
                                                  "two-digit month.\n"
                                                  "- Iteration 2.1.c, spawned by iteration 2.1: the browser saves the "
                                                  "file.\n\n### Sales list")]:
                assert old in text, old
                text = text.replace(old, new)
            plan.write_text(text)
        self.assertTrue(graded(6, "", change).get(FIXES))

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

    def test_a_current_line_on_an_iteration_named_after_the_done_one_has_moved_on(self):
        change = plan_with(("Writers, iteration 3.2: NEXT; waits for nothing.",
                            'Writers, iteration 3.2.a: NEXT; waiting on the user\'s "continue".'))
        self.assertTrue(graded(15, "", change).get(MOVED))

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
