# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import json
import os
import re
from binascii import Error as BinasciiError

from datetime import timedelta

import frappe
from frappe import _, safe_decode
from frappe.core.doctype.file.utils import get_random_filename
from frappe.model.document import Document
from frappe.utils import cint, comma_and, escape_html, get_datetime, get_system_timezone, now_datetime
from frappe.utils.file_manager import safe_b64decode
from frappe.utils.html_utils import sanitize_html
from fuzzywuzzy import fuzz

from lms.lms.doctype.course_lesson.course_lesson import save_progress
from lms.lms.doctype.lms_question.lms_question import (
	QUESTION_CORRECTNESS_FIELDS,
	QUESTION_OPTION_FIELDS,
	QUESTION_POSSIBILITY_FIELDS,
)
from lms.lms.utils import (
	generate_slug,
)

# Quiz answers may embed inline images as data: URIs. Only raster image types are
# permitted. A data: URI with an active-document extension (.xhtml, .xsl, .html,
# .js, …) would otherwise be written to the public /files/ dir and served inline,
# enabling stored XSS on the LMS origin. SVG is excluded (script-bearing).
ALLOWED_DATAURL_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp"}


class LMSQuiz(Document):
	def before_insert(self):
		self.set_initial_release_status()

	def set_initial_release_status(self):
		if getattr(self.flags, "direct_publish", False):
			self.release_status = "Released"
			return

		course = self.course
		if not course and getattr(self, "lesson", None):
			course = frappe.db.get_value("Course Lesson", self.lesson, "course")
			self.course = course

		if not course:
			return

		course_doc = frappe.db.get_value(
			"LMS Course",
			course,
			["published", "content_release_mode"],
			as_dict=True,
		)
		if (
			course_doc
			and course_doc.published
			and course_doc.content_release_mode
			and course_doc.content_release_mode not in ("None", "")
		):
			self.release_status = "Draft"
		elif not self.release_status:
			self.release_status = "Released"

	def validate(self):
		self.validate_duplicate_questions()
		self.validate_limit()
		self.calculate_total_marks()
		self.validate_open_ended_questions()
		self.validate_schedule()

	def validate_schedule(self):
		if not getattr(self, "enable_quiz_scheduling", 0):
			return

		if not self.quiz_start_date:
			frappe.throw(_("Quiz Start Date is required when scheduling is enabled."))
		if not self.quiz_start_time:
			frappe.throw(_("Quiz Start Time is required when scheduling is enabled."))
		if not self.quiz_end_date:
			frappe.throw(_("Quiz End Date is required when scheduling is enabled."))
		if not self.quiz_end_time:
			frappe.throw(_("Quiz End Time is required when scheduling is enabled."))

		if not self.duration or cint(self.duration) <= 0:
			frappe.throw(_("Quiz Duration (Minutes) must be a positive number when scheduling is enabled."))

		start_dt = get_datetime(f"{self.quiz_start_date} {self.quiz_start_time}")
		end_dt = get_datetime(f"{self.quiz_end_date} {self.quiz_end_time}")

		if end_dt <= start_dt:
			frappe.throw(_("Quiz End Date & Time must be later than Start Date & Time."))

		if self.allow_late_submission and self.late_submission_grace_period is not None:
			if cint(self.late_submission_grace_period) < 0:
				frappe.throw(_("Late Submission Grace Period cannot be negative."))

	def validate_duplicate_questions(self):
		questions = [row.question for row in self.questions]
		rows = [i + 1 for i, x in enumerate(questions) if questions.count(x) > 1]
		if len(rows):
			frappe.throw(_("Rows {0} have the duplicate questions.").format(frappe.bold(comma_and(rows))))

	def validate_limit(self):
		if not self.shuffle_questions and self.limit_questions_to:
			self.limit_questions_to = 0

		if self.limit_questions_to and cint(self.limit_questions_to) >= len(self.questions):
			frappe.throw(_("Limit cannot be greater than or equal to the number of questions in the quiz."))

		if self.limit_questions_to and cint(self.limit_questions_to) < len(self.questions):
			marks = [question.marks for question in self.questions]
			if len(set(marks)) > 1:
				frappe.throw(_("All questions should have the same marks if the limit is set."))

	def calculate_total_marks(self):
		if len(self.questions) == 0:
			self.total_marks = 0
			self.passing_percentage = 100
			return

		if self.limit_questions_to:
			self.total_marks = sum(
				question.marks for question in self.questions[: cint(self.limit_questions_to)]
			)
		else:
			self.total_marks = sum(cint(question.marks) for question in self.questions)

	def validate_open_ended_questions(self):
		types = [question.type for question in self.questions]
		types = set(types)

		if "Open Ended" in types:
			if len(types) > 1:
				frappe.throw(
					_(
						"If you want open ended questions then make sure each question in the quiz is of open ended type."
					)
				)
			else:
				self.show_answers = 0

	def autoname(self):
		if not self.name:
			self.name = generate_slug(self.title, "LMS Quiz")

	def get_last_submission_details(self):
		"""Returns the latest submission for this user."""
		user = frappe.session.user
		if not user or user == "Guest":
			return

		result = frappe.get_all(
			"LMS Quiz Submission",
			fields="*",
			filters={"owner": user, "quiz": self.name},
			order_by="creation desc",
			page_length=1,
		)

		if result:
			return result[0]


def set_total_marks(questions: list) -> int:
	marks = 0
	for question in questions:
		marks += question.get("marks")
	return marks


def _parse_json_arg(raw, label):
	"""Parse a client-supplied JSON-string argument, raising a clean error (not a 500)."""
	try:
		return json.loads(raw)
	except (TypeError, ValueError):
		frappe.throw(_("Invalid {0} submitted.").format(label), frappe.ValidationError)


def _validate_quiz_results(results):
	"""Coarse shape check before process_results reads result["question_name"] / ["answer"].
	Rejects genuinely malformed items (non-dict, no question_name, or an answer that isn't a
	list) with a clean validation error. A blank/null answer element is NOT rejected here: the
	UI legitimately emits answer=[null] for a skipped open-ended question; process_results
	normalises those to "" so a student can still submit a partially-answered quiz."""
	for result in results:
		if not (isinstance(result, dict) and result.get("question_name")):
			frappe.throw(_("Invalid quiz results submitted."), frappe.ValidationError)
		answer = result.get("answer")
		if answer is not None and not isinstance(answer, list):
			frappe.throw(_("Invalid quiz results submitted."), frappe.ValidationError)


@frappe.whitelist()
def submit_quiz(quiz: str, results: str | None = None, attempt: str | None = None):
	if not isinstance(quiz, str):
		frappe.throw(_("Invalid quiz."), frappe.ValidationError)

	results = _parse_json_arg(results, _("quiz results")) if results else []
	if not isinstance(results, list):
		frappe.throw(_("Invalid quiz results submitted."), frappe.ValidationError)
	_validate_quiz_results(results)

	quiz_details = frappe.db.get_value(
		"LMS Quiz",
		quiz,
		[
			"name",
			"total_marks",
			"passing_percentage",
			"lesson",
			"course",
			"enable_negative_marking",
			"marks_to_cut",
			"enable_quiz_scheduling",
			"quiz_start_date",
			"quiz_start_time",
			"quiz_end_date",
			"quiz_end_time",
			"duration",
			"allow_late_submission",
			"late_submission_grace_period",
		],
		as_dict=1,
	)
	if not quiz_details:
		frappe.throw(_("Invalid quiz."), frappe.ValidationError)

	from lms.lms.permissions import can_access_quiz

	if not can_access_quiz(quiz):
		frappe.throw(_("You are not authorized to submit this quiz."), frappe.PermissionError)

	now = now_datetime()
	attempt_doc = None
	is_late = 0

	if quiz_details.enable_quiz_scheduling:
		user = frappe.session.user
		if attempt:
			if not frappe.db.exists("LMS Quiz Attempt", attempt):
				frappe.throw(_("Invalid quiz attempt."), frappe.ValidationError)
			attempt_doc = frappe.get_doc("LMS Quiz Attempt", attempt)
			if attempt_doc.quiz != quiz or attempt_doc.member != user:
				frappe.throw(_("You are not authorized to submit this attempt."), frappe.PermissionError)
		else:
			attempt_name = frappe.db.get_value(
				"LMS Quiz Attempt",
				{"quiz": quiz, "member": user, "status": "In Progress"},
				"name",
			)
			if attempt_name:
				attempt_doc = frappe.get_doc("LMS Quiz Attempt", attempt_name)
			else:
				# Check if already submitted recently (idempotent / prevent duplicate results)
				recent_attempts = frappe.get_all(
					"LMS Quiz Attempt",
					filters={"quiz": quiz, "member": user, "status": "Completed"},
					order_by="modified desc",
					limit=1,
					fields=["name", "submission"],
				)
				if recent_attempts and recent_attempts[0].submission:
					sub = frappe.get_doc("LMS Quiz Submission", recent_attempts[0].submission)
					return {
						"score": sub.score,
						"score_out_of": sub.score_out_of,
						"submission": sub.name,
						"pass": (sub.percentage or 0) >= quiz_details.passing_percentage,
						"percentage": sub.percentage or 0,
						"is_open_ended": any(r.get("type") == "Open Ended" for r in (sub.result or [])),
						"is_late": bool(sub.is_late),
					}
				frappe.throw(_("No active attempt found for this scheduled quiz."), frappe.ValidationError)

		if attempt_doc.status == "Completed" and attempt_doc.submission:
			sub = frappe.get_doc("LMS Quiz Submission", attempt_doc.submission)
			return {
				"score": sub.score,
				"score_out_of": sub.score_out_of,
				"submission": sub.name,
				"pass": (sub.percentage or 0) >= quiz_details.passing_percentage,
				"percentage": sub.percentage or 0,
				"is_open_ended": any(r.get("type") == "Open Ended" for r in (sub.result or [])),
				"is_late": bool(sub.is_late),
			}

		deadline = get_datetime(attempt_doc.deadline)
		if now > deadline:
			if not quiz_details.allow_late_submission:
				attempt_doc.status = "Expired"
				attempt_doc.save(ignore_permissions=True)
				frappe.throw(
					_("The quiz deadline has passed. Submissions are no longer accepted."),
					frappe.ValidationError,
				)
			else:
				grace_mins = cint(quiz_details.late_submission_grace_period or 5)
				grace_deadline = deadline + timedelta(minutes=grace_mins)
				if now > grace_deadline:
					attempt_doc.status = "Expired"
					attempt_doc.save(ignore_permissions=True)
					frappe.throw(
						_("The quiz deadline and late submission grace period have passed. Submissions are no longer accepted."),
						frappe.ValidationError,
					)
				else:
					is_late = 1

	data = process_results(results, quiz_details)
	is_open_ended = data["is_open_ended"]

	# Score and percentage are the submission's responsibility. Its validate()
	# runs validate_marks() + set_percentage() on save. Read them back rather
	# than recomputing here, so the two paths can't drift.
	submission = create_submission(
		quiz,
		data["results"],
		quiz_details.total_marks,
		quiz_details.passing_percentage,
		started_at=attempt_doc.start_time if attempt_doc else None,
		submitted_at=now,
		is_late=is_late,
		attempt=attempt_doc.name if attempt_doc else None,
	)
	percentage = submission.percentage or 0
	save_progress_after_quiz(quiz_details, percentage)

	if attempt_doc:
		attempt_doc.status = "Completed"
		attempt_doc.submission = submission.name
		attempt_doc.saved_answers = json.dumps(results)
		attempt_doc.save(ignore_permissions=True)

	return {
		"score": submission.score,
		"score_out_of": submission.score_out_of,
		"submission": submission.name,
		"pass": percentage >= quiz_details.passing_percentage,
		"percentage": percentage,
		"is_open_ended": is_open_ended,
		"is_late": bool(is_late),
	}


def process_results(results: list, quiz_details: dict):
	is_open_ended = False

	for result in results:
		question_details = frappe.db.get_value(
			"LMS Quiz Question",
			{"parent": quiz_details.name, "question": result["question_name"]},
			["question", "marks", "question_detail", "type"],
			as_dict=1,
		)
		# The question must belong to this quiz. A stale/forged submission can name a row
		# that no longer resolves for quiz_details; reject cleanly instead of NoneType-500ing.
		if not question_details:
			frappe.throw(_("Invalid quiz results submitted."), frappe.ValidationError)

		# Normalise the answer to a non-empty list of strings so re.sub/join/[0] below can't
		# choke on a null/empty element (the UI sends [null] for a skipped open-ended answer).
		result["answer"] = [a if isinstance(a, str) else "" for a in (result.get("answer") or [])] or [""]

		result["question_name"] = question_details.question
		result["question"] = question_details.question_detail
		result["marks_out_of"] = question_details.marks

		if question_details.type != "Open Ended":
			if question_details.type == "User Input":
				correct = bool(check_input_answers(question_details.question, result["answer"][0]))
			else:
				correct = verify_answer(question_details.question, result["answer"])
			result["answer"] = ", ".join(result["answer"])
			if correct:
				result["marks"] = question_details.marks
			else:
				result["marks"] = -quiz_details.marks_to_cut if quiz_details.enable_negative_marking else 0
			result["is_correct"] = 1 if correct else 0

		else:
			is_open_ended = True
			result["is_correct"] = 0
			answer = re.sub(r'<img[^>]*src\s*=\s*["\'](?=data:)(.*?)["\']', _save_file, result["answer"][0])
			# Defense-in-depth: the answer is later rendered in the instructor's
			# privileged grading view (QuizSubmission.vue). The frontend already
			# wraps it in sanitizeRichHTML, but a student-controlled answer must
			# not be stored as live HTML that other surfaces could render raw.
			result["answer"] = sanitize_html(answer, always_sanitize=True)

	return {
		"results": results,
		"is_open_ended": is_open_ended,
	}


def verify_answer(question: str, answer: list):
	question_details = get_question_details(question)

	if question_details.multiple:
		for option_field, correctness_field in zip(
			QUESTION_OPTION_FIELDS, QUESTION_CORRECTNESS_FIELDS, strict=True
		):
			option = question_details[option_field]
			is_correct = question_details[correctness_field]
			if option in answer and not is_correct:
				return False
			if is_correct and option not in answer:
				return False
		return True

	correct = False
	for option_field, correctness_field in zip(
		QUESTION_OPTION_FIELDS, QUESTION_CORRECTNESS_FIELDS, strict=True
	):
		if question_details[option_field] in answer:
			correct = question_details[correctness_field]
	return correct


def _save_file(match: re.Match) -> str:
	data = match.group(1).split("data:")[1]
	headers, content = data.split(",")
	mtype = headers.split(";", 1)[0]

	if not mtype.lower().startswith("image/"):
		frappe.throw(_("Only image data is allowed in quiz answers."))

	if isinstance(content, str):
		content = content.encode("utf-8")
	if b"," in content:
		content = content.split(b",")[1]

	try:
		content = safe_b64decode(content)
	except BinasciiError:
		frappe.flags.has_dataurl = True
		return f'<img src="#broken-image" alt="{get_corrupted_image_msg()}"'

	if "filename=" in headers:
		filename = headers.split("filename=")[-1]
		filename = safe_decode(filename).split(";", 1)[0]

	else:
		filename = get_random_filename(content_type=mtype)

	if os.path.splitext(filename)[1].lower() not in ALLOWED_DATAURL_IMAGE_EXTENSIONS:
		frappe.throw(_("File type of {0} is not allowed in quiz answers.").format(escape_html(filename)))

	_file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": filename,
			"content": content,
			"decode": False,
			"is_private": False,
		}
	)
	_file.save(ignore_permissions=True)
	file_url = _file.unique_url
	frappe.flags.has_dataurl = True

	return f'<img src="{file_url}"'


def get_corrupted_image_msg():
	return _("Image: Corrupted Data Stream")


def create_submission(
	quiz: str,
	results: list,
	score_out_of: int,
	passing_percentage: float,
	*,
	started_at=None,
	submitted_at=None,
	is_late=0,
	attempt=None,
):
	submission = frappe.new_doc("LMS Quiz Submission")
	# Score and percentage are calculated by the controller function
	submission.update(
		{
			"doctype": "LMS Quiz Submission",
			"quiz": quiz,
			"result": results,
			"score": 0,
			"score_out_of": score_out_of,
			"member": frappe.session.user,
			"percentage": 0,
			"passing_percentage": passing_percentage,
			"started_at": started_at,
			"submitted_at": submitted_at or now_datetime(),
			"is_late": is_late,
			"attempt": attempt,
		}
	)
	submission.save(ignore_permissions=True)
	return submission


def save_progress_after_quiz(quiz_details: dict, percentage: float):
	if not quiz_details.lesson or not quiz_details.course:
		return

	if quiz_details.passing_percentage and percentage < quiz_details.passing_percentage:
		return
	save_progress(quiz_details.lesson, quiz_details.course)


@frappe.whitelist()
def check_answer(quiz: str, question: str, question_type: str, answers: str):
	ADMIN_ROLES = ("System Manager", "Moderator", "Course Creator", "Batch Evaluator")
	is_admin = any(role in ADMIN_ROLES for role in frappe.get_roles())

	if not frappe.db.exists("LMS Quiz Question", {"parent": quiz, "question": question}):
		frappe.throw(_("Question not found in this quiz."), frappe.PermissionError)

	if not is_admin and not frappe.db.get_value("LMS Quiz", quiz, "show_answers"):
		frappe.throw(
			_("Live answer checking is not enabled for this quiz."),
			frappe.PermissionError,
		)

	answers = _parse_json_arg(answers, _("answers")) if answers else []
	if not isinstance(answers, list):
		frappe.throw(_("Invalid answers submitted."), frappe.ValidationError)

	if question_type == "Choices":
		return check_choice_answers(question, answers)

	# A blank input answer (empty list, or the [null] the UI emits for an untouched field)
	# scores as incorrect; coerce to "" so answers[0] can't IndexError / feed None onward.
	answer = answers[0] if answers else ""
	return check_input_answers(question, answer if isinstance(answer, str) else "")


def get_question_details(question: str):
	fields = ["multiple"] + QUESTION_OPTION_FIELDS + QUESTION_CORRECTNESS_FIELDS
	return frappe.db.get_value("LMS Question", question, fields, as_dict=1)


def check_choice_answers(question: str, answers: list):
	question_details = get_question_details(question)
	is_correct = []

	for option_field, correctness_field in zip(
		QUESTION_OPTION_FIELDS, QUESTION_CORRECTNESS_FIELDS, strict=True
	):
		if question_details[option_field] in answers:
			is_correct.append(question_details[correctness_field])
		elif question_details[correctness_field]:
			is_correct.append(2)
		else:
			is_correct.append(0)

	return is_correct


def check_input_answers(question: str, answer: str):
	question_details = frappe.db.get_value("LMS Question", question, QUESTION_POSSIBILITY_FIELDS, as_dict=1)
	for field in QUESTION_POSSIBILITY_FIELDS:
		possibility = question_details[field]
		if possibility and fuzz.token_sort_ratio(possibility, answer) > 85:
			return 1
	return 0


@frappe.whitelist()
def get_quiz_schedule_info(quiz: str) -> dict:
	if not isinstance(quiz, str):
		frappe.throw(_("Invalid quiz."), frappe.ValidationError)

	from lms.lms.permissions import can_access_quiz

	if not can_access_quiz(quiz):
		frappe.throw(_("You are not authorized to access this quiz."), frappe.PermissionError)

	quiz_row = frappe.db.get_value(
		"LMS Quiz",
		quiz,
		[
			"name",
			"title",
			"enable_quiz_scheduling",
			"quiz_start_date",
			"quiz_start_time",
			"quiz_end_date",
			"quiz_end_time",
			"duration",
			"allow_late_submission",
			"late_submission_grace_period",
			"max_attempts",
		],
		as_dict=True,
	)
	if not quiz_row:
		frappe.throw(_("Quiz not found."), frappe.ValidationError)

	if not quiz_row.enable_quiz_scheduling:
		return {
			"is_scheduled": False,
			"is_available": True,
			"can_start": True,
			"status": "available",
			"message": "",
		}

	now = now_datetime()
	start_dt = get_datetime(f"{quiz_row.quiz_start_date} {quiz_row.quiz_start_time}")
	end_dt = get_datetime(f"{quiz_row.quiz_end_date} {quiz_row.quiz_end_time}")

	if now < start_dt:
		status = "upcoming"
		is_available = False
		can_start = False
		message = _("Quiz has not started yet.")
	elif now > end_dt:
		status = "expired"
		is_available = False
		can_start = False
		message = _("Quiz has expired.")
	else:
		status = "available"
		is_available = True
		can_start = True
		message = _("Quiz is currently open.")

	# Check active attempt for current user
	active_attempt = None
	user = frappe.session.user
	if user and user != "Guest":
		attempt_row = frappe.db.get_value(
			"LMS Quiz Attempt",
			{"quiz": quiz, "member": user, "status": "In Progress"},
			["name", "start_time", "deadline", "saved_answers"],
			as_dict=True,
		)
		if attempt_row:
			deadline = get_datetime(attempt_row.deadline)
			remaining_sec = int((deadline - now).total_seconds())
			if remaining_sec > 0:
				active_attempt = {
					"name": attempt_row.name,
					"start_time": str(attempt_row.start_time),
					"deadline": str(attempt_row.deadline),
					"remaining_seconds": remaining_sec,
					"saved_answers": attempt_row.saved_answers or "[]",
					"is_grace_period": False,
				}
			else:
				# Check late submission grace period
				allow_late = quiz_row.allow_late_submission
				grace_mins = cint(quiz_row.late_submission_grace_period or 5)
				grace_deadline = deadline + timedelta(minutes=grace_mins)
				if allow_late and now <= grace_deadline:
					active_attempt = {
						"name": attempt_row.name,
						"start_time": str(attempt_row.start_time),
						"deadline": str(attempt_row.deadline),
						"remaining_seconds": 0,
						"is_grace_period": True,
						"saved_answers": attempt_row.saved_answers or "[]",
					}
				else:
					attempt_doc = frappe.get_doc("LMS Quiz Attempt", attempt_row.name)
					auto_finalize_expired_attempt(attempt_doc, quiz_row)

	return {
		"is_scheduled": True,
		"status": status,
		"is_available": is_available,
		"can_start": can_start,
		"message": message,
		"start_datetime": str(start_dt),
		"end_datetime": str(end_dt),
		"duration": cint(quiz_row.duration),
		"allow_late_submission": bool(quiz_row.allow_late_submission),
		"late_submission_grace_period": cint(quiz_row.late_submission_grace_period or 5),
		"server_time": str(now),
		"timezone": get_system_timezone(),
		"active_attempt": active_attempt,
	}


@frappe.whitelist()
def start_quiz_attempt(quiz: str) -> dict:
	if not isinstance(quiz, str):
		frappe.throw(_("Invalid quiz."), frappe.ValidationError)

	from lms.lms.permissions import can_access_quiz

	if not can_access_quiz(quiz):
		frappe.throw(_("You are not authorized to take this quiz."), frappe.PermissionError)

	quiz_row = frappe.db.get_value(
		"LMS Quiz",
		quiz,
		[
			"name",
			"total_marks",
			"passing_percentage",
			"enable_quiz_scheduling",
			"quiz_start_date",
			"quiz_start_time",
			"quiz_end_date",
			"quiz_end_time",
			"duration",
			"allow_late_submission",
			"late_submission_grace_period",
			"max_attempts",
		],
		as_dict=True,
	)
	if not quiz_row:
		frappe.throw(_("Quiz not found."), frappe.ValidationError)

	if not quiz_row.enable_quiz_scheduling:
		return {"is_scheduled": False}

	now = now_datetime()
	start_dt = get_datetime(f"{quiz_row.quiz_start_date} {quiz_row.quiz_start_time}")
	end_dt = get_datetime(f"{quiz_row.quiz_end_date} {quiz_row.quiz_end_time}")

	if now < start_dt:
		frappe.throw(_("Quiz has not started yet."), frappe.ValidationError)

	user = frappe.session.user

	# Check for existing in-progress attempt
	existing_attempt = frappe.db.get_value(
		"LMS Quiz Attempt",
		{"quiz": quiz, "member": user, "status": "In Progress"},
		["name", "start_time", "deadline", "saved_answers"],
		as_dict=True,
	)
	if existing_attempt:
		deadline = get_datetime(existing_attempt.deadline)
		remaining = int((deadline - now).total_seconds())
		if remaining > 0:
			return {
				"attempt": existing_attempt.name,
				"start_time": str(existing_attempt.start_time),
				"deadline": str(existing_attempt.deadline),
				"remaining_seconds": remaining,
				"saved_answers": existing_attempt.saved_answers or "[]",
				"is_resumed": True,
				"is_grace_period": False,
			}
		else:
			# Check grace period
			if quiz_row.allow_late_submission:
				grace_mins = cint(quiz_row.late_submission_grace_period or 5)
				if now <= deadline + timedelta(minutes=grace_mins):
					return {
						"attempt": existing_attempt.name,
						"start_time": str(existing_attempt.start_time),
						"deadline": str(existing_attempt.deadline),
						"remaining_seconds": 0,
						"is_grace_period": True,
						"saved_answers": existing_attempt.saved_answers or "[]",
						"is_resumed": True,
					}
			attempt_doc = frappe.get_doc("LMS Quiz Attempt", existing_attempt.name)
			auto_finalize_expired_attempt(attempt_doc, quiz_row)

	# If no active attempt and closing time has passed, do not allow starting a new attempt
	if now > end_dt:
		frappe.throw(
			_("Quiz has already closed and is no longer accepting new attempts."),
			frappe.ValidationError,
		)

	# Validate attempt limit
	if quiz_row.max_attempts:
		submissions_count = frappe.db.count(
			"LMS Quiz Submission", filters={"quiz": quiz, "member": user}
		)
		if submissions_count >= quiz_row.max_attempts:
			from lms.lms.doctype.lms_quiz_submission.lms_quiz_submission import (
				MaximumAttemptsExceededError,
			)

			frappe.throw(
				_("You have exceeded the maximum number of attempts ({0}) for this quiz").format(
					quiz_row.max_attempts
				),
				MaximumAttemptsExceededError,
			)

	# Calculate effective deadline: earlier of (now + duration) and (closing datetime)
	start_time = now
	effective_deadline = end_dt
	if quiz_row.duration and cint(quiz_row.duration) > 0:
		duration_deadline = start_time + timedelta(minutes=cint(quiz_row.duration))
		effective_deadline = min(duration_deadline, end_dt)

	remaining_seconds = max(0, int((effective_deadline - start_time).total_seconds()))

	attempt = frappe.new_doc("LMS Quiz Attempt")
	attempt.update(
		{
			"quiz": quiz,
			"member": user,
			"start_time": start_time,
			"deadline": effective_deadline,
			"status": "In Progress",
			"saved_answers": "[]",
		}
	)
	attempt.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"attempt": attempt.name,
		"start_time": str(start_time),
		"deadline": str(effective_deadline),
		"remaining_seconds": remaining_seconds,
		"saved_answers": "[]",
		"is_resumed": False,
		"is_grace_period": False,
	}


@frappe.whitelist()
def save_quiz_progress(quiz: str, results: str) -> dict:
	if not isinstance(quiz, str):
		frappe.throw(_("Invalid quiz."), frappe.ValidationError)

	from lms.lms.permissions import can_access_quiz

	if not can_access_quiz(quiz):
		frappe.throw(_("You are not authorized to access this quiz."), frappe.PermissionError)

	user = frappe.session.user
	attempt_name = frappe.db.get_value(
		"LMS Quiz Attempt",
		{"quiz": quiz, "member": user, "status": "In Progress"},
		"name",
	)
	if not attempt_name:
		return {"status": "no_active_attempt"}

	attempt_doc = frappe.get_doc("LMS Quiz Attempt", attempt_name)
	now = now_datetime()
	deadline = get_datetime(attempt_doc.deadline)

	# Allow saving if still within deadline or reasonable grace period
	if now <= deadline + timedelta(minutes=10):
		attempt_doc.saved_answers = results
		attempt_doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "saved"}

	return {"status": "expired"}


def auto_finalize_expired_attempt(attempt_doc, quiz_details):
	"""Finalize an expired attempt by grading whatever answers were saved on server before deadline."""
	if attempt_doc.status == "Completed" or attempt_doc.submission:
		return
	attempt_doc.status = "Expired"
	saved_results = []
	try:
		if attempt_doc.saved_answers:
			saved_results = json.loads(attempt_doc.saved_answers)
	except Exception:
		saved_results = []

	if saved_results and isinstance(saved_results, list):
		try:
			_validate_quiz_results(saved_results)
			data = process_results(saved_results, quiz_details)
			submission = create_submission(
				quiz_details.name if hasattr(quiz_details, "name") else quiz_details.get("name"),
				data["results"],
				quiz_details.total_marks if hasattr(quiz_details, "total_marks") else quiz_details.get("total_marks"),
				quiz_details.passing_percentage if hasattr(quiz_details, "passing_percentage") else quiz_details.get("passing_percentage"),
				started_at=attempt_doc.start_time,
				submitted_at=get_datetime(attempt_doc.deadline),
				is_late=0,
				attempt=attempt_doc.name,
			)
			attempt_doc.submission = submission.name
		except Exception:
			pass
	attempt_doc.save(ignore_permissions=True)
	frappe.db.commit()

