# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime
from frappe.utils.response import build_response

from lms.lms.ai.analytics import get_quiz_assessment_report
from lms.lms.ai.content_extractor import (
	extract_batch_content,
	extract_chapter_content,
	extract_course_content,
	extract_lesson_content,
	get_content_stats,
)
from lms.lms.ai.ai_service import get_ai_settings, test_ai_connection
from lms.lms.ai.openai_service import get_default_model, get_openai_api_key
from lms.lms.ai.pdf_generator import generate_paper_pdf_file, get_paper_html
from lms.lms.ai.question_bank import (
	create_or_update_bank_question,
	detect_duplicate_question,
	search_question_bank,
)
from lms.lms.ai.question_paper_generator import (
	generate_question_paper,
	save_ai_question_paper,
	validate_paper_structure,
)
from lms.lms.ai.quiz_generator import (
	generate_quiz,
	regenerate_single_question,
	save_ai_quiz_to_database,
)


def _check_teacher_or_admin_permission():
	"""Ensures the caller has Teacher, Course Creator, Instructor, Moderator, or System Manager role."""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required."), frappe.AuthenticationError)
	roles = frappe.get_roles(user)
	allowed = ["System Manager", "Administrator", "Course Creator", "Instructor", "Batch Evaluator", "Moderator", "Principal"]
	if not any(r in roles for r in allowed):
		frappe.throw(_("Access denied: You need Teacher or Course Creator permissions."), frappe.PermissionError)


def _check_principal_permission():
	"""Ensures caller has Principal or System Manager role."""
	user = frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required."), frappe.AuthenticationError)
	roles = frappe.get_roles(user)
	if not ("Principal" in roles or "System Manager" in roles or user == "Administrator"):
		frappe.throw(_("Access denied: Only Principal or System Manager can perform this action."), frappe.PermissionError)


@frappe.whitelist()
def api_get_ai_config():
	"""Returns public AI configuration (provider, model, endpoints, status) WITHOUT leaking the API key."""
	_check_teacher_or_admin_permission()
	cfg = get_ai_settings()
	return {
		"enable_ai_assessment": cfg.get("enable_ai_assessment", 1),
		"provider": cfg.get("provider", "Ollama"),
		"ollama_base_url": cfg.get("ollama_base_url", "http://localhost:11434"),
		"ollama_model": cfg.get("ollama_model", "llama3.2"),
		"openai_model": cfg.get("openai_model", "gpt-4o-mini"),
		"openai_base_url": cfg.get("openai_base_url", "https://api.openai.com/v1"),
		"has_openai_key": bool(cfg.get("openai_api_key")),
		"has_api_key": bool(cfg.get("openai_api_key")),
		"temperature": cfg.get("temperature", 0.7),
		"max_tokens": cfg.get("max_tokens", 4000),
		"model": cfg.get("openai_model" if cfg.get("provider") == "OpenAI" else "ollama_model"),
		"school_name": cfg.get("school_name", "Izensphere International School"),
		"school_logo": frappe.db.get_single_value("LMS Settings", "school_logo"),
		"default_mode": cfg.get("default_generation_mode", "Chapter-Based"),
	}


@frappe.whitelist()
def api_test_ai_connection(provider: str | None = None, base_url: str | None = None, model: str | None = None, api_key: str | None = None):
	"""Test connectivity and model readiness for Ollama or OpenAI."""
	_check_teacher_or_admin_permission()
	return test_ai_connection(provider=provider, base_url=base_url, model=model, api_key=api_key)


@frappe.whitelist()
def api_save_ai_settings(settings: str | dict | None = None):
	"""Save AI Provider configuration into LMS Settings (System Manager / Administrator only)."""
	user = frappe.session.user
	if not ("System Manager" in frappe.get_roles(user) or user == "Administrator"):
		frappe.throw(_("Only System Managers can update AI settings."), frappe.PermissionError)

	if isinstance(settings, str):
		settings = json.loads(settings)

	if not isinstance(settings, dict):
		frappe.throw(_("Invalid settings payload."))

	doc = frappe.get_doc("LMS Settings", "LMS Settings")
	if "enable_ai_assessment" in settings:
		doc.enable_ai_assessment = cint(settings["enable_ai_assessment"])
	if "provider" in settings:
		doc.ai_provider = settings["provider"]
	if "ollama_base_url" in settings:
		doc.ollama_base_url = settings["ollama_base_url"].strip()
	if "ollama_model" in settings:
		doc.ollama_model = settings["ollama_model"].strip()
	if "openai_model" in settings:
		doc.openai_model = settings["openai_model"].strip()
	if "openai_base_url" in settings:
		doc.openai_base_url = settings["openai_base_url"].strip()
	if "temperature" in settings:
		doc.ai_temperature = flt(settings["temperature"])
	if "max_tokens" in settings:
		doc.ai_max_tokens = cint(settings["max_tokens"])
	if "school_name" in settings:
		doc.school_name = settings["school_name"].strip()
	if "default_mode" in settings:
		doc.default_generation_mode = settings["default_mode"].strip()

	# Save password field if provided
	if settings.get("openai_api_key"):
		doc.openai_api_key = settings["openai_api_key"].strip()

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"success": True, "message": "AI settings saved successfully."}


@frappe.whitelist()
def api_get_content_preview(
	course: str | None = None,
	chapter: str | None = None,
	lesson: str | None = None,
	batch: str | None = None,
):
	"""Returns extracted educational content preview and sufficiency metrics for the teacher."""
	_check_teacher_or_admin_permission()
	if lesson:
		return extract_lesson_content(lesson)
	elif chapter:
		return extract_chapter_content(chapter)
	elif batch:
		return extract_batch_content(batch, course_name=course)
	elif course:
		return extract_course_content(course)
	else:
		frappe.throw(_("Please select Batch, Course, Chapter, or Lesson."))


@frappe.whitelist()
def api_get_batch_details(batch: str):
	"""Returns batch metadata and its linked courses for examination generation."""
	_check_teacher_or_admin_permission()
	if not frappe.db.exists("LMS Batch", batch):
		frappe.throw(_("Batch {0} not found.").format(batch), frappe.DoesNotExistError)

	doc = frappe.get_doc("LMS Batch", batch)
	courses = []
	for c in doc.courses:
		if c.course:
			course_title = frappe.db.get_value("LMS Course", c.course, "title") or c.title or c.course
			courses.append({"course": c.course, "title": course_title})

	if not courses:
		if frappe.db.exists("LMS Course", batch):
			c_title = frappe.db.get_value("LMS Course", batch, "title") or batch
			courses.append({"course": batch, "title": c_title})
		elif frappe.db.exists("LMS Course", batch.strip().lower()):
			match_slug = batch.strip().lower()
			c_title = frappe.db.get_value("LMS Course", match_slug, "title") or match_slug
			courses.append({"course": match_slug, "title": c_title})

	return {
		"name": doc.name,
		"title": doc.title,
		"category": doc.category,
		"description": doc.description,
		"start_date": str(doc.start_date) if doc.start_date else "",
		"end_date": str(doc.end_date) if doc.end_date else "",
		"courses": courses,
	}


@frappe.whitelist()
def api_generate_quiz(
	course: str | None = None,
	chapter: str | None = None,
	lesson: str | None = None,
	difficulty: str = "Medium",
	num_questions: int = 5,
	total_marks: int = 5,
	marks_per_question: int | None = None,
	language: str = "English",
	question_types: str | None = None,
	include_explanations: bool | str = True,
	randomize: bool | str = False,
	mode: str = "Chapter-Based",
):
	"""Generates quiz questions from chapter/lesson content."""
	_check_teacher_or_admin_permission()

	q_types = None
	if question_types:
		if isinstance(question_types, str):
			try:
				q_types = json.loads(question_types)
			except Exception:
				q_types = [t.strip() for t in question_types.split(",")]
		elif isinstance(question_types, list):
			q_types = question_types

	inc_exp = cint(include_explanations) if isinstance(include_explanations, (int, str)) and str(include_explanations).isdigit() else bool(include_explanations)
	rand = cint(randomize) if isinstance(randomize, (int, str)) and str(randomize).isdigit() else bool(randomize)

	return generate_quiz(
		course=course,
		chapter=chapter,
		lesson=lesson,
		difficulty=difficulty,
		num_questions=cint(num_questions) or 5,
		total_marks=cint(total_marks) or 5,
		marks_per_question=cint(marks_per_question) if marks_per_question else None,
		language=language,
		question_types=q_types,
		include_explanations=inc_exp,
		randomize=rand,
		mode=mode,
	)


@frappe.whitelist()
def api_regenerate_question(
	question_data: str | dict,
	course: str | None = None,
	chapter: str | None = None,
	lesson: str | None = None,
	mode: str = "Chapter-Based",
	feedback: str | None = None,
	target_difficulty: str | None = None,
):
	"""Regenerates a single question without regenerating the entire quiz."""
	_check_teacher_or_admin_permission()
	if isinstance(question_data, str):
		question_data = json.loads(question_data)

	return regenerate_single_question(
		current_question=question_data,
		course=course,
		chapter=chapter,
		lesson=lesson,
		mode=mode,
		feedback=feedback,
		target_difficulty=target_difficulty,
	)


@frappe.whitelist()
def api_save_quiz(
	quiz_title: str,
	questions: str | list,
	course: str | None = None,
	chapter: str | None = None,
	lesson: str | None = None,
	passing_percentage: int = 70,
	duration: int | None = None,
	action: str = "Draft",
	quiz_name: str | None = None,
):
	"""Saves reviewed AI-generated quiz questions into LMS Quiz and LMS Question."""
	_check_teacher_or_admin_permission()
	if isinstance(questions, str):
		questions = json.loads(questions)

	return save_ai_quiz_to_database(
		quiz_title=quiz_title,
		questions=questions,
		course=course,
		chapter=chapter,
		lesson=lesson,
		passing_percentage=passing_percentage,
		duration=duration,
		action=action,
		quiz_name=quiz_name,
	)


@frappe.whitelist()
def api_generate_question_paper(
	academic_year: str = "2026-27",
	class_level: str = "Class 10",
	subject: str = "Science",
	examination_type: str = "Midterm Examination",
	course: str | None = None,
	batch: str | None = None,
	selected_chapters: str | list | None = None,
	total_marks: int = 80,
	duration: str = "3 Hours",
	examination_date: str | None = None,
	language: str = "English",
	difficulty_distribution: str | dict | None = None,
	sections_config: str | list | None = None,
	mode: str = "Chapter-Based",
):
	"""Generates full examination question paper structure with sections and solutions."""
	_check_teacher_or_admin_permission()

	chapters = None
	if selected_chapters:
		if isinstance(selected_chapters, str):
			try:
				chapters = json.loads(selected_chapters)
			except Exception:
				chapters = [c.strip() for c in selected_chapters.split(",")]
		elif isinstance(selected_chapters, list):
			chapters = selected_chapters

	diff_dist = None
	if difficulty_distribution:
		if isinstance(difficulty_distribution, str):
			diff_dist = json.loads(difficulty_distribution)
		else:
			diff_dist = difficulty_distribution

	sec_cfg = None
	if sections_config:
		if isinstance(sections_config, str):
			sec_cfg = json.loads(sections_config)
		else:
			sec_cfg = sections_config

	return generate_question_paper(
		academic_year=academic_year,
		class_level=class_level,
		subject=subject,
		examination_type=examination_type,
		course=course,
		batch=batch,
		selected_chapters=chapters,
		total_marks=cint(total_marks) or 80,
		duration=duration,
		examination_date=examination_date,
		language=language,
		difficulty_distribution=diff_dist,
		sections_config=sec_cfg,
		mode=mode,
	)


@frappe.whitelist()
def api_validate_question_paper(paper_data: str | dict, total_marks: int = 80):
	"""Verifies examination paper marks, difficulty, duplicates, and completeness."""
	_check_teacher_or_admin_permission()
	if isinstance(paper_data, str):
		paper_data = json.loads(paper_data)
	return validate_paper_structure(paper_data, target_total_marks=cint(total_marks) or 80)


@frappe.whitelist()
def api_save_question_paper(paper_data: str | dict, action: str = "Draft"):
	"""Saves and approves AI Question Paper with strict marks validation."""
	_check_teacher_or_admin_permission()
	if isinstance(paper_data, str):
		paper_data = json.loads(paper_data)
	return save_ai_question_paper(paper_data, action=action)


@frappe.whitelist()
def api_get_question_paper(name: str):
	"""Retrieves an AI Question Paper with its sections and questions."""
	if not frappe.db.exists("AI Question Paper", name):
		frappe.throw(_("Question Paper {0} not found.").format(name), frappe.DoesNotExistError)

	doc = frappe.get_doc("AI Question Paper", name)

	# Student permission check
	user = frappe.session.user
	if user and user != "Guest":
		roles = frappe.get_roles(user)
		if "LMS Student" in roles and not any(r in roles for r in ["System Manager", "Course Creator", "Instructor", "Principal"]):
			if doc.approval_status not in ("Principal Approved", "Published"):
				frappe.throw(_("Students can only access published and approved question papers."), frappe.PermissionError)

	# Parse sections
	sections = []
	for s in doc.sections:
		q_list = []
		if s.questions_data:
			try:
				q_list = json.loads(s.questions_data)
			except Exception:
				q_list = []
		sections.append(
			{
				"name": s.name,
				"section_name": s.section_name,
				"title": s.title,
				"question_type": s.question_type,
				"marks_per_question": s.marks_per_question,
				"questions_count": s.questions_count,
				"total_marks": s.total_marks,
				"instructions": s.instructions,
				"questions": q_list,
			}
		)

	return {
		"name": doc.name,
		"title": doc.title,
		"academic_year": doc.academic_year,
		"class_level": doc.class_level,
		"subject": doc.subject,
		"batch": doc.batch,
		"course": doc.course,
		"examination_type": doc.examination_type,
		"examination_date": str(doc.examination_date) if doc.examination_date else "",
		"duration": doc.duration,
		"total_marks": doc.total_marks,
		"language": doc.language,
		"school_name": doc.school_name,
		"school_logo": doc.school_logo,
		"instructions": doc.instructions,
		"generation_mode": doc.generation_mode,
		"approval_status": doc.approval_status,
		"sections": sections,
		"created_by_teacher": doc.created_by_teacher,
		"approved_by": doc.approved_by,
	}


@frappe.whitelist()
def api_list_question_papers(
	subject: str | None = None,
	class_level: str | None = None,
	status: str | None = None,
	batch: str | None = None,
	course: str | None = None,
):
	"""Returns list of question papers with role-based filtering."""
	user = frappe.session.user
	roles = frappe.get_roles(user) if user and user != "Guest" else []

	filters = {}
	if subject:
		filters["subject"] = ["like", f"%{subject}%"]
	if class_level:
		filters["class_level"] = class_level
	if status:
		filters["approval_status"] = status
	if batch:
		filters["batch"] = batch
	if course:
		filters["course"] = course

	# If student, only show published
	if "LMS Student" in roles and not any(r in roles for r in ["System Manager", "Course Creator", "Instructor", "Principal"]):
		filters["approval_status"] = "Published"

	papers = frappe.get_all(
		"AI Question Paper",
		filters=filters,
		fields=[
			"name",
			"title",
			"academic_year",
			"class_level",
			"subject",
			"batch",
			"course",
			"examination_type",
			"examination_date",
			"duration",
			"total_marks",
			"approval_status",
			"created_by_teacher",
			"creation",
		],
		order_by="creation desc",
	)
	return papers


@frappe.whitelist()
def api_download_paper_pdf(name: str, doc_type: str = "question_paper"):
	"""Generates and serves the PDF file for download."""
	pdf_bytes = generate_paper_pdf_file(name, doc_type=doc_type)
	filename = f"{name}_{doc_type}.pdf"
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = pdf_bytes
	frappe.local.response.type = "pdf"


@frappe.whitelist()
def api_get_paper_html_preview(name: str, doc_type: str = "question_paper"):
	"""Returns the rendered HTML of the paper for inline preview."""
	return get_paper_html(name, doc_type=doc_type)


@frappe.whitelist()
def api_search_question_bank(
	course: str | None = None,
	chapter: str | None = None,
	subject: str | None = None,
	difficulty: str | None = None,
	question_type: str | None = None,
	marks: int | None = None,
	search_query: str | None = None,
	start: int = 0,
	page_length: int = 20,
):
	"""Searches and filters approved questions in the Question Bank."""
	_check_teacher_or_admin_permission()
	return search_question_bank(
		course=course,
		chapter=chapter,
		subject=subject,
		difficulty=difficulty,
		question_type=question_type,
		marks=cint(marks) if marks else None,
		search_query=search_query,
		start=cint(start) or 0,
		page_length=cint(page_length) or 20,
	)


@frappe.whitelist()
def api_save_bank_question(data: str | dict):
	"""Adds or edits a question in the Question Bank."""
	_check_teacher_or_admin_permission()
	if isinstance(data, str):
		data = json.loads(data)
	return create_or_update_bank_question(data)


@frappe.whitelist()
def api_get_generation_history(limit: int = 20, start: int = 0):
	"""Fetches generation audit logs."""
	_check_teacher_or_admin_permission()
	logs = frappe.get_all(
		"AI Generation Log",
		fields=[
			"name",
			"user",
			"generation_type",
			"status",
			"model",
			"mode",
			"course",
			"chapter",
			"lesson",
			"prompt_tokens",
			"completion_tokens",
			"total_tokens",
			"estimated_cost",
			"creation",
			"error_message",
		],
		order_by="creation desc",
		start=cint(start),
		page_length=cint(limit) or 20,
	)
	total = frappe.db.count("AI Generation Log")
	return {"logs": logs, "total": total}


@frappe.whitelist()
def api_get_quiz_analytics(quiz_id: str):
	"""Returns comprehensive assessment analytics and weak-topic reports for teachers."""
	_check_teacher_or_admin_permission()
	return get_quiz_assessment_report(quiz_id)


@frappe.whitelist()
def api_submit_for_approval(doctype: str, name: str):
	"""Workflow action: Teacher submits Quiz or Question Paper for Principal Approval."""
	_check_teacher_or_admin_permission()
	user = frappe.session.user
	if doctype == "LMS Quiz":
		quiz = frappe.get_doc("LMS Quiz", name)
		quiz.release_status = "Pending Principal Approval"
		quiz.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "success", "release_status": quiz.release_status}
	elif doctype == "AI Question Paper":
		paper = frappe.get_doc("AI Question Paper", name)
		paper.approval_status = "Submitted for Approval"
		paper.reviewed_by = user
		paper.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "success", "approval_status": paper.approval_status}
	frappe.throw(_("Unsupported DocType."))


@frappe.whitelist()
def api_approve_assessment(doctype: str, name: str):
	"""Workflow action: Principal approves Quiz or Question Paper."""
	_check_principal_permission()
	user = frappe.session.user
	if doctype == "LMS Quiz":
		quiz = frappe.get_doc("LMS Quiz", name)
		quiz.release_status = "Released"
		quiz.released_by = user
		quiz.released_on = now_datetime()
		quiz.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "success", "release_status": quiz.release_status}
	elif doctype == "AI Question Paper":
		paper = frappe.get_doc("AI Question Paper", name)
		paper.approval_status = "Principal Approved"
		paper.approved_by = user
		paper.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "success", "approval_status": paper.approval_status}
	frappe.throw(_("Unsupported DocType."))


@frappe.whitelist()
def api_publish_assessment(doctype: str, name: str):
	"""Workflow action: Publish approved assessment to make it available to students."""
	_check_principal_permission()
	user = frappe.session.user
	if doctype == "LMS Quiz":
		quiz = frappe.get_doc("LMS Quiz", name)
		quiz.release_status = "Released"
		quiz.released_by = user
		quiz.released_on = now_datetime()
		quiz.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "success", "release_status": quiz.release_status}
	elif doctype == "AI Question Paper":
		paper = frappe.get_doc("AI Question Paper", name)
		paper.approval_status = "Published"
		paper.approved_by = user
		paper.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "success", "approval_status": paper.approval_status}
	frappe.throw(_("Unsupported DocType."))


@frappe.whitelist()
def api_reject_assessment(doctype: str, name: str, reason: str = ""):
	"""Workflow action: Principal rejects assessment with feedback for the teacher."""
	_check_principal_permission()
	if doctype == "LMS Quiz":
		quiz = frappe.get_doc("LMS Quiz", name)
		quiz.release_status = "Rejected"
		quiz.rejection_reason = reason
		quiz.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "success", "release_status": quiz.release_status}
	elif doctype == "AI Question Paper":
		paper = frappe.get_doc("AI Question Paper", name)
		paper.approval_status = "Rejected"
		paper.rejection_reason = reason
		paper.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "success", "approval_status": paper.approval_status}
	frappe.throw(_("Unsupported DocType."))

