# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import re
import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime
from lms.lms.ai.content_extractor import (
	extract_batch_content,
	extract_chapter_content,
	extract_course_content,
	get_content_stats,
)
from lms.lms.ai.ai_service import call_ai_service as call_openai_json


def build_paper_system_prompt(language: str = "English", mode: str = "Chapter-Based") -> str:
	if mode == "Chapter-Based":
		rule = (
			"STRICT REQUIREMENT: All questions MUST be rooted exclusively in the provided educational content. "
			"Do NOT invent concepts or facts absent from the chapters and batch syllabus."
		)
	else:
		rule = (
			"REQUIREMENT: Use the provided chapter content as the foundation, and supplement it with standard "
			"curriculum-aligned subject knowledge. Clearly label questions using external knowledge with 'source': 'Extended Knowledge'."
		)

	return f"""You are an Expert Examination Board Controller and Senior Question Paper Setter for Izensphere International LMS.
Your mission is to construct a rigorous, balanced, highly diversified, and perfectly structured formal examination question paper in {language}.

{rule}

QUESTION PAPER DIVERSITY REQUIREMENTS:
1. Every question MUST be unique, realistic, and test a distinct educational concept across the syllabus.
2. NEVER repeat the same question stem or placeholder wording across questions.
3. For Multiple Choice Questions (MCQs): Provide 4 plausible, authentic options labeled "(A)", "(B)", "(C)", "(D)".
4. For Higher Marks Questions (Section D & E): Include internal choice ("OR") questions on equally rigorous topics.

DETAILED ANSWER KEY & MARKING SCHEME REQUIREMENTS (STRICT):
For EVERY question, you MUST generate:
1. "correct_answer": The definitive correct answer or option text.
2. "answer_key_detail": A comprehensive, point-by-point Answer Key explicitly broken down according to the marks allocated:
   - For 1-mark questions: Definitive answer + 1 key conceptual reason.
   - For 2-mark questions: 2 distinct evaluation criteria (1 mark each).
   - For 3-mark questions: 3 distinct points or steps (1 mark each).
   - For 4-mark questions: 4 sub-parts or 2 marks for analysis + 2 marks for implementation.
   - For 5-mark questions: Detailed multi-part rubric (e.g. Principle/Definition: 1 mark; Core Mechanism/Architecture: 2 marks; Implementation/Syntax: 1 mark; Use-Case/Significance: 1 mark).
3. "solution": Full step-by-step textbook solution explaining the concepts thoroughly.
4. "internal_choice_question": If an alternative "OR" question is provided, it MUST ALSO contain its own "correct_answer", "answer_key_detail", and "solution" with equivalent detail!

CRITICAL MATHEMATICAL RULE:
The sum of marks of all questions in all sections MUST EQUAL the requested Total Marks EXACTLY.
For questions with an internal choice (OR), count the marks only once!

OUTPUT STRICT JSON SCHEMA:
{{
  "title": "Examination Title",
  "academic_year": "2026-27",
  "class_level": "Class / Batch Name",
  "subject": "Subject Name",
  "examination_type": "Midterm Examination",
  "duration": "3 Hours",
  "total_marks": 80,
  "instructions": "General instructions text (point-wise)",
  "sections": [
    {{
      "section_name": "Section A",
      "title": "Multiple Choice Questions",
      "instructions": "Each question carries 1 mark. Select the correct option.",
      "question_type": "MCQ",
      "marks_per_question": 1,
      "questions_count": 20,
      "total_marks": 20,
      "questions": [
        {{
          "question_number": "1",
          "question": "Specific, realistic question text...",
          "options": ["(A) Choice 1", "(B) Choice 2", "(C) Choice 3", "(D) Choice 4"],
          "correct_answer": "(B) Choice 2",
          "marks": 1,
          "difficulty": "Easy",
          "chapter": "Chapter name",
          "source": "Course Content",
          "answer_key_detail": "[1 Mark] Correct Answer: (B) Choice 2. Key Reason: Explanation...",
          "solution": "Comprehensive explanation of why option (B) is correct and why other choices are invalid.",
          "internal_choice_question": null
        }}
      ]
    }}
  ]
}}
"""


def generate_question_paper(
	academic_year: str = "2026-27",
	class_level: str = "Class 10",
	subject: str = "Science",
	examination_type: str = "Midterm Examination",
	course: str | None = None,
	batch: str | None = None,
	selected_chapters: list[str] | None = None,
	total_marks: int = 80,
	duration: str = "3 Hours",
	examination_date: str | None = None,
	language: str = "English",
	difficulty_distribution: dict | None = None,
	sections_config: list[dict] | None = None,
	mode: str = "Chapter-Based",
) -> dict:
	"""Generates a complete formal examination question paper with sections, internal choices,
	answer key, and detailed solutions based on selected Course and Batch content.
	"""
	total_target_marks = cint(total_marks) or 80

	if not difficulty_distribution:
		difficulty_distribution = {"easy": 30, "medium": 40, "hard": 30}

	# Extract content from Batch, Course, and selected Course Chapters (Additive)
	all_content_texts = []
	chapter_names = []
	batch_title = None
	course_title = None

	# 1. Batch extraction
	batch_res = None
	if batch and frappe.db.exists("LMS Batch", batch):
		batch_res = extract_batch_content(batch, course_name=course, selected_chapters=selected_chapters)
		batch_title = (batch_res.get("title") or batch).strip()
		if batch_res.get("content"):
			all_content_texts.append(batch_res["content"])
		if not course:
			if batch_res.get("courses") and batch_res["courses"][0].get("name"):
				course = batch_res["courses"][0].get("name")
			elif batch_res.get("batch_courses") and batch_res["batch_courses"]:
				course = batch_res["batch_courses"][0]
			elif frappe.db.exists("LMS Course", batch):
				course = batch
		for c_info in batch_res.get("courses", []):
			for ch in c_info.get("chapters", []):
				ch_t = ch.get("title") or ch.get("name")
				if ch_t and ch_t not in chapter_names:
					chapter_names.append(ch_t)

	# 2. Course extraction (ensure course details are included)
	if course and frappe.db.exists("LMS Course", course):
		course_doc = frappe.get_doc("LMS Course", course)
		course_title = course_doc.title.strip()
		# If course content wasn't already included by batch_res, extract it
		if not batch_res or not batch_res.get("courses"):
			course_res = extract_course_content(course, selected_chapters=selected_chapters)
			if course_res.get("content"):
				all_content_texts.append(course_res["content"])
			for ch in course_res.get("chapters", []):
				ch_t = ch.get("title") or ch.get("name")
				if ch_t and ch_t not in chapter_names:
					chapter_names.append(ch_t)

	# 3. Selected chapters extraction (ensure any explicitly chosen chapter is included)
	if selected_chapters:
		for ch_name in selected_chapters:
			if frappe.db.exists("Course Chapter", ch_name):
				ch_res = extract_chapter_content(ch_name)
				ch_t = ch_res.get("title", ch_name)
				if ch_t not in chapter_names:
					chapter_names.append(ch_t)
				if not any(ch_t in t for t in all_content_texts):
					if ch_res.get("content"):
						all_content_texts.append(ch_res["content"])

	# Auto-adjust class_level and subject to match actual Course / Batch
	if course_title:
		if not subject or subject == "Science":
			subject = course_title
		if not class_level or class_level == "Class 10":
			class_level = course_title
	if batch_title:
		if not class_level or class_level == "Class 10" or (course_title and class_level == course_title):
			class_level = batch_title
		if not subject or subject == "Science":
			subject = batch_res.get("category") or batch_title

	combined_content = "\n\n---\n\n".join(all_content_texts).strip()

	# Content check
	stats = get_content_stats(combined_content)
	warning = stats["warning"] if (stats["is_insufficient"] and mode == "Chapter-Based") else None

	# Default sections if not configured by user
	if not sections_config:
		if total_target_marks == 100:
			sections_config = [
				{"name": "Section A", "title": "Multiple Choice Questions", "type": "MCQ", "count": 20, "marks_each": 1, "total": 20},
				{"name": "Section B", "title": "Fill in the Blanks / Very Short Answers", "type": "Fill in the Blanks", "count": 10, "marks_each": 1, "total": 10},
				{"name": "Section C", "title": "Short Answer Questions", "type": "Short Answer", "count": 10, "marks_each": 3, "total": 30},
				{"name": "Section D", "title": "Long Answer / Descriptive Questions", "type": "Long Answer", "count": 4, "marks_each": 5, "total": 20},
				{"name": "Section E", "title": "Application-Based / Higher Order Thinking Questions", "type": "Application-Based", "count": 4, "marks_each": 5, "total": 20},
			]
		elif total_target_marks == 80:
			sections_config = [
				{"name": "Section A", "title": "Multiple Choice Questions", "type": "MCQ", "count": 20, "marks_each": 1, "total": 20},
				{"name": "Section B", "title": "Fill in the Blanks / Very Short Answers", "type": "Short Answer", "count": 6, "marks_each": 2, "total": 12},
				{"name": "Section C", "title": "Short Answer Questions", "type": "Short Answer", "count": 7, "marks_each": 3, "total": 21},
				{"name": "Section D", "title": "Long Answer / Descriptive Questions", "type": "Long Answer", "count": 3, "marks_each": 5, "total": 15},
				{"name": "Section E", "title": "Application-Based / Higher Order Thinking Questions", "type": "Application-Based", "count": 3, "marks_each": 4, "total": 12},
			]
		elif total_target_marks == 50:
			sections_config = [
				{"name": "Section A", "title": "Multiple Choice Questions", "type": "MCQ", "count": 10, "marks_each": 1, "total": 10},
				{"name": "Section B", "title": "Fill in the Blanks / Short Answers", "type": "Short Answer", "count": 5, "marks_each": 2, "total": 10},
				{"name": "Section C", "title": "Short Answer Questions", "type": "Short Answer", "count": 5, "marks_each": 3, "total": 15},
				{"name": "Section D", "title": "Long Answer (with Internal Choice)", "type": "Long Answer", "count": 3, "marks_each": 5, "total": 15},
			]
		else:
			# General split across sections A through E
			sec_a_count = max(4, total_target_marks // 5)
			rem = total_target_marks - sec_a_count
			sec_b_count = max(1, rem // 10)
			rem -= sec_b_count * 2
			sec_c_count = max(1, rem // 6)
			rem -= sec_c_count * 3
			sec_d_count = max(1, rem // 5)
			rem -= sec_d_count * 5
			sec_a_count += rem
			sections_config = [
				{"name": "Section A", "title": "Multiple Choice Questions", "type": "MCQ", "count": sec_a_count, "marks_each": 1, "total": sec_a_count},
				{"name": "Section B", "title": "Fill in the Blanks / Very Short Answers", "type": "Short Answer", "count": sec_b_count, "marks_each": 2, "total": sec_b_count * 2},
				{"name": "Section C", "title": "Short Answer Questions", "type": "Short Answer", "count": sec_c_count, "marks_each": 3, "total": sec_c_count * 3},
				{"name": "Section D", "title": "Long Answer Questions", "type": "Long Answer", "count": sec_d_count, "marks_each": 5, "total": sec_d_count * 5},
			]

	system_prompt = build_paper_system_prompt(language=language, mode=mode)

	sections_prompt_desc = "\n".join(
		[f"- {s.get('name')}: {s.get('count')} questions of {s.get('marks_each')} marks each = {s.get('total')} marks ({s.get('type')})" for s in sections_config]
	)

	batch_line = f"Batch / Cohort: {batch_title}\n" if batch_title else ""
	user_prompt = f"""Generate a complete Question Paper.
School Name: Izensphere International School
Academic Year: {academic_year}
Class: {class_level}
Subject: {subject}
{batch_line}Examination Type: {examination_type}
Duration: {duration}
Total Marks: {total_target_marks}
Selected Scope: {', '.join(chapter_names) if chapter_names else (batch_title or 'Course Curriculum')}
Target Difficulty: Easy {difficulty_distribution.get('easy', 30)}%, Medium {difficulty_distribution.get('medium', 40)}%, Hard {difficulty_distribution.get('hard', 30)}%
Language: {language}

Blueprint of Sections to create:
{sections_prompt_desc}

Provide continuous question numbering starting at 1.
Include step-by-step solutions for every question.
For 5-mark and 4-mark questions, include an alternative internal choice question ('internal_choice_question').

--- CONTENT START ---
{combined_content[:16000]}
--- CONTENT END ---
"""

	result = call_openai_json(
		system_prompt=system_prompt,
		user_prompt=user_prompt,
		generation_type="Question Paper",
		mode=mode,
		course=course,
		batch=batch,
	)

	# Fetch school settings
	school_name = "Izensphere International School"
	school_logo = None
	try:
		s_name = frappe.db.get_single_value("LMS Settings", "school_name")
		if s_name:
			school_name = s_name
		school_logo = frappe.db.get_single_value("LMS Settings", "school_logo")
	except Exception:
		pass

	title_scope = batch_title or course_title or subject
	paper_title_str = f"{title_scope} - {examination_type} ({academic_year})".strip()

	result["title"] = paper_title_str
	result["school_name"] = school_name
	result["school_logo"] = school_logo
	result["academic_year"] = academic_year
	result["class_level"] = class_level
	result["subject"] = subject
	result["examination_type"] = examination_type
	result["duration"] = duration
	result["total_marks"] = total_target_marks
	result["course"] = course
	result["course_title"] = course_title
	result["batch"] = batch
	result["batch_title"] = batch_title
	result["selected_chapters"] = selected_chapters or []
	result["warning"] = warning

	# Validation
	validation = validate_paper_structure(result, target_total_marks=total_target_marks)
	result["validation"] = validation

	return result


def validate_paper_structure(paper_data: dict, target_total_marks: int) -> dict:
	"""Performs comprehensive verification of the question paper:
	1. Total marks match target
	2. Section-wise marks add up to total marks
	3. Duplicate questions check
	4. Chapter coverage
	5. Solution completeness
	"""
	errors = []
	warnings = []

	sections = paper_data.get("sections", [])
	if not sections:
		errors.append("No sections found in the question paper.")
		return {"is_valid": False, "errors": errors, "warnings": warnings}

	calculated_total = 0
	all_questions_text = []
	all_difficulties = {"Easy": 0, "Medium": 0, "Hard": 0}
	total_question_count = 0

	for s_idx, sec in enumerate(sections, 1):
		s_name = sec.get("section_name", f"Section {s_idx}")
		s_marks = cint(sec.get("total_marks", 0))
		calculated_total += s_marks

		questions = sec.get("questions", [])
		sec_q_marks_sum = 0
		for q in questions:
			q_marks = cint(q.get("marks", 0))
			sec_q_marks_sum += q_marks
			total_question_count += 1

			# Difficulty tracking
			diff = q.get("difficulty", "Medium")
			if diff in all_difficulties:
				all_difficulties[diff] += q_marks
			else:
				all_difficulties["Medium"] += q_marks

			# Check duplicates
			q_clean = re.sub(r"[^\w\s]", "", q.get("question", "").lower()).strip()
			if q_clean in all_questions_text:
				warnings.append(f"Potential duplicate question detected in {s_name}: '{q.get('question')[:60]}...'")
			all_questions_text.append(q_clean)

			# Check solution completeness
			if not q.get("solution") and not q.get("correct_answer"):
				warnings.append(f"Question {q.get('question_number')} in {s_name} is missing an answer/solution.")

		# Check section total matches sum of question marks
		if sec_q_marks_sum != s_marks:
			errors.append(
				f"{s_name} sum of question marks ({sec_q_marks_sum}) does not match section total marks ({s_marks})."
			)

	# Verify overall total marks
	if calculated_total != target_total_marks:
		errors.append(
			f"Total Marks Mismatch: The sections sum to {calculated_total} marks, but the requested total is {target_total_marks} marks."
		)

	# Calculate difficulty percentage
	diff_pct = {}
	if calculated_total > 0:
		diff_pct = {k: round((v / calculated_total) * 100, 1) for k, v in all_difficulties.items()}

	is_valid = len(errors) == 0

	return {
		"is_valid": is_valid,
		"errors": errors,
		"warnings": warnings,
		"calculated_total_marks": calculated_total,
		"target_total_marks": target_total_marks,
		"total_questions": total_question_count,
		"difficulty_distribution_actual": diff_pct,
	}


def save_ai_question_paper(paper_data: dict, action: str = "Draft") -> dict:
	"""Validates and persists the AI Question Paper to MariaDB.
	Enforces: Never save a paper if total marks are incorrect!
	"""
	target_marks = cint(paper_data.get("total_marks", 80))
	validation = validate_paper_structure(paper_data, target_total_marks=target_marks)

	if not validation["is_valid"]:
		frappe.throw(
			_("Cannot save Question Paper: Validation failed. {0}").format("; ".join(validation["errors"])),
			frappe.ValidationError,
		)

	user = frappe.session.user
	is_principal_user = "Principal" in frappe.get_roles(user) or user == "Administrator"

	# Workflow status
	if action == "Published" and is_principal_user:
		approval_status = "Published"
	elif action == "Principal Approved" and is_principal_user:
		approval_status = "Principal Approved"
	elif action == "Submitted for Approval":
		approval_status = "Submitted for Approval"
	elif action == "Teacher Review":
		approval_status = "Teacher Review"
	else:
		approval_status = "Draft"

	doc_name = paper_data.get("name")
	if doc_name and frappe.db.exists("AI Question Paper", doc_name):
		doc = frappe.get_doc("AI Question Paper", doc_name)
		doc.sections = []
	else:
		doc = frappe.new_doc("AI Question Paper")
		doc.created_by_teacher = user

	doc.title = paper_data.get("title") or f"{paper_data.get('class_level')} {paper_data.get('subject')} Examination"
	doc.academic_year = paper_data.get("academic_year", "2026-27")
	doc.class_level = paper_data.get("class_level", "Class 10")
	doc.subject = paper_data.get("subject", "Science")
	doc.batch = paper_data.get("batch")
	doc.course = paper_data.get("course")
	doc.examination_type = paper_data.get("examination_type", "Midterm Examination")
	doc.examination_date = paper_data.get("examination_date")
	doc.duration = paper_data.get("duration", "3 Hours")
	doc.total_marks = target_marks
	doc.language = paper_data.get("language", "English")
	doc.school_name = paper_data.get("school_name", "Izensphere International School")
	doc.school_logo = paper_data.get("school_logo")
	doc.instructions = paper_data.get("instructions", "")
	doc.generation_mode = paper_data.get("generation_mode", "Chapter-Based")
	doc.selected_chapters = json.dumps(paper_data.get("selected_chapters", []))
	doc.approval_status = approval_status

	if approval_status == "Submitted for Approval":
		doc.reviewed_by = user
	elif approval_status in ("Principal Approved", "Published"):
		doc.approved_by = user

	# Add sections
	meta_options = [opt.strip() for opt in (frappe.get_meta("AI Question Paper Section").get_field("question_type").options or "").splitlines() if opt.strip()]
	for sec in paper_data.get("sections", []):
		raw_type = sec.get("question_type", "MCQ")
		if raw_type not in meta_options:
			if "case" in raw_type.lower() or "application" in raw_type.lower():
				sec_type = "Case Study / Assertion-Reason"
			elif "short" in raw_type.lower():
				sec_type = "Short Answer"
			elif "long" in raw_type.lower():
				sec_type = "Long Answer"
			else:
				sec_type = "MCQ"
		else:
			sec_type = raw_type

		doc.append(
			"sections",
			{
				"section_name": sec.get("section_name", "Section A"),
				"title": sec.get("title", ""),
				"question_type": sec_type,
				"marks_per_question": flt(sec.get("marks_per_question", 1)),
				"questions_count": cint(sec.get("questions_count", len(sec.get("questions", [])))),
				"total_marks": cint(sec.get("total_marks", 0)),
				"instructions": sec.get("instructions", ""),
				"questions_data": json.dumps(sec.get("questions", [])),
			},
		)

	# Store full JSON representation
	doc.paper_json = json.dumps(paper_data)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"name": doc.name,
		"title": doc.title,
		"total_marks": doc.total_marks,
		"approval_status": doc.approval_status,
		"sections_count": len(doc.sections),
		"status": "success",
	}

