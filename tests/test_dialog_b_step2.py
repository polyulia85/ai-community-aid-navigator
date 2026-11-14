"""Tests for Step 2: main(argv) command-line interface (Supervisor v0.2.5, Session B).

Run from the repo root:  python -m unittest tests.test_dialog_b_step2 -v
Uses agents_fake_dialog.json and --no-isolate.
"""
import json
import os
import shutil
import tempfile
import unittest

from navigator.supervisor import dialog as D
from tests.fake_agents import FIXTURE_KB, FIXTURE_ZIPS

HERE = os.path.dirname(__file__)
AGENTS_JSON = os.path.normpath(os.path.join(HERE, "agents_fake_dialog.json"))
STORY = "I need help with housing and food."


def _write_json(tmp_dir, name, data):
    path = os.path.join(tmp_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def _write_text(tmp_dir, name, text):
    path = os.path.join(tmp_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def _shared_args(tmp_dir, out_name="out.json"):
    """Return shared CLI flags for every subcommand."""
    out = os.path.join(tmp_dir, out_name)
    return [
        "--agents", AGENTS_JSON,
        "--kb", FIXTURE_KB,
        "--zips", FIXTURE_ZIPS,
        "--no-isolate",
        "--out", out,
    ], out


class TestMainStart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_start_produces_response_file(self):
        flags, out = _shared_args(self.tmp)
        story_path = _write_text(self.tmp, "story.txt", STORY)
        rc = D.main(["start", "--story-file", story_path] + flags)
        self.assertEqual(rc, 0)
        with open(out, encoding="utf-8") as f:
            resp = json.load(f)
        self.assertEqual(resp["status"], "needs_clarification")
        self.assertEqual(resp["dialog_version"], "0.2")

    def test_start_with_ref_date(self):
        flags, out = _shared_args(self.tmp)
        story_path = _write_text(self.tmp, "story.txt", STORY)
        rc = D.main(["start", "--story-file", story_path,
                     "--ref-date", "2026-11-15"] + flags)
        self.assertEqual(rc, 0)
        with open(out, encoding="utf-8") as f:
            resp = json.load(f)
        self.assertIn(resp["status"], ("needs_clarification", "needs_confirmation"))

    def test_start_missing_story_file_arg(self):
        flags, out = _shared_args(self.tmp)
        rc = D.main(["start"] + flags)
        self.assertEqual(rc, 2)

    def test_start_nonexistent_story_file(self):
        flags, out = _shared_args(self.tmp)
        rc = D.main(["start", "--story-file", "/no/such/file.txt"] + flags)
        self.assertEqual(rc, 2)

    def test_start_bad_ref_date(self):
        flags, out = _shared_args(self.tmp)
        story_path = _write_text(self.tmp, "story.txt", STORY)
        rc = D.main(["start", "--story-file", story_path,
                     "--ref-date", "not-a-date"] + flags)
        self.assertEqual(rc, 2)

    def test_start_bad_agents_file(self):
        flags, out = _shared_args(self.tmp)
        story_path = _write_text(self.tmp, "story.txt", STORY)
        # Replace --agents value with nonexistent path
        flags[1] = "/no/such/agents.json"
        rc = D.main(["start", "--story-file", story_path] + flags)
        self.assertEqual(rc, 2)


class TestMainAnswerConfirm(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _run_start(self):
        """Run start and return (resp, out_path)."""
        flags, out = _shared_args(self.tmp, "start_out.json")
        story_path = _write_text(self.tmp, "story.txt", STORY)
        D.main(["start", "--story-file", story_path, "--ref-date", "2026-11-15"] + flags)
        with open(out, encoding="utf-8") as f:
            return json.load(f), out

    def test_full_start_answer_confirm(self):
        """start → answer → confirm round-trip via main()."""
        # start
        flags_start, out_start = _shared_args(self.tmp, "start.json")
        story_path = _write_text(self.tmp, "story.txt", STORY)
        rc = D.main(["start", "--story-file", story_path, "--ref-date", "2026-11-15"]
                    + flags_start)
        self.assertIn(rc, (0, 1))
        with open(out_start, encoding="utf-8") as f:
            start_resp = json.load(f)

        def _make_answers(questions):
            """Answer required (can_skip=False) questions with a stub; skip the rest."""
            result = []
            for q in questions:
                if q.get("can_skip", True):
                    result.append({"question_id": q["question_id"], "skipped": True})
                else:
                    # Provide a minimal valid answer for required questions
                    result.append({"question_id": q["question_id"], "answer_text": "0"})
            return result

        # If we got clarification questions, answer them
        status = start_resp["status"]
        if status == "needs_clarification":
            questions = start_resp.get("questions", [])
            answers = _make_answers(questions)
            answers_path = _write_json(self.tmp, "answers.json", answers)
            flags_ans, out_ans = _shared_args(self.tmp, "answer.json")
            rc = D.main(["answer",
                         "--case-in", out_start,
                         "--answers-file", answers_path]
                        + flags_ans)
            self.assertIn(rc, (0, 1))
            with open(out_ans, encoding="utf-8") as f:
                prev_resp = json.load(f)
        else:
            prev_resp = start_resp
            out_ans = out_start

        # Drive to confirmation if still clarifying
        for _ in range(10):
            if prev_resp.get("status") != "needs_clarification":
                break
            questions = prev_resp.get("questions", [])
            answers = _make_answers(questions)
            answers_path = _write_json(self.tmp, "answers2.json", answers)
            prev_path = os.path.join(self.tmp, "prev_tmp.json")
            with open(prev_path, "w", encoding="utf-8") as f:
                json.dump(prev_resp, f)
            flags_ans2, out_ans2 = _shared_args(self.tmp, "answer2.json")
            D.main(["answer", "--case-in", prev_path,
                    "--answers-file", answers_path] + flags_ans2)
            with open(out_ans2, encoding="utf-8") as f:
                prev_resp = json.load(f)

        # At confirmation stage
        self.assertEqual(prev_resp.get("status"), "needs_confirmation")

        # Find the out file for the last response
        last_out = os.path.join(self.tmp, "last_ans.json")
        with open(last_out, "w", encoding="utf-8") as f:
            json.dump(prev_resp, f)

        flags_conf, out_conf = _shared_args(self.tmp, "confirm.json")
        rc = D.main(["confirm", "--case-in", last_out] + flags_conf)
        self.assertEqual(rc, 0)
        with open(out_conf, encoding="utf-8") as f:
            conf_resp = json.load(f)
        self.assertEqual(conf_resp["status"], "completed")
        self.assertTrue(conf_resp["plan"]["action_cards"])

    def test_files_with_bom_are_read(self):
        """Notepad on Windows may save UTF-8 with a BOM; every input file must still be read."""
        flags, out = _shared_args(self.tmp, "bom_start.json")
        story = os.path.join(self.tmp, "story_bom.txt")
        with open(story, "w", encoding="utf-8-sig") as f:
            f.write(STORY)
        self.assertEqual(D.main(["start", "--story-file", story, "--ref-date", "2026-11-15"] + flags), 0)
        with open(out, encoding="utf-8") as f:
            first = json.load(f)
        prev = os.path.join(self.tmp, "prev_bom.json")
        with open(prev, "w", encoding="utf-8-sig") as f:
            json.dump(first, f)
        answers = os.path.join(self.tmp, "answers_bom.json")
        with open(answers, "w", encoding="utf-8-sig") as f:
            json.dump([{"question_id": q["question_id"], "skipped": True} if q["can_skip"]
                       else {"question_id": q["question_id"], "answer_text": "0"}
                       for q in first["questions"]], f)
        flags2, out2 = _shared_args(self.tmp, "bom_answer.json")
        self.assertIn(D.main(["answer", "--case-in", prev, "--answers-file", answers] + flags2), (0,))

    def test_case_in_not_an_object_is_exit_2(self):
        flags, out = _shared_args(self.tmp)
        arr = _write_json(self.tmp, "arr.json", [1, 2])
        answers = _write_json(self.tmp, "a.json", [])
        self.assertEqual(D.main(["answer", "--case-in", arr, "--answers-file", answers] + flags), 2)
        self.assertEqual(D.main(["confirm", "--case-in", arr] + flags), 2)

    def test_answer_missing_case_in(self):
        flags, out = _shared_args(self.tmp)
        answers_path = _write_json(self.tmp, "answers.json", [])
        rc = D.main(["answer", "--answers-file", answers_path] + flags)
        self.assertEqual(rc, 2)

    def test_answer_missing_answers_file(self):
        flags, out = _shared_args(self.tmp)
        story_path = _write_text(self.tmp, "story.txt", STORY)
        # Create a dummy case-in file
        dummy = _write_json(self.tmp, "prev.json", {"case": None})
        rc = D.main(["answer", "--case-in", dummy] + flags)
        self.assertEqual(rc, 2)

    def test_confirm_missing_case_in(self):
        flags, out = _shared_args(self.tmp)
        rc = D.main(["confirm"] + flags)
        self.assertEqual(rc, 2)

    def test_confirm_bad_case_in_json(self):
        flags, out = _shared_args(self.tmp)
        bad_path = _write_text(self.tmp, "bad.json", "{not json")
        rc = D.main(["confirm", "--case-in", bad_path] + flags)
        self.assertEqual(rc, 2)

    def test_failed_status_gives_exit_1(self):
        """Calling confirm with a bad case gives status=failed and exit 1."""
        flags, out = _shared_args(self.tmp)
        # Write a case-in with a deliberately invalid case (None)
        bad_case = _write_json(self.tmp, "bad_case.json", {"case": None})
        rc = D.main(["confirm", "--case-in", bad_case] + flags)
        # status=failed → exit 1
        self.assertEqual(rc, 1)
        with open(out, encoding="utf-8") as f:
            resp = json.load(f)
        self.assertEqual(resp["status"], "failed")

    def test_output_file_is_valid_json_with_indent(self):
        flags, out = _shared_args(self.tmp)
        story_path = _write_text(self.tmp, "story.txt", STORY)
        D.main(["start", "--story-file", story_path, "--ref-date", "2026-11-15"] + flags)
        raw = open(out, encoding="utf-8").read()
        # indent=2: each key starts on a new line
        self.assertIn("\n  ", raw)
        json.loads(raw)   # must parse without error


if __name__ == "__main__":
    unittest.main()
