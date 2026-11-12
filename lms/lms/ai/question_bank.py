# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import re
import frappe
from frappe import _
from frappe.utils import cint
from fuzzywuzzy import fuzz


def search_question_bank(
	course: str | None = None,
	chapter: str | None = None,
	subject: str | None = None,
	difficulty: str | None = None,
	question_type: str | None = None,
	marks: int | None = None,
	search_query: str | None = None,
	start: int = 0,
	page_length: int = 20,
) -> dict:
	"""Queries and filters questions stored in LMS Question table."""
	filters = {}

	if course:
		filters["course"] = course
	if chapter:
		filters["chapter"] = chapter
	if subject:
		filters["subject"] = ["like", f"%{subject}%"]
	if difficulty and difficulty != "All":
		filters["difficulty"] = difficulty
	if question_type and question_type != "All":
		filters["type"] = question_type
	if marks:
		filters["marks"] = cint(marks)

	or_filters = []
	if search_query:
		or_filters.append(["question", "like", f"%{search_query}%"])
		or_filters.append(["explanation", "like", f"%{search_query}%"])

	total_count = frappe.db.count("LMS Question", filters=filters)

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
			"source",
			"course",
			"chapter",
			"lesson",
			"subject",
			"explanation",
			"is_ai_generated",
			"creation",
			"modified",
			"option_1",
			"option_2",
			"option_3",
			"option_4",
			"is_correct_1",
			"is_correct_2",
			"is_correct_3",
			"is_correct_4",
			"possibility_1",
			"possibility_2",
		],
		order_by="creation desc",
		start=start,
		page_length=page_length,
	)

	# Format questions for easy frontend display
	formatted = []
	for q in questions_raw:
		options = []
		correct = []
		if q.type == "Choices":
			for i in range(1, 5):
				opt = getattr(q, f"option_{i}")
				if opt:
					options.append(opt)
					if getattr(q, f"is_correct_{i}"):
						correct.append(opt)
		elif q.type == "User Input":
			for i in range(1, 3):
				pos = getattr(q, f"possibility_{i}")
				if pos:
					options.append(pos)
					correct.append(pos)

		formatted.append(
			{
				"name": q.name,
				"question": q.question,
				"type": q.type,
				"multiple": q.multiple,
				"difficulty": q.difficulty or "Medium",
				"marks": q.marks or 1,
				"source": q.source or "Manual",
				"course": q.course,
				"chapter": q.chapter,
				"lesson": q.lesson,
				"subject": q.subject,
				"explanation": q.explanation,
				"is_ai_generated": q.is_ai_generated,
				"options": options,
				"correct_answer": correct if q.multiple else (correct[0] if correct else ""),
				"creation": str(q.creation),
			}
		)

	return {
		"questions": formatted,
		"total_count": total_count,
		"start": start,
		"page_length": page_length,
	}


def detect_duplicate_question(question_text: str, threshold: int = 85) -> dict:
	"""Detects if a question with substantially similar wording already exists in the Question Bank."""
	clean_new = re.sub(r"[^\w\s]", "", question_text.lower()).strip()
	if not clean_new:
		return {"is_duplicate": False}

	# Check exact match first
	exact_match = frappe.db.get_value(
		"LMS Question",
		{"question": ["like", f"%{question_text[:50]}%"]},
		["name", "question"],
		as_dict=True,
	)
	if exact_match:
		ratio = fuzz.ratio(clean_new, re.sub(r"[^\w\s]", "", exact_match.question.lower()).strip())
		if ratio >= threshold:
			return {
				"is_duplicate": True,
				"similarity": ratio,
				"matched_question": exact_match.name,
				"matched_text": exact_match.question,
			}

	# Sample recent questions for fuzzy match
	recent_questions = frappe.get_all("LMS Question", fields=["name", "question"], limit_page_length=100)
	for q in recent_questions:
		clean_existing = re.sub(r"[^\w\s]", "", q.question.lower()).strip()
		sim = fuzz.ratio(clean_new, clean_existing)
		if sim >= threshold:
			return {
				"is_duplicate": True,
				"similarity": sim,
				"matched_question": q.name,
				"matched_text": q.question,
			}

	return {"is_duplicate": False, "similarity": 0}


def create_or_update_bank_question(data: dict) -> dict:
	"""Allows teachers to manually add or edit a question in the Question Bank."""
	name = data.get("name")
	if name and frappe.db.exists("LMS Question", name):
		doc = frappe.get_doc("LMS Question", name)
	else:
		doc = frappe.new_doc("LMS Question")
		doc.is_ai_generated = cint(data.get("is_ai_generated", 0))

	doc.question = data.get("question", "").strip()
	doc.type = data.get("type", "Choices")
	doc.difficulty = data.get("difficulty", "Medium")
	doc.marks = cint(data.get("marks")) or 1
	doc.course = data.get("course")
	doc.chapter = data.get("chapter")
	doc.lesson = data.get("lesson")
	doc.subject = data.get("subject")
	doc.source = data.get("source", "Manual")
	doc.explanation = data.get("explanation", "")

	# Check for duplicates if creating new
	if not name:
		dup_check = detect_duplicate_question(doc.question)
		if dup_check["is_duplicate"]:
			frappe.msgprint(
				_(
					"Note: A similar question already exists: '{0}' ({1}% match)."
				).format(dup_check["matched_text"][:60], dup_check["similarity"])
			)

	if doc.type == "Choices":
		options = data.get("options", [])
		correct = data.get("correct_answer")
		is_multi = isinstance(correct, list) and len(correct) > 1
		doc.multiple = 1 if is_multi else 0

		for i in range(1, 11):
			setattr(doc, f"option_{i}", None)
			setattr(doc, f"is_correct_{i}", 0)

		for i, opt in enumerate(options[:10], 1):
			setattr(doc, f"option_{i}", opt)
			is_corr = (opt in correct) if is_multi else (opt == correct)
			setattr(doc, f"is_correct_{i}", 1 if is_corr else 0)

	elif doc.type == "User Input":
		possibilities = data.get("possibilities", [])
		for i in range(1, 11):
			setattr(doc, f"possibility_{i}", None)
		for i, pos in enumerate(possibilities[:10], 1):
			setattr(doc, f"possibility_{i}", pos)

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"name": doc.name, "status": "success"}

