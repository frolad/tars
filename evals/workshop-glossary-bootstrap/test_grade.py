"""The grader's own checks: python3 -m unittest discover -s evals/workshop-glossary-bootstrap"""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("bootstrap_grade", HERE / "grade.py")
grader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)
NAMES = "Every `_In the code_` line of the members' proposal names a thing (Account), not a flag such as is_staff"


def graded(case, reply):
    """The checks of one run of the case, by text: the case's fixture repo untouched, and the reply."""
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "run-1"
        (run / "outputs").mkdir(parents=True)
        (run / "outputs/final.md").write_text(reply)
        (run / "outputs/commands.txt").write_text("")
        fixture = grader.EVALS[case]["fixture"]
        subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), fixture, str(run / "repo")], check=True,
                       capture_output=True)
        grader.grade(run, case)
        return {c["text"]: c["passed"] for c in json.load(open(run / "grading.json"))["expectations"]}


class Grade(unittest.TestCase):
    def test_a_members_proposal_with_no_code_names_fails_the_names_check_after_approval(self):
        self.assertFalse(graded(3, "**Member**: a person who borrows tools.")[NAMES])

    def test_a_members_proposal_with_no_code_names_fails_the_names_check_in_context_md(self):
        self.assertFalse(graded(4, "**Member**: a person who borrows tools.")[NAMES])


if __name__ == "__main__":
    unittest.main()
