# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import cint, now_datetime
from frappe.utils.pdf import get_pdf
from lms.lms.ai.document_extractor import process_question_paper_document
from lms.lms.ai.historical_analyzer import analyze_course_previous_year_papers
from lms.lms.ai.historical_question_generator import (
	generate_historical_ai_questions,
	regenerate_single_question,
)
from lms.lms.ai.historical_model_paper_builder import generate_historical_model_paper
from lms.lms.ai.pdf_generator import get_paper_html
from lms.lms.ai.question_bank import create_or_update_bank_question


def verify_teacher_or_admin():
	"""Security check: Bar students from modifying papers or viewing answers."""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required."), frappe.AuthenticationError)

	roles = frappe.get_roles(user)
	allowed = {
		"System Manager",
		"Course Creator",
		"Instructor",
		"Principal",
		"Moderator",
		"Batch Evaluator",
		"Administrator",
	}
	if "LMS Student" in roles and not (set(roles) & allowed):
		frappe.throw(
			_("Access Denied: Students do not have permission to access previous year examination analysis."),
			frappe.PermissionError,
		)


@frappe.whitelist()
def api_upload_previous_year_paper(
	course: str,
	subject: str,
	title: str,
	examination_year: int,
	attachment: str,
	batch: str | None = None,
	academic_year: str | None = None,
	examination_type: str = "Annual Examination",
	board_university: str | None = None,
	chapter: str | None = None,
	max_marks: int = 100,
	duration: str = "3 Hours",
	auto_process: int = 1,
) -> dict:
	"""Uploads and saves a previous year examination question paper record."""
	verify_teacher_or_admin()

	doc = frappe.new_doc("Previous Year Question Papers")
	doc.title = title or f"{subject} ({examination_year})"
	doc.course = course
	doc.batch = batch
	doc.subject = subject
	doc.academic_year = academic_year or f"{cint(examination_year) - 1}-{examination_year}"
	doc.examination_year = cint(examination_year)
	doc.examination_type = examination_type
	doc.board_university = board_university
	doc.chapter = chapter
	doc.max_marks = cint(max_marks) or 100
	doc.duration = duration or "3 Hours"
	doc.attachment = attachment
	doc.uploaded_by = frappe.session.user
	doc.upload_date = now_datetime()
	doc.ai_processing_status = "Pending"

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	# Process immediately or via background job
	if cint(auto_process):
		proc_res = process_question_paper_document(doc.name)
		return {"status": "success", "paper_name": doc.name, "processing": proc_res}

	return {"status": "success", "paper_name": doc.name}


@frappe.whitelist()
def api_get_uploaded_papers(course: str, subject: str | None = None, batch: str | None = None) -> list[dict]:
	"""Retrieve all uploaded papers for a given course and optional subject/batch."""
	verify_teacher_or_admin()

	filters = {"course": course}
	if subject and subject.strip() and subject != "All":
		filters["subject"] = subject.strip()
	if batch and batch.strip():
		filters["batch"] = batch.strip()

	return frappe.get_all(
		"Previous Year Question Papers",
		filters=filters,
		fields=[
			"name",
			"title",
			"course",
			"batch",
			"subject",
			"academic_year",
			"examination_year",
			"examination_type",
			"board_university",
			"chapter",
			"max_marks",
			"duration",
			"attachment",
			"ai_processing_status",
			"extracted_questions_count",
			"uploaded_by",
			"upload_date",
			"error_message",
		],
		order_by="examination_year desc, creation desc",
	)


@frappe.whitelist()
def api_process_paper(paper_name: str) -> dict:
	"""Triggers processing and extraction on an uploaded paper."""
	verify_teacher_or_admin()
	return process_question_paper_document(paper_name)


@frappe.whitelist()
def api_delete_uploaded_paper(paper_name: str) -> dict:
	"""Deletes an uploaded question paper."""
	verify_teacher_or_admin()
	if not frappe.db.exists("Previous Year Question Papers", paper_name):
		frappe.throw(_("Question paper not found."))

	frappe.delete_doc("Previous Year Question Papers", paper_name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "deleted": paper_name}


@frappe.whitelist()
def api_analyze_all_papers(course: str, subject: str | None = None, batch: str | None = None) -> dict:
	"""Analyzes ALL uploaded previous year papers for the selected Course."""
	verify_teacher_or_admin()
	return analyze_course_previous_year_papers(course=course, subject=subject, batch=batch)


@frappe.whitelist()
def api_get_historical_dashboard(course: str, subject: str | None = None, batch: str | None = None) -> dict:
	"""Returns the dashboard metrics for the Course/Subject."""
	verify_teacher_or_admin()

	filters = {"course": course}
	if subject and subject.strip() and subject != "All":
		filters["subject"] = subject.strip()

	analysis_list = frappe.get_all(
		"Previous Year Paper Analysis",
		filters=filters,
		fields=[
			"name",
			"title",
			"course",
			"batch",
			"subject",
			"academic_years_covered",
			"total_papers_analyzed",
			"total_questions_extracted",
			"total_repeated_questions",
			"status",
			"analysis_date",
			"topic_importance_json",
			"repeated_questions_json",
			"year_distribution_json",
			"marks_distribution_json",
			"difficulty_distribution_json",
			"chapter_frequency_json",
			"frequently_asked_topics_json",
		],
		order_by="creation desc",
		limit=1,
	)

	if not analysis_list:
		# Run analysis automatically if papers exist
		paper_count = frappe.db.count("Previous Year Question Papers", filters=filters)
		if paper_count > 0:
			return analyze_course_previous_year_papers(course=course, subject=subject, batch=batch)
		else:
			return {
				"has_data": False,
				"message": "No previous year question papers uploaded for this course yet.",
			}

	row = analysis_list[0]
	return {
		"has_data": True,
		"analysis_name": row.name,
		"title": row.title,
		"course": row.course,
		"subject": row.subject,
		"academic_years_covered": row.academic_years_covered,
		"total_uploaded_papers": row.total_papers_analyzed,
		"total_processed_papers": row.total_papers_analyzed,
		"total_extracted_questions": row.total_questions_extracted,
		"total_repeated_questions": row.total_repeated_questions,
		"status": row.status,
		"analysis_date": str(row.analysis_date),
		"topic_importance": json.loads(row.topic_importance_json or "[]"),
		"repeated_questions": json.loads(row.repeated_questions_json or "[]")[:50],
		"year_distribution": json.loads(row.year_distribution_json or "[]"),
		"marks_distribution": json.loads(row.marks_distribution_json or "{}"),
		"difficulty_distribution": json.loads(row.difficulty_distribution_json or "{}"),
		"chapter_frequency": json.loads(row.chapter_frequency_json or "[]"),
		"frequently_asked_topics": json.loads(row.frequently_asked_topics_json or "[]"),
	}


@frappe.whitelist()
def api_generate_questions_from_history(
	course: str,
	subject: str,
	batch: str | None = None,
	chapter: str | None = None,
	number_of_questions: int = 10,
	question_type: str = "Mixed",
	difficulty: str = "Mixed",
	marks_per_question: int | None = None,
	analysis_name: str | None = None,
) -> dict:
	"""Generate novel examination questions using the collective historical patterns."""
	verify_teacher_or_admin()
	return generate_historical_ai_questions(
		course=course,
		subject=subject,
		batch=batch,
		chapter=chapter,
		number_of_questions=cint(number_of_questions) or 10,
		question_type=question_type,
		difficulty=difficulty,
		marks_per_question=cint(marks_per_question) if marks_per_question else None,
		analysis_name=analysis_name,
	)


@frappe.whitelist()
def api_regenerate_single_question(
	question_id: str,
	analysis_name: str | None,
	course: str,
	subject: str,
	topic: str = "",
	question_type: str = "Short Answer",
	difficulty: str = "Medium",
	marks: int = 5,
) -> dict:
	"""Regenerates a single question in the staged review."""
	verify_teacher_or_admin()
	return regenerate_single_question(
		question_id=question_id,
		analysis_name=analysis_name,
		course=course,
		subject=subject,
		topic=topic,
		question_type=question_type,
		difficulty=difficulty,
		marks=cint(marks) or 5,
	)


@frappe.whitelist()
def api_save_approved_questions_to_bank(questions: str | list, course: str, subject: str = "") -> dict:
	"""Saves approved AI-generated questions into the LMS Question bank safely."""
	verify_teacher_or_admin()

	q_list = questions
	if isinstance(questions, str):
		try:
			q_list = json.loads(questions)
		except Exception:
			q_list = []

	if not q_list:
		frappe.throw(_("No questions provided to save."))

	saved_names = []
	for q in q_list:
		try:
			q_type = q.get("type", "Choices")
			# Validate chapter link if provided
			chapter_val = q.get("chapter")
			if chapter_val and not frappe.db.exists("Course Chapter", chapter_val):
				chapter_val = None

			# Map to LMS Question format
			payload = {
				"question": q.get("question", "").strip(),
				"type": "Choices" if q_type in ["Choices", "MCQ", "True or False"] else ("User Input" if q_type == "Fill in the Blanks" else "Choices"),
				"difficulty": q.get("difficulty", "Medium"),
				"marks": cint(q.get("marks")) or 1,
				"course": course,
				"chapter": chapter_val,
				"subject": subject or q.get("subject"),
				"source": "Course Content",
				"is_ai_generated": 1,
				"explanation": q.get("explanation", ""),
				"options": q.get("options", []),
				"correct_answer": q.get("correct_answer"),
				"possibilities": [q.get("correct_answer")] if q.get("correct_answer") else [],
			}
			res = create_or_update_bank_question(payload)
			if res.get("name"):
				saved_names.append(res["name"])
		except Exception as e:
			frappe.logger("ai_assessment").warning(f"Failed to save question to bank: {e}")

	return {
		"status": "success",
		"saved_count": len(saved_names),
		"question_names": saved_names,
	}


@frappe.whitelist()
def api_generate_model_paper_from_history(
	title: str,
	course: str,
	subject: str,
	batch: str | None = None,
	chapters: str | list | None = None,
	total_marks: int = 100,
	duration: str = "3 Hours",
	sections_config: str | list | None = None,
	difficulty_easy_pct: int = 30,
	difficulty_medium_pct: int = 40,
	difficulty_hard_pct: int = 30,
	analysis_name: str | None = None,
) -> dict:
	"""Generate a complete model paper based on historical examination analysis."""
	verify_teacher_or_admin()

	sec_cfg = sections_config
	if isinstance(sections_config, str):
		try:
			sec_cfg = json.loads(sections_config)
		except Exception:
			sec_cfg = None

	ch_list = chapters
	if isinstance(chapters, str) and chapters.startswith("["):
		try:
			ch_list = json.loads(chapters)
		except Exception:
			ch_list = chapters

	return generate_historical_model_paper(
		title=title,
		course=course,
		subject=subject,
		batch=batch,
		chapters=ch_list,
		total_marks=cint(total_marks) or 100,
		duration=duration or "3 Hours",
		sections_config=sec_cfg,
		difficulty_easy_pct=cint(difficulty_easy_pct),
		difficulty_medium_pct=cint(difficulty_medium_pct),
		difficulty_hard_pct=cint(difficulty_hard_pct),
		analysis_name=analysis_name,
	)


@frappe.whitelist()
def api_download_model_paper_pdf(paper_name: str, doc_type: str = "question_paper"):
	"""Download PDF of model question paper or separate answer key."""
	verify_teacher_or_admin()

	if doc_type not in ("question_paper", "answer_key", "detailed_solutions"):
		doc_type = "question_paper"

	html_content = get_paper_html(paper_name, doc_type=doc_type)
	pdf_data = get_pdf(html_content)

	paper_doc = frappe.get_doc("AI Question Paper", paper_name)
	filename = f"{paper_doc.title.replace(' ', '_')}_{doc_type}.pdf"

	frappe.response.filename = filename
	frappe.response.filecontent = pdf_data
	frappe.response.type = "download"
