# Copyright (c) 2021, FOSS United and Contributors
# See license.txt

# import frappe
import base64
import re
import unittest

import frappe
from frappe.exceptions import ValidationError

from lms.lms.doctype.lms_quiz.lms_quiz import _save_file

# 1x1 transparent PNG, used to assert that genuine images are still accepted.
ONE_PIXEL_PNG = base64.b64decode(
	"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)
# Same matcher process_results() uses to feed data: URIs to _save_file().
IMAGE_DATA_URI_PATTERN = r'<img[^>]*src\s*=\s*["\'](?=data:)(.*?)["\']'


class TestLMSQuiz(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		frappe.get_doc({"doctype": "LMS Quiz", "title": "Test Quiz", "passing_percentage": 90}).save()

	def test_with_multiple_options(self):
		question = frappe.new_doc("LMS Question")
		question.question = "Question Multiple"
		question.type = "Choices"
		question.option_1 = "Option 1"
		question.is_correct_1 = 1
		question.option_2 = "Option 2"
		question.is_correct_2 = 1
		question.save()
		self.assertTrue(question.multiple)

	def test_with_no_correct_option(self):
		question = frappe.new_doc("LMS Question")
		question.question = "Question Multiple"
		question.type = "Choices"
		question.option_1 = "Option 1"
		question.option_2 = "Option 2"
		self.assertRaises(frappe.ValidationError, question.save)

	def test_with_no_possible_answers(self):
		question = frappe.new_doc("LMS Question")
		question.question = "Question Multiple"
		question.type = "User Input"
		self.assertRaises(frappe.ValidationError, question.save)

	def test_scores_question_with_ten_options(self):
		from lms.lms.doctype.lms_quiz.lms_quiz import verify_answer

		q = frappe.new_doc("LMS Question")
		q.question = "Ten option question"
		q.type = "Choices"
		for i in range(1, 11):
			q.set(f"option_{i}", f"opt{i}")
		q.is_correct_7 = 1
		q.save()

		self.assertTrue(verify_answer(q.name, ["opt7"]))
		self.assertFalse(verify_answer(q.name, ["opt3"]))

	def test_legacy_two_option_question_still_scores(self):
		from lms.lms.doctype.lms_quiz.lms_quiz import verify_answer

		q = frappe.new_doc("LMS Question")
		q.question = "Two option legacy"
		q.type = "Choices"
		q.option_1 = "yes"
		q.is_correct_1 = 1
		q.option_2 = "no"
		q.save()

		self.assertTrue(verify_answer(q.name, ["yes"]))
		self.assertFalse(verify_answer(q.name, ["no"]))

	def test_user_input_matches_seventh_possibility(self):
		from lms.lms.doctype.lms_quiz.lms_quiz import check_input_answers

		q = frappe.new_doc("LMS Question")
		q.question = "Ten possibility question"
		q.type = "User Input"
		for i in range(1, 11):
			q.set(f"possibility_{i}", f"answer {i}")
		q.save()

		self.assertTrue(bool(check_input_answers(q.name, "answer 7")))
		self.assertFalse(bool(check_input_answers(q.name, "totally different")))

	@classmethod
	def tearDownClass(cls) -> None:
		frappe.db.delete("LMS Quiz", "test-quiz")
		frappe.db.delete("LMS Question")


class TestQuizAnswerImageUpload(unittest.TestCase):
	"""Open-ended quiz answers may embed inline images as data: URIs that get
	written to the public /files/ directory. Only image types are allowed: an
	active-document extension (.xhtml, .js, ...) would be served inline and
	enable stored XSS on the LMS origin.
	"""

	def save_answer_image(self, mime_type, filename, content=b"image-bytes"):
		encoded = base64.b64encode(content).decode()
		answer = f'<img src="data:{mime_type};filename={filename},{encoded}">'
		return re.sub(IMAGE_DATA_URI_PATTERN, _save_file, answer)

	def test_rejects_active_document_extension(self):
		with self.assertRaises(ValidationError):
			self.save_answer_image("application/xhtml+xml", "attack.xhtml", b"<script>alert(1)</script>")

	def test_rejects_non_image_mime_type(self):
		with self.assertRaises(ValidationError):
			self.save_answer_image("text/javascript", "attack.js", b"alert(1)")

	def test_rejects_image_mime_with_active_document_extension(self):
		with self.assertRaises(ValidationError):
			self.save_answer_image("image/png", "spoof.xhtml")

	def test_accepts_genuine_image(self):
		rendered = self.save_answer_image("image/png", "answer.png", ONE_PIXEL_PNG)
		self.assertIn("/files/", rendered)

	def tearDown(self):
		for name in frappe.get_all("File", {"file_name": "answer.png"}, pluck="name"):
			frappe.delete_doc("File", name, force=True, ignore_permissions=True)


from lms.lms.doctype.lms_quiz.lms_quiz import _parse_json_arg  # noqa: E402


class TestQuizSubmissionInputValidation(unittest.TestCase):
	"""submit_quiz / check_answer json.loads the client-sent answers payload. A malformed
	payload used to surface as a raw 500 (JSONDecodeError); it now raises a clean
	validation error. Fixture-free.
	"""

	def test_valid_json_is_parsed(self):
		self.assertEqual(_parse_json_arg("[1, 2]", "answers"), [1, 2])
		self.assertEqual(_parse_json_arg('{"a": 1}', "answers"), {"a": 1})

	def test_malformed_json_is_rejected(self):
		# Under a real request this is frappe.ValidationError; bare it raises too. The
		# contract is "reject, don't 500/parse-as-None".
		for raw in ("not json", "{bad}", "", "[1,"):
			with self.subTest(raw=raw):
				with self.assertRaises(Exception):
					_parse_json_arg(raw, "answers")


class TestCheckAnswerEmptyInput(unittest.TestCase):
	"""check_answer normalises the client answers payload before dispatching. Empty/absent
	answers used to skip the parser and reach downstream in the wrong shape: answers[0]
	(IndexError on "") or `x in None` (TypeError). It must now normalise to a list and
	reject an empty answer for input questions with a clean ValidationError. The pre-dispatch
	permission/existence checks are monkeypatched so this stays fixture-free.
	"""

	def setUp(self):
		from lms.lms.doctype.lms_quiz import lms_quiz

		self.mod = lms_quiz
		self._orig = {
			name: getattr(lms_quiz, name) for name in ("check_choice_answers", "check_input_answers")
		}
		self._orig_exists = frappe.db.exists
		self._orig_get_value = frappe.db.get_value
		self._orig_get_roles = frappe.get_roles

		self.choice_calls = []
		self.input_calls = []
		lms_quiz.check_choice_answers = lambda q, a: self.choice_calls.append(a) or []
		lms_quiz.check_input_answers = lambda q, a: self.input_calls.append(a) or []
		# question exists; live checking enabled (show_answers); admin so gate is open anyway
		frappe.db.exists = lambda *a, **k: True
		frappe.db.get_value = lambda *a, **k: 1
		frappe.get_roles = lambda *a, **k: ["System Manager"]

	def tearDown(self):
		for name, fn in self._orig.items():
			setattr(self.mod, name, fn)
		frappe.db.exists = self._orig_exists
		frappe.db.get_value = self._orig_get_value
		frappe.get_roles = self._orig_get_roles

	# `answers` is a whitelisted str param; Frappe's own type wrapper rejects a bare
	# None before the body, so the realistic empty value to test here is "" (and the
	# JSON strings that parse to empty/null), not Python None.

	def test_empty_choice_answers_normalise_to_list(self):
		# No selection on a choice question is legitimate. Dispatch with [], never crash.
		for raw in ("", "[]"):
			with self.subTest(raw=raw):
				self.choice_calls.clear()
				self.mod.check_answer("Q", "QN", "Choices", raw)
				self.assertEqual(self.choice_calls, [[]])

	def test_blank_input_answers_dispatch_empty_string(self):
		# A blank input answer ("" / [] / the [null]/[""] the UI emits for an untouched
		# field) scores as incorrect: it's coerced to "" and dispatched, never throwing
		# and never IndexError-ing on answers[0].
		for raw in ("", "[]", "[null]", '[""]'):
			with self.subTest(raw=raw):
				self.input_calls.clear()
				self.mod.check_answer("Q", "QN", "Input", raw)
				self.assertEqual(self.input_calls, [""])

	def test_non_list_answers_are_rejected(self):
		for raw in ('{"a": 1}', '"str"', "42"):
			with self.subTest(raw=raw):
				with self.assertRaises(ValidationError):
					self.mod.check_answer("Q", "QN", "Choices", raw)

	def test_valid_input_answer_reaches_checker(self):
		self.input_calls.clear()
		self.mod.check_answer("Q", "QN", "Input", '["my answer"]')
		self.assertEqual(self.input_calls, ["my answer"])


class TestQuizResultValidation(unittest.TestCase):
	"""submit_quiz validates the results payload item-by-item before process_results reads
	result["question_name"] and result["answer"][0]. Malformed items must raise a clean
	ValidationError, not a 500 deep in scoring. Fixture-free (validator is pure).
	"""

	def setUp(self):
		from lms.lms.doctype.lms_quiz.lms_quiz import _validate_quiz_results

		self.fn = _validate_quiz_results

	def test_wellformed_and_blank_results_pass(self):
		# Only coarse shape is enforced here; a blank/absent answer is NOT rejected (the UI
		# emits [null] for a skipped question; process_results normalises it to "").
		self.fn([])  # empty submission is fine
		self.fn([{"question_name": "Q1", "answer": ["opt1"]}])
		self.fn([{"question_name": "Q1", "answer": ["a", "b"]}])
		self.fn([{"question_name": "Q1"}])  # missing answer
		self.fn([{"question_name": "Q1", "answer": None}])
		self.fn([{"question_name": "Q1", "answer": []}])
		self.fn([{"question_name": "Q1", "answer": [None]}])  # blank open-ended

	def test_malformed_items_are_rejected(self):
		cases = [
			[{}],  # no question_name
			[{"question_name": "", "answer": ["x"]}],  # empty question_name
			[{"question_name": "Q", "answer": "opt1"}],  # answer not a list -> would iterate chars
			["not a dict"],
			[None],
		]
		for results in cases:
			with self.subTest(results=results):
				with self.assertRaises(ValidationError):
					self.fn(results)


from datetime import timedelta
from frappe.utils import add_days, add_to_date, get_datetime, now_datetime
from lms.lms.doctype.lms_quiz.lms_quiz import (
	get_quiz_schedule_info,
	start_quiz_attempt,
	save_quiz_progress,
	submit_quiz,
	auto_finalize_expired_attempt,
)


class TestQuizScheduling(unittest.TestCase):
	def setUp(self):
		self.cleanup_records = []
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		for dt, name in reversed(self.cleanup_records):
			if frappe.db.exists(dt, name):
				frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

	def create_question(self, prompt="What is 2+2?"):
		q = frappe.new_doc("LMS Question")
		q.question = prompt
		q.type = "Choices"
		q.option_1 = "4"
		q.is_correct_1 = 1
		q.option_2 = "5"
		q.is_correct_2 = 0
		q.save()
		self.cleanup_records.append(("LMS Question", q.name))
		return q

	def create_quiz(self, title, enable_scheduling=0, **kwargs):
		quiz = frappe.new_doc("LMS Quiz")
		quiz.title = title
		quiz.passing_percentage = 50
		quiz.enable_quiz_scheduling = enable_scheduling
		for k, v in kwargs.items():
			setattr(quiz, k, v)
		q = self.create_question(f"Question for {title}")
		quiz.append("questions", {"question": q.name, "marks": 10})
		quiz.save()
		self.cleanup_records.append(("LMS Quiz", quiz.name))
		return quiz

	def test_normal_quiz_without_scheduling_works_with_empty_fields(self):
		"""Test A: Normal quiz with empty schedule fields validates and works normally."""
		quiz = self.create_quiz("Normal Unscheduled Quiz", enable_scheduling=0)
		self.assertEqual(quiz.enable_quiz_scheduling, 0)
		self.assertIsNone(quiz.quiz_start_date)

		info = get_quiz_schedule_info(quiz.name)
		self.assertFalse(info["is_scheduled"])
		self.assertTrue(info["is_available"])

	def test_scheduled_quiz_validates_required_fields(self):
		"""Test B: Scheduled quiz requires start/end dates, valid duration, and end > start."""
		# Missing dates
		with self.assertRaises(frappe.ValidationError):
			self.create_quiz("Scheduled Missing Dates", enable_scheduling=1)

		# End datetime earlier than start datetime
		now = now_datetime()
		with self.assertRaises(frappe.ValidationError):
			self.create_quiz(
				"Scheduled Inverted Dates",
				enable_scheduling=1,
				quiz_start_date=str(now.date()),
				quiz_start_time="14:00:00",
				quiz_end_date=str(now.date()),
				quiz_end_time="12:00:00",
				duration=30,
			)

		# Valid dates and duration
		quiz = self.create_quiz(
			"Scheduled Valid Quiz",
			enable_scheduling=1,
			quiz_start_date=str(now.date()),
			quiz_start_time="08:00:00",
			quiz_end_date=str(add_days(now.date(), 1)),
			quiz_end_time="18:00:00",
			duration=30,
		)
		self.assertEqual(quiz.enable_quiz_scheduling, 1)

	def test_quiz_availability_status_upcoming_available_expired(self):
		"""Test B & C: Check upcoming, available, and expired statuses."""
		now = now_datetime()
		# Upcoming
		upcoming = self.create_quiz(
			"Upcoming Quiz",
			enable_scheduling=1,
			quiz_start_date=str(add_days(now.date(), 1)),
			quiz_start_time="10:00:00",
			quiz_end_date=str(add_days(now.date(), 2)),
			quiz_end_time="10:00:00",
			duration=20,
		)
		up_info = get_quiz_schedule_info(upcoming.name)
		self.assertEqual(up_info["status"], "upcoming")
		self.assertFalse(up_info["is_available"])

		# Expired
		expired = self.create_quiz(
			"Expired Quiz",
			enable_scheduling=1,
			quiz_start_date=str(add_days(now.date(), -2)),
			quiz_start_time="10:00:00",
			quiz_end_date=str(add_days(now.date(), -1)),
			quiz_end_time="10:00:00",
			duration=20,
		)
		exp_info = get_quiz_schedule_info(expired.name)
		self.assertEqual(exp_info["status"], "expired")
		self.assertFalse(exp_info["is_available"])

		# Available
		avail = self.create_quiz(
			"Available Quiz",
			enable_scheduling=1,
			quiz_start_date=str(add_days(now.date(), -1)),
			quiz_start_time="10:00:00",
			quiz_end_date=str(add_days(now.date(), 1)),
			quiz_end_time="10:00:00",
			duration=20,
		)
		av_info = get_quiz_schedule_info(avail.name)
		self.assertEqual(av_info["status"], "available")
		self.assertTrue(av_info["is_available"])

	def test_start_attempt_and_countdown_effective_deadline(self):
		"""Test B & C: Starting attempt returns earlier of (start+duration, closing)."""
		now = now_datetime()
		# Quiz closes in 15 minutes, duration is 30 minutes -> effective deadline is closing (15 mins)
		quiz = self.create_quiz(
			"Effective Deadline Quiz",
			enable_scheduling=1,
			quiz_start_date=str(now.date()),
			quiz_start_time=str((now - timedelta(hours=1)).time()),
			quiz_end_date=str(now.date()),
			quiz_end_time=str((now + timedelta(minutes=15)).time()),
			duration=30,
		)
		res = start_quiz_attempt(quiz.name)
		self.assertTrue(res.get("attempt"))
		self.cleanup_records.append(("LMS Quiz Attempt", res["attempt"]))
		# Remaining seconds should be approximately 15 minutes (<= 900 seconds)
		self.assertLessEqual(res["remaining_seconds"], 900)
		self.assertGreater(res["remaining_seconds"], 800)

		# Refresh / reconnect should return the SAME attempt without resetting timer
		res2 = start_quiz_attempt(quiz.name)
		self.assertEqual(res2["attempt"], res["attempt"])
		self.assertTrue(res2["is_resumed"])
		self.assertLessEqual(res2["remaining_seconds"], res["remaining_seconds"])

	def test_deadline_enforcement_and_late_submission(self):
		"""Test C: Submission past deadline is rejected or accepted under grace period."""
		now = now_datetime()
		# Quiz with allow_late_submission = 0
		quiz_strict = self.create_quiz(
			"Strict Deadline Quiz",
			enable_scheduling=1,
			quiz_start_date=str(now.date()),
			quiz_start_time=str((now - timedelta(hours=1)).time()),
			quiz_end_date=str(now.date()),
			quiz_end_time=str((now + timedelta(hours=1)).time()),
			duration=1,
			allow_late_submission=0,
		)
		attempt = start_quiz_attempt(quiz_strict.name)
		self.cleanup_records.append(("LMS Quiz Attempt", attempt["attempt"]))

		# Artificially set deadline in the past to test deadline enforcement
		past_deadline = now - timedelta(minutes=5)
		frappe.db.set_value("LMS Quiz Attempt", attempt["attempt"], "deadline", past_deadline)
		frappe.db.commit()

		q_row = quiz_strict.questions[0]
		results_payload = [{"question_name": q_row.question, "answer": ["4"]}]
		import json
		with self.assertRaises(frappe.ValidationError):
			submit_quiz(quiz_strict.name, json.dumps(results_payload), attempt["attempt"])

		# Now test with allow_late_submission = 1 and 10 min grace period
		quiz_grace = self.create_quiz(
			"Grace Period Quiz",
			enable_scheduling=1,
			quiz_start_date=str(now.date()),
			quiz_start_time=str((now - timedelta(hours=1)).time()),
			quiz_end_date=str(now.date()),
			quiz_end_time=str((now + timedelta(hours=1)).time()),
			duration=1,
			allow_late_submission=1,
			late_submission_grace_period=10,
		)
		attempt2 = start_quiz_attempt(quiz_grace.name)
		self.cleanup_records.append(("LMS Quiz Attempt", attempt2["attempt"]))

		# Set deadline to 3 minutes ago (within the 10 min grace period)
		past_deadline = now - timedelta(minutes=3)
		frappe.db.set_value("LMS Quiz Attempt", attempt2["attempt"], "deadline", past_deadline)
		frappe.db.commit()

		q_row2 = quiz_grace.questions[0]
		results_payload2 = [{"question_name": q_row2.question, "answer": ["4"]}]
		sub_res = submit_quiz(quiz_grace.name, json.dumps(results_payload2), attempt2["attempt"])
		self.assertTrue(sub_res.get("submission"))
		self.cleanup_records.append(("LMS Quiz Submission", sub_res["submission"]))
		self.assertTrue(sub_res.get("is_late"))

		# Submitting duplicate for the same attempt returns idempotent submission
		dup_res = submit_quiz(quiz_grace.name, json.dumps(results_payload2), attempt2["attempt"])
		self.assertEqual(dup_res["submission"], sub_res["submission"])

