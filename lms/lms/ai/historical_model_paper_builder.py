# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import uuid
import frappe
from frappe import _
from frappe.utils import cint, now_datetime
from lms.lms.ai.historical_question_generator import (
	build_comprehensive_answer_and_rubric,
	generate_historical_ai_questions,
	get_latest_analysis_data,
)


SECTION_TYPE_MAP = {
	"Choices": "MCQ",
	"MCQ": "MCQ",
	"True or False": "True/False",
	"True/False": "True/False",
	"Fill in the Blanks": "Fill in the Blanks",
	"Short Answer": "Short Answer",
	"Long Answer": "Long Answer",
	"Essay": "Descriptive Questions",
	"Descriptive Questions": "Descriptive Questions",
	"Programming": "Application-Based",
	"Application-Based": "Application-Based",
	"Mixed": "Mixed",
}


def default_section_blueprint(total_marks: int = 100) -> list[dict]:
	"""Generates standard multi-section blueprint proportional to total marks."""
	if total_marks == 100:
		return [
			{
				"section_name": "Section A",
				"title": "Objective & Conceptual Questions",
				"instructions": "Answer all questions. Each question carries 1 mark.",
				"question_type": "MCQ",
				"num_questions": 10,
				"marks_per_question": 1,
				"total_marks": 10,
			},
			{
				"section_name": "Section B",
				"title": "Short Answer & Core Definitions",
				"instructions": "Answer all questions. Each question carries 4 marks.",
				"question_type": "Short Answer",
				"num_questions": 5,
				"marks_per_question": 4,
				"total_marks": 20,
			},
			{
				"section_name": "Section C",
				"title": "Analytical & Problem-Solving Questions",
				"instructions": "Answer all questions. Each question carries 6 marks.",
				"question_type": "Long Answer",
				"num_questions": 5,
				"marks_per_question": 6,
				"total_marks": 30,
			},
			{
				"section_name": "Section D",
				"title": "Comprehensive & Programming / Essay Questions",
				"instructions": "Answer all questions. Each question carries 10 marks.",
				"question_type": "Descriptive Questions",
				"num_questions": 4,
				"marks_per_question": 10,
				"total_marks": 40,
			},
		]
	elif total_marks == 50:
		return [
			{
				"section_name": "Section A",
				"title": "Objective Type",
				"instructions": "Answer all questions. Each question carries 1 mark.",
				"question_type": "MCQ",
				"num_questions": 10,
				"marks_per_question": 1,
				"total_marks": 10,
			},
			{
				"section_name": "Section B",
				"title": "Short Answer",
				"instructions": "Answer all questions. Each question carries 4 marks.",
				"question_type": "Short Answer",
				"num_questions": 5,
				"marks_per_question": 4,
				"total_marks": 20,
			},
			{
				"section_name": "Section C",
				"title": "Long Answer",
				"instructions": "Answer all questions. Each question carries 10 marks.",
				"question_type": "Long Answer",
				"num_questions": 2,
				"marks_per_question": 10,
				"total_marks": 20,
			},
		]
	else:
		return [
			{
				"section_name": "Section A",
				"title": "General Questions",
				"instructions": "Answer all questions.",
				"question_type": "Mixed",
				"num_questions": max(1, total_marks // 5),
				"marks_per_question": 5,
				"total_marks": total_marks,
			}
		]


def generate_historical_model_paper(
	title: str,
	course: str,
	subject: str,
	batch: str | None = None,
	chapters: list[str] | str | None = None,
	total_marks: int = 100,
	duration: str = "3 Hours",
	sections_config: list[dict] | None = None,
	difficulty_easy_pct: int = 30,
	difficulty_medium_pct: int = 40,
	difficulty_hard_pct: int = 30,
	analysis_name: str | None = None,
) -> dict:
	"""Builds a complete Model Examination Paper based on collective historical examination paper patterns."""
	total_marks = cint(total_marks) or 100

	# Ensure sections config
	sections = sections_config or default_section_blueprint(total_marks)

	# Validate total marks match
	calculated_sum = sum(cint(s.get("total_marks", s.get("num_questions", 1) * s.get("marks_per_question", 1))) for s in sections)
	if calculated_sum != total_marks:
		frappe.throw(
			_(
				"Total marks validation failed: Sections sum up to {0} marks, but total marks is set to {1}. Marks must match exactly."
			).format(calculated_sum, total_marks)
		)

	# Validate difficulty percentage
	easy = cint(difficulty_easy_pct or 0)
	med = cint(difficulty_medium_pct or 0)
	hard = cint(difficulty_hard_pct or 0)
	if (easy + med + hard) > 0 and (easy + med + hard) != 100:
		frappe.throw(_("Difficulty percentages must sum to 100%."))

	# Resolve chapters string
	chapter_str = ", ".join(chapters) if isinstance(chapters, list) else (chapters or "")

	# Fetch historical analysis
	analysis_data = {}
	if analysis_name and frappe.db.exists("Previous Year Paper Analysis", analysis_name):
		doc = frappe.get_doc("Previous Year Paper Analysis", analysis_name)
		analysis_data = {
			"analysis_name": doc.name,
			"academic_years": doc.academic_years_covered or "Past 10 Years",
			"topic_importance": json.loads(doc.topic_importance_json or "[]"),
			"repeated_questions": json.loads(doc.repeated_questions_json or "[]"),
		}
	else:
		analysis_data = get_latest_analysis_data(course, subject)

	# Create new AI Question Paper
	paper_doc = frappe.new_doc("AI Question Paper")
	paper_doc.title = title or f"Model Paper: {subject} ({course})"
	paper_doc.course = course
	paper_doc.batch = batch
	paper_doc.subject = subject
	paper_doc.total_marks = total_marks
	paper_doc.duration = duration or "3 Hours"
	paper_doc.examination_type = "Practice Test"  # Valid option in AI Question Paper
	paper_doc.approval_status = "Draft"  # Strictly Draft, NOT published
	paper_doc.difficulty_easy_pct = easy
	paper_doc.difficulty_medium_pct = med
	paper_doc.difficulty_hard_pct = hard
	paper_doc.generation_mode = "Chapter-Based"
	paper_doc.selected_chapters = chapter_str
	paper_doc.created_by_teacher = frappe.session.user
	paper_doc.instructions = (
		"1. Please verify that this question paper contains all printed pages and designated sections.\n"
		"2. Write your Candidate Roll Number and Name in the designated boxes on the paper/booklet.\n"
		"3. All sections are compulsory. Internal choice questions ('OR') are provided in higher-mark sections.\n"
		"4. Figures to the right indicate full marks assigned to each question.\n"
		"5. Illustrate your answers with clear diagrams, algorithms, and syntactically verified code snippets where applicable."
	)

	built_sections = []
	all_answer_keys = []

	for s_idx, sec in enumerate(sections, 1):
		s_name = sec.get("section_name", f"Section {chr(64 + s_idx)}")
		s_title = sec.get("title", f"Section {chr(64 + s_idx)}")
		s_instr = sec.get("instructions", "Answer all questions according to instructions.")
		s_type = sec.get("question_type", "Choices")
		s_num = cint(sec.get("num_questions", 1))
		s_marks_each = cint(sec.get("marks_per_question", 1))
		s_total = s_num * s_marks_each

		# Generate questions for this section
		gen_res = generate_historical_ai_questions(
			course=course,
			subject=subject,
			batch=batch,
			chapter=chapter_str,
			number_of_questions=s_num,
			question_type=s_type,
			difficulty="Mixed",
			marks_per_question=s_marks_each,
			analysis_name=analysis_data.get("analysis_name"),
		)

		section_questions = gen_res.get("questions", [])

		# Format section questions with exhaustive marks-proportional answers and rubrics
		formatted_qs = []
		for q_idx, q in enumerate(section_questions, 1):
			# For questions carrying 5+ marks, provide an authentic internal choice question ("OR")
			internal_choice = None
			if s_marks_each >= 5:
				alt_topic = f"{q.get('topic', 'Core Concept')} Alternative Architecture"
				alt_pack = build_comprehensive_answer_and_rubric(
					topic=alt_topic,
					q_text=f"Explain the design, internal execution, and implementation of {alt_topic}.",
					q_type=q.get("type", s_type),
					marks=s_marks_each,
					subject=subject,
					course=course,
				)
				internal_choice = {
					"question": f"Explain the architectural design, execution flow, and practical implementation of {alt_topic} with appropriate error handling and complexity analysis.",
					"type": q.get("type", s_type),
					"options": [],
					"marks": s_marks_each,
					"correct_answer": alt_pack["correct_answer"],
					"answer_key_detail": alt_pack["answer_key_detail"],
					"solution": alt_pack["solution"],
					"explanation": alt_pack["explanation"],
				}

			formatted_qs.append({
				"id": q.get("id", f"Q-{s_idx}-{q_idx}"),
				"question_number": f"{s_idx}.{q_idx}",
				"question": q.get("question"),
				"type": q.get("type", s_type),
				"options": q.get("options", []),
				"marks": s_marks_each,
				"difficulty": q.get("difficulty", "Medium"),
				"topic": q.get("topic", "General"),
				"correct_answer": q.get("correct_answer", ""),
				"answer_key_detail": q.get("answer_key_detail", ""),
				"solution": q.get("solution", ""),
				"explanation": q.get("explanation", ""),
				"internal_choice_question": internal_choice,
				"historical_reference": q.get("historical_reference", ""),
			})

			all_answer_keys.append({
				"section": s_name,
				"question_number": f"{s_idx}.{q_idx}",
				"question_snippet": (q.get("question") or "")[:80] + "...",
				"correct_answer": q.get("correct_answer", "See solution"),
				"answer_key_detail": q.get("answer_key_detail", ""),
				"solution": q.get("solution", ""),
				"explanation": q.get("explanation", ""),
				"marks": s_marks_each,
				"internal_choice_question": internal_choice,
			})

		s_type_validated = SECTION_TYPE_MAP.get(s_type, "Mixed")
		built_sections.append({
			"section_name": s_name,
			"title": s_title,
			"instructions": s_instr,
			"question_type": s_type_validated,
			"marks_per_question": s_marks_each,
			"total_marks": s_total,
			"questions_data": json.dumps(formatted_qs, ensure_ascii=False),
		})

		paper_doc.append("sections", {
			"section_name": s_name,
			"title": s_title,
			"instructions": s_instr,
			"question_type": s_type_validated,
			"marks_per_question": s_marks_each,
			"total_marks": s_total,
			"questions_data": json.dumps(formatted_qs, ensure_ascii=False),
		})

	# Set paper_json
	paper_payload = {
		"title": paper_doc.title,
		"course": course,
		"subject": subject,
		"total_marks": total_marks,
		"duration": duration,
		"sections": built_sections,
		"answer_keys": all_answer_keys,
		"academic_years_basis": analysis_data.get("academic_years", "Past 10 Years"),
	}
	paper_doc.paper_json = json.dumps(paper_payload, ensure_ascii=False)

	paper_doc.save(ignore_permissions=True)
	frappe.db.commit()

	# Record paper in Previous Year Paper Analysis doc
	if analysis_data.get("analysis_name"):
		try:
			analysis_doc = frappe.get_doc("Previous Year Paper Analysis", analysis_data["analysis_name"])
			existing_papers = []
			if analysis_doc.model_papers_json:
				existing_papers = json.loads(analysis_doc.model_papers_json)
			existing_papers.append({
				"paper_name": paper_doc.name,
				"title": paper_doc.title,
				"total_marks": total_marks,
				"created_at": str(now_datetime()),
			})
			analysis_doc.model_papers_json = json.dumps(existing_papers, ensure_ascii=False)
			analysis_doc.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.logger("ai_assessment").warning(f"Could not link model paper in analysis: {e}")

	return {
		"status": "success",
		"paper_name": paper_doc.name,
		"title": paper_doc.title,
		"total_marks": total_marks,
		"duration": duration,
		"sections_count": len(built_sections),
		"paper_payload": paper_payload,
	}
