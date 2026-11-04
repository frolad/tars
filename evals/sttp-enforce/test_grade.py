"""The grader's own checks, on runs built from the fixture: python3 -m unittest discover -s evals/sttp-enforce"""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("enforce_grade", HERE / "grade.py")
grader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)


def graded(case, edit):
    """The checks of one run of the case, by text: the fixture repo as the run left it after edit(repo)."""
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "run-1"
        (run / "outputs").mkdir(parents=True)
        (run / "outputs/final.md").write_text("Done.")
        subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), "bare", str(run / "repo")], check=True,
                       capture_output=True)
        edit(run / "repo")
        grader.grade(run, case)
        return {c["text"]: c["passed"] for c in json.load(open(run / "grading.json"))["expectations"]}


class Grade(unittest.TestCase):
    def test_a_cli_py_that_does_not_parse_fails_the_docstring_check_and_the_run_is_graded(self):
        def break_cli(repo):
            cli = repo / "brewlog/cli.py"
            cli.write_text(cli.read_text().replace("def connect(path):", "def connect(path)"))
        self.assertFalse(graded(2, break_cli)["connect's docstring keeps only its first line"])

    def test_a_cli_py_with_an_unclosed_string_fails_the_comments_check_and_the_run_is_graded(self):
        def break_cli(repo):
            cli = repo / "brewlog/cli.py"
            cli.write_text(cli.read_text() + 'NOTE = """unclosed\n')
        self.assertFalse(graded(2, break_cli)["The comments that restate the line and the banners are gone; the why "
                                              "comment on the empty ABV stays"])


if __name__ == "__main__":
    unittest.main()
