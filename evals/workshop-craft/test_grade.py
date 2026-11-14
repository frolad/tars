"""The grader's own checks: python3 -m unittest discover -s evals/workshop-craft"""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("craft_grade", HERE / "grade.py")
grader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)
ROWS = "Every iteration has a PLANNED or BLOCKED row in the status table"
PLAN = """# Pipeline 1: csv

## Status

| Category | #     | Title         | Status  |
|----------|-------|---------------|---------|
| CSV      | 1.1   | header row    | PLANNED |

## Iterations

### CSV
- Iteration 1.1: the header row.
- Iteration 1.1.a, spawned by iteration 1.1: the amount column names the currency.
"""


def graded(case, plan):
    """The checks of one run of the case, by text: the case's fixture repo with `plan` as its first pipeline's
    iterations.md, an empty reply and no command run."""
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "with_skill" / "run-1"
        (run / "outputs").mkdir(parents=True)
        (run / "outputs/final.md").write_text("")
        (run / "outputs/commands.txt").write_text("")
        (run / "metrics.json").write_text(json.dumps({"tool_calls": {}}))
        subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), grader.EVALS[case]["fixture"],
                        str(run / "repo")], check=True, capture_output=True)
        file = run / "repo" / grader.BP / "pipelines/01-csv" / grader.PIPELINE_FILE
        file.parent.mkdir(parents=True)
        file.write_text(plan)
        grader.grade(run, case)
        return {c["text"]: c["passed"] for c in json.load(open(run / "grading.json"))["expectations"]}


class Grade(unittest.TestCase):
    def test_an_iteration_with_a_lettered_name_and_no_row_of_its_own_has_no_row(self):
        self.assertIs(graded(6, PLAN).get(ROWS), False)

    def test_an_iteration_with_a_lettered_name_has_the_row_of_that_name(self):
        row = "| CSV      | 1.1   | header row    | PLANNED |\n"
        self.assertTrue(graded(6, PLAN.replace(row, row + "| CSV      | 1.1.a | amount column | PLANNED |\n")).get(ROWS))


if __name__ == "__main__":
    unittest.main()
