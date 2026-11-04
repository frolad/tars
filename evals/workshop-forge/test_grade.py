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


def graded(case, reply):
    """The checks of one run of the case, by text: the case's fixture repo untouched, no command run, and the reply."""
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "with_skill" / "run-1"
        (run / "outputs").mkdir(parents=True)
        (run / "outputs/final.md").write_text(reply)
        (run / "outputs/commands.txt").write_text("")
        (run / "metrics.json").write_text(json.dumps({"tool_calls": {}}))
        subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), grader.EVALS[case]["fixture"],
                        str(run / "repo")], check=True, capture_output=True)
        grader.grade(run, case)
        return {c["text"]: c["passed"] for c in json.load(open(run / "grading.json"))["expectations"]}


class Grade(unittest.TestCase):
    def test_a_commit_asked_for_before_the_review_is_a_suggestion(self):
        reply = "Before the review, commit the pipeline's work, because some review skills read only commits."
        self.assertTrue(graded(9, reply)[COMMIT])

    def test_a_commit_put_off_is_not_a_suggestion(self):
        reply = "The commit and the review wait until both drift tests are done. Continue with iteration 4.1?"
        self.assertFalse(graded(9, reply)[COMMIT])


if __name__ == "__main__":
    unittest.main()
