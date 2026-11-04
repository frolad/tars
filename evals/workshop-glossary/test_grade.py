"""The grader's own checks: python3 -m unittest discover -s evals/workshop-glossary"""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("glossary_grade", HERE / "grade.py")
grader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)
SILENT = "The reply says nothing about a glossary or ADRs"


def graded(case, reply):
    """The checks of one run of the case, by text: the fixture repo untouched, no command run, and reply(run), the
    reply as written for a run kept, like the test workspaces, under a folder named after the skill."""
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "workshop-glossary" / "run-1"
        (run / "outputs").mkdir(parents=True)
        (run / "outputs/final.md").write_text(reply(run))
        (run / "outputs/commands.txt").write_text("")
        subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), grader.EVALS[case]["fixture"],
                        str(run / "repo")], check=True, capture_output=True)
        grader.grade(run, case)
        return {c["text"]: c["passed"] for c in json.load(open(run / "grading.json"))["expectations"]}


class Grade(unittest.TestCase):
    def test_a_link_into_the_runs_own_folder_is_not_talk_of_a_glossary(self):
        def reply(run):
            path = run / "repo/.blueprints/finance-exports/02-scope.md"
            return f"Every Done when item is met: [02-scope.md](vscode://file{path}). Commit before the review."
        self.assertTrue(graded(6, reply)[SILENT])

    def test_a_word_on_the_missing_glossary_still_fails(self):
        def reply(run):
            return "The project has no docs/GLOSSARY.md, so the merge is skipped. Commit before the review."
        self.assertFalse(graded(6, reply)[SILENT])


if __name__ == "__main__":
    unittest.main()
