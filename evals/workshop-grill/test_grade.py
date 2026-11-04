"""The grader's own checks: python3 -m unittest discover -s evals/workshop-grill"""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("grill_grade", HERE / "grade.py")
grader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grader)
TITLES = "Every question's title names its subject, not only a label such as 'Done when 4'"
OTHER = "No other skill was loaded"


def graded(eval_name, fixture, reply, commands=""):
    """The checks of one run, by text: the fixture repo untouched, the command log as extract.py writes it, and the
    reply."""
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp) / "run-1"
        (run / "outputs").mkdir(parents=True)
        (run / "outputs/final.md").write_text(reply)
        (run / "outputs/commands.txt").write_text(commands)
        (run / "metrics.json").write_text(json.dumps({"tool_calls": {}}))
        subprocess.run(["bash", str(HERE / "fixtures/make_fixture.sh"), fixture, str(run / "repo")], check=True,
                       capture_output=True)
        grader.grade(run, eval_name)
        return {c["text"]: c["passed"] for c in json.load(open(run / "grading.json"))["expectations"]}


def round_titled(title):
    return f"❓ **Q13** - **{title}**: the export has no totals row yet. Add one?\n\n➡️ Yes: finance sums by hand today.\n"


class Grade(unittest.TestCase):
    def test_a_one_word_title_names_its_subject(self):
        self.assertTrue(graded("eval-5-self-check", "self-check", round_titled("Totals"))[TITLES])

    def test_a_label_alone_is_not_a_title(self):
        self.assertFalse(graded("eval-5-self-check", "self-check", round_titled("Done when 4"))[TITLES])

    def test_listing_a_skills_folder_is_not_loading_the_skill(self):
        commands = ("$ ls -la /work/skills/workshop-forge/\n  -> total 24\n"
                    "     -rw-r--r-- 1 sam sam 7591 Oct 28 11:23 SKILL.md\n")
        self.assertTrue(graded("eval-4-light-decision", "light-decision", round_titled("Access"), commands)[OTHER])

    def test_reading_another_skill_is_loading_it(self):
        commands = "$ cat /work/skills/workshop-forge/SKILL.md\n  -> the end of the file\n"
        self.assertFalse(graded("eval-4-light-decision", "light-decision", round_titled("Access"), commands)[OTHER])


if __name__ == "__main__":
    unittest.main()
