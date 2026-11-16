# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import re
import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime, today

from lms.lms.ai.ai_service import call_ai_service


def verify_student_course_enrollment(user: str, course: str) -> bool:
	"""Strictly verifies on the server that user is actively enrolled in course and course is not expired."""
	if not user or user == "Guest":
		frappe.throw(_("Authentication required. Please log in."), frappe.AuthenticationError)

	# Teachers, Course Creators, Moderators, and Administrators have pedagogical oversight
	roles = frappe.get_roles(user)
	privileged_roles = ["System Manager", "Administrator", "Course Creator", "Instructor", "Moderator", "Principal"]
	if any(r in roles for r in privileged_roles):
		return True

	# 1. Check Course existence and published status
	course_details = frappe.db.get_value(
		"LMS Course",
		course,
		["name", "published", "expiry_date"],
		as_dict=True,
	)
	if not course_details:
		frappe.throw(_("Course '{0}' does not exist.").format(course), frappe.DoesNotExistError)

	if not course_details.published:
		frappe.throw(_("Course '{0}' is not published.").format(course), frappe.PermissionError)

	# 2. Check Course Expiry
	now_date = getdate(today())
	if course_details.expiry_date and now_date > getdate(course_details.expiry_date):
		frappe.throw(
			_("Access Denied: Course '{0}' enrollment has expired.").format(course),
			frappe.PermissionError,
		)

	# 3. Check LMS Enrollment
	enrollment = frappe.db.get_value(
		"LMS Enrollment",
		{"member": user, "course": course},
		["name", "course", "enrollment_from_batch"],
		as_dict=True,
	)

	if not enrollment:
		frappe.throw(
			_("Access Denied: You are not enrolled in course '{0}'.").format(course),
			frappe.PermissionError,
		)

	# 4. Check Batch Expiry if enrolled through a batch
	if enrollment.enrollment_from_batch:
		batch_expiry = frappe.db.get_value("LMS Batch", enrollment.enrollment_from_batch, "expiry_date")
		if batch_expiry and now_date > getdate(batch_expiry):
			frappe.throw(
				_("Access Denied: Your enrollment batch '{0}' has expired.").format(enrollment.enrollment_from_batch),
				frappe.PermissionError,
			)

	return True


@frappe.whitelist()
def api_get_student_enrolled_courses() -> dict:
	"""Retrieves the logged-in student's active, non-expired courses with question bank stats."""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required."), frappe.AuthenticationError)

	roles = frappe.get_roles(user)
	is_admin = any(
		r in roles
		for r in ["System Manager", "Administrator", "Course Creator", "Instructor", "Moderator", "Principal"]
	)

	now_date = getdate(today())

	# Find enrolled courses from LMS Enrollment
	enrollments = frappe.get_all(
		"LMS Enrollment",
		filters={"member": user},
		fields=["name", "course", "enrollment_from_batch", "creation"],
	)

	enrolled_course_names = set()
	for e in enrollments:
		c_name = e.course
		if not c_name or not frappe.db.exists("LMS Course", c_name):
			continue

		# Check Course Expiry
		c_exp = frappe.db.get_value("LMS Course", c_name, "expiry_date")
		if c_exp and now_date > getdate(c_exp):
			continue

		# Check Batch Expiry
		if e.enrollment_from_batch:
			b_exp = frappe.db.get_value("LMS Batch", e.enrollment_from_batch, "expiry_date")
			if b_exp and now_date > getdate(b_exp):
				continue

		enrolled_course_names.add(c_name)

	# If teacher or admin and has no direct enrollments, provide published courses for preview
	if is_admin and not enrolled_course_names:
		pub = frappe.get_all("LMS Course", filters={"published": 1}, pluck="name")
		enrolled_course_names.update(pub)

	courses_data = []
	for c_name in enrolled_course_names:
		c_doc = frappe.db.get_value(
			"LMS Course",
			c_name,
			["name", "title", "image", "short_introduction", "published"],
			as_dict=True,
		)
		if not c_doc or not c_doc.published:
			continue

		# Count approved questions in this course
		q_count = frappe.db.count(
			"LMS Question",
			filters={"course": c_name, "approval_status": "Approved"},
		)

		# Get chapters for this course
		chapters = frappe.get_all(
			"Course Chapter",
			filters={"course": c_name},
			fields=["name", "title"],
			order_by="idx asc",
		)

		courses_data.append(
			{
				"name": c_doc.name,
				"title": c_doc.title,
				"image": c_doc.image,
				"short_introduction": c_doc.short_introduction,
				"total_questions": q_count,
				"chapters": chapters,
			}
		)

	courses_data.sort(key=lambda x: x["title"])

	return {
		"courses": courses_data,
		"total_enrolled": len(courses_data),
		"student": user,
	}


@frappe.whitelist()
def api_get_student_practice_questions(
	course: str,
	chapter: str | None = None,
	difficulty: str | None = None,
	question_type: str | None = None,
	search_query: str | None = None,
	start: int = 0,
	page_length: int = 20,
) -> dict:
	"""Fetches approved questions for student practice.
	Answer keys and detailed explanations are stripped to prevent cheating during practice tests.
	"""
	user = frappe.session.user
	verify_student_course_enrollment(user, course)

	filters = {
		"course": course,
		"approval_status": "Approved",
	}

	if chapter:
		filters["chapter"] = chapter
	if difficulty and difficulty != "All":
		filters["difficulty"] = difficulty
	if question_type and question_type != "All":
		filters["type"] = question_type

	or_filters = []
	if search_query:
		or_filters.append(["question", "like", f"%{search_query}%"])
		or_filters.append(["subject", "like", f"%{search_query}%"])

	total_count = frappe.db.count("LMS Question", filters=filters)

	# Fetch questions WITHOUT revealing correct answer flags or explanations
	questions_raw = frappe.get_all(
		"LMS Question",
		filters=filters,
		or_filters=or_filters if or_filters else None,
		fields=[
			"name",
			"question",
			"type",
			"multiple",
			"difficulty",
			"marks",
			"course",
			"chapter",
			"lesson",
			"subject",
			"option_1",
			"option_2",
			"option_3",
			"option_4",
			"option_5",
			"option_6",
			"option_7",
			"option_8",
			"option_9",
			"option_10",
		],
		order_by="creation desc",
		start=cint(start) or 0,
		page_length=cint(page_length) or 20,
	)

	# Fetch user's previous practice attempts for these questions
	q_names = [q.name for q in questions_raw]
	practice_map = {}
	if q_names:
		attempts = frappe.get_all(
			"AI Question Practice Log",
			filters={"member": user, "question": ["in", q_names]},
			fields=["question", "is_correct", "selected_answer", "correct_answer", "marks_obtained", "practice_date"],
			order_by="practice_date desc",
		)
		for att in attempts:
			if att.question not in practice_map:
				practice_map[att.question] = att

	formatted_questions = []
	for q in questions_raw:
		options = []
		if q.type == "Choices":
			for i in range(1, 11):
				opt = getattr(q, f"option_{i}")
				if opt:
					options.append(opt)

		prev = practice_map.get(q.name)
		formatted_questions.append(
			{
				"name": q.name,
				"question": q.question,
				"type": q.type or "Choices",
				"multiple": q.multiple or 0,
				"difficulty": q.difficulty or "Medium",
				"marks": q.marks or 1,
				"course": q.course,
				"chapter": q.chapter,
				"lesson": q.lesson,
				"subject": q.subject,
				"options": options,
				"already_attempted": bool(prev),
				"previous_attempt": {
					"is_correct": bool(prev.is_correct) if prev else False,
					"selected_answer": prev.selected_answer if prev else None,
					"correct_answer": prev.correct_answer if prev else None,
					"marks_obtained": prev.marks_obtained if prev else 0,
				}
				if prev
				else None,
			}
		)

	return {
		"questions": formatted_questions,
		"total_count": total_count,
		"course": course,
		"start": cint(start) or 0,
		"page_length": cint(page_length) or 20,
	}


@frappe.whitelist()
def api_submit_student_practice_answer(question_id: str, user_answer: str, course: str) -> dict:
	"""Validates student's answer, saves the practice log, and securely returns correctness & explanation."""
	user = frappe.session.user
	verify_student_course_enrollment(user, course)

	if not frappe.db.exists("LMS Question", question_id):
		frappe.throw(_("Question {0} does not exist.").format(question_id), frappe.DoesNotExistError)

	q_doc = frappe.get_doc("LMS Question", question_id)

	# Strict verification: Question must belong to the specified course
	if q_doc.course != course:
		frappe.throw(
			_("Security Violation: Question '{0}' does not belong to course '{1}'.").format(question_id, course),
			frappe.PermissionError,
		)

	# Strict verification: Question must be approved
	if q_doc.approval_status != "Approved":
		frappe.throw(
			_("Access Denied: This question is not approved for practice."),
			frappe.PermissionError,
		)

	# Evaluate user answer
	is_correct = False
	correct_str = ""
	explanation_text = q_doc.explanation or ""

	if q_doc.type == "Choices":
		correct_opts = []
		for i in range(1, 11):
			opt = getattr(q_doc, f"option_{i}")
			if opt and getattr(q_doc, f"is_correct_{i}"):
				correct_opts.append(opt)
				# Specific option explanation if present
				opt_exp = getattr(q_doc, f"explanation_{i}")
				if opt_exp and not explanation_text:
					explanation_text = opt_exp

		correct_str = ", ".join(correct_opts) if correct_opts else "None"
		u_ans = str(user_answer).strip().lower()

		# Case-insensitive and trimmed check
		for c_opt in correct_opts:
			if u_ans == c_opt.strip().lower():
				is_correct = True
				break

	elif q_doc.type == "User Input":
		possibilities = []
		for i in range(1, 11):
			pos = getattr(q_doc, f"possibility_{i}")
			if pos:
				possibilities.append(pos.strip())

		correct_str = ", ".join(possibilities) if possibilities else ""
		u_ans = str(user_answer).strip().lower()
		for pos in possibilities:
			if u_ans == pos.lower():
				is_correct = True
				break

	elif q_doc.type == "Open Ended":
		# Subjective question: mark as self-reviewed
		is_correct = True
		correct_str = "Model Answer Provided in Explanation"

	marks_obtained = flt(q_doc.marks or 1) if is_correct else 0.0

	# Record practice log in MariaDB
	log = frappe.new_doc("AI Question Practice Log")
	log.member = user
	log.course = course
	log.chapter = q_doc.chapter
	log.question = question_id
	log.question_text = frappe.utils.strip_html(q_doc.question or "")[:300]
	log.question_type = q_doc.type or "Choices"
	log.selected_answer = str(user_answer)[:200]
	log.correct_answer = correct_str[:200]
	log.is_correct = 1 if is_correct else 0
	log.marks_obtained = marks_obtained
	log.total_marks = flt(q_doc.marks or 1)
	log.practice_date = now_datetime()
	log.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": "success",
		"question_id": question_id,
		"is_correct": is_correct,
		"marks_obtained": marks_obtained,
		"total_marks": flt(q_doc.marks or 1),
		"correct_answer": correct_str,
		"explanation": explanation_text or _("Great practice! Review the concept thoroughly for examination mastery."),
		"user_answer": user_answer,
	}


@frappe.whitelist()
def api_ask_ai_question_help(question_id: str, course: str | None = None) -> dict:
	"""AI Pedagogical Tutor: Explains difficult questions and concepts step-by-step."""
	user = frappe.session.user
	if not frappe.db.exists("LMS Question", question_id):
		frappe.throw(_("Question not found."), frappe.DoesNotExistError)

	q_doc = frappe.get_doc("LMS Question", question_id)
	target_course = course or q_doc.course
	verify_student_course_enrollment(user, target_course)

	if q_doc.approval_status != "Approved":
		frappe.throw(_("Question is not approved."), frappe.PermissionError)

	clean_question = frappe.utils.strip_html(q_doc.question or "")
	options_text = ""
	if q_doc.type == "Choices":
		opts = []
		for i in range(1, 11):
			opt = getattr(q_doc, f"option_{i}")
			if opt:
				opts.append(f"{chr(64 + i)}. {opt}")
		options_text = "\n".join(opts)

	system_prompt = (
		"You are an encouraging, expert AI Academic Tutor for Izensphere School students. "
		"Explain the concepts clearly, simply, and step-by-step. "
		"Help the student understand WHY the concept works, break down the logic, "
		"and provide an intuitive analogy or memory tip. Do not use condescending language."
	)

	user_prompt = f"""Question: {clean_question}
Question Type: {q_doc.type}
Options:
{options_text}
Subject/Topic: {q_doc.subject or q_doc.chapter or target_course}

Please provide:
1. Core Concept Explanation: What fundamental principle is being tested here?
2. Step-by-Step Solution Logic: How to approach and solve this question.
3. Common Pitfalls: Where students usually make mistakes.
4. Quick Memory Tip / Analogy to remember this concept permanently."""

	ai_resp = call_ai_service(
		system_prompt=system_prompt,
		user_prompt=user_prompt,
		generation_type="Assessment Analytics",
		course=target_course,
		chapter=q_doc.chapter,
	)

	explanation_output = ai_resp.get("explanation") or ai_resp.get("content") or ai_resp.get("response") or ai_resp.get("summary")
	if not explanation_output and isinstance(ai_resp, dict):
		# Collect text values
		parts = [f"**{k.replace('_', ' ').title()}**:\n{v}" for k, v in ai_resp.items() if isinstance(v, str) and not k.startswith("_")]
		explanation_output = "\n\n".join(parts) if parts else str(ai_resp)

	# Mark AI hint used in log
	recent_log = frappe.db.get_value(
		"AI Question Practice Log",
		{"member": user, "question": question_id},
		"name",
		order_by="practice_date desc",
	)
	if recent_log:
		frappe.db.set_value("AI Question Practice Log", recent_log, "ai_hint_requested", 1)

	return {
		"status": "success",
		"question_id": question_id,
		"ai_explanation": explanation_output or "AI tutor analysis complete.",
	}


@frappe.whitelist()
def api_generate_similar_practice_question(question_id: str, course: str | None = None) -> dict:
	"""AI Practice Generator: Generates a new variation of the same question/concept on the fly."""
	user = frappe.session.user
	if not frappe.db.exists("LMS Question", question_id):
		frappe.throw(_("Question not found."), frappe.DoesNotExistError)

	q_doc = frappe.get_doc("LMS Question", question_id)
	target_course = course or q_doc.course
	verify_student_course_enrollment(user, target_course)

	if q_doc.approval_status != "Approved":
		frappe.throw(_("Question is not approved."), frappe.PermissionError)

	clean_question = frappe.utils.strip_html(q_doc.question or "")

	system_prompt = (
		"You are an AI Question Generator for Izensphere LMS. "
		"Generate ONE completely NEW practice question testing the EXACT same academic concept and difficulty level, "
		"but with fresh wording, new numbers/scenarios, and 4 distinct multiple choice options. "
		"Respond STRICTLY in JSON format with keys: question, options (array of 4 strings), correct_answer (one string matching one option exactly), explanation."
	)

	user_prompt = f"""Source Question to clone concept from:
Question: {clean_question}
Difficulty: {q_doc.difficulty or 'Medium'}
Subject/Chapter: {q_doc.subject or q_doc.chapter or target_course}

Generate 1 new similar practice question in JSON format."""

	ai_resp = call_ai_service(
		system_prompt=system_prompt,
		user_prompt=user_prompt,
		generation_type="Quiz",
		course=target_course,
		chapter=q_doc.chapter,
	)

	# Extract questions
	sim_q = None
	if isinstance(ai_resp.get("questions"), list) and ai_resp["questions"]:
		sim_q = ai_resp["questions"][0]
	elif ai_resp.get("question"):
		sim_q = ai_resp

	if not sim_q or not sim_q.get("question"):
		sim_q = {
			"question": f"Practice Variation: {clean_question} (Application Scenario)",
			"options": [
				getattr(q_doc, f"option_{i}") or f"Option {chr(64 + i)}" for i in range(1, 5)
			],
			"correct_answer": getattr(q_doc, "option_1") or "Option A",
			"explanation": q_doc.explanation or "Apply the same fundamental principles to solve this scenario.",
		}

	# Mark similar question generated in log
	recent_log = frappe.db.get_value(
		"AI Question Practice Log",
		{"member": user, "question": question_id},
		"name",
		order_by="practice_date desc",
	)
	if recent_log:
		frappe.db.set_value("AI Question Practice Log", recent_log, "similar_generated", 1)

	return {
		"status": "success",
		"similar_question": sim_q,
	}


@frappe.whitelist()
def api_get_student_practice_history(course: str | None = None) -> dict:
	"""Returns the student's practice performance metrics, mastery rates, and recent activity."""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required."), frappe.AuthenticationError)

	filters = {"member": user}
	if course:
		verify_student_course_enrollment(user, course)
		filters["course"] = course

	logs = frappe.get_all(
		"AI Question Practice Log",
		filters=filters,
		fields=[
			"name",
			"course",
			"chapter",
			"question",
			"question_text",
			"question_type",
			"selected_answer",
			"correct_answer",
			"is_correct",
			"marks_obtained",
			"total_marks",
			"practice_date",
		],
		order_by="practice_date desc",
		limit_page_length=200,
	)

	total_attempted = len(logs)
	total_correct = sum(1 for l in logs if l.is_correct)
	accuracy_pct = round((total_correct / total_attempted * 100), 1) if total_attempted > 0 else 0.0
	total_marks_earned = sum(flt(l.marks_obtained) for l in logs)

	# Chapter-wise breakdown
	chapter_stats = {}
	for l in logs:
		chap = l.chapter or "General Practice"
		if chap not in chapter_stats:
			chapter_stats[chap] = {"total": 0, "correct": 0, "accuracy": 0.0}
		chapter_stats[chap]["total"] += 1
		if l.is_correct:
			chapter_stats[chap]["correct"] += 1

	for chap, data in chapter_stats.items():
		if data["total"] > 0:
			data["accuracy"] = round((data["correct"] / data["total"] * 100), 1)

	return {
		"student": user,
		"course": course,
		"total_attempted": total_attempted,
		"total_correct": total_correct,
		"accuracy_percentage": accuracy_pct,
		"total_marks_earned": total_marks_earned,
		"chapter_breakdown": chapter_stats,
		"recent_logs": logs[:25],
	}
