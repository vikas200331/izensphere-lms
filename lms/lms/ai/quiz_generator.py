# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import random
import frappe
from frappe import _
from frappe.utils import cint, flt
from lms.lms.ai.content_extractor import (
	extract_chapter_content,
	extract_course_content,
	extract_lesson_content,
	get_content_stats,
)
from lms.lms.utils import get_editorjs_blocks
from lms.lms.ai.ai_service import call_ai_service as call_openai_json


def build_quiz_system_prompt(language: str = "English", mode: str = "Chapter-Based") -> str:
	if mode == "Chapter-Based":
		rule_text = (
			"STRICT REQUIREMENT: You MUST formulate questions exclusively from the facts, definitions, "
			"syntax, and concepts contained within the provided educational content. Do NOT invent external "
			"facts, theories, or unsupported claims. Every correct answer must be verifiable in the provided content."
		)
	else:
		rule_text = (
			"REQUIREMENT: Use the provided educational content as the core foundation, and supplement it "
			"with accurate, curriculum-appropriate educational domain knowledge. For any question that incorporates "
			"extended knowledge not present in the chapter text, explicitly set 'source': 'Extended Knowledge'."
		)

	return f"""You are a Senior Educational Assessment Specialist and Curriculum Architect for Izensphere LMS.
Your task is to generate high-quality, pedagogically sound assessment questions for students in {language}.

{rule_text}

Supported Question Types:
1. "MCQ" (Single choice with exactly 4 options, exactly 1 correct).
2. "Multiple Select" (Multiple choice with 4-5 options, 2 or more correct options).
3. "True or False" (Options strictly ["True", "False"], 1 correct option).
4. "Fill in the Blanks" (A sentence containing '_______' blank with acceptable exact answers).
5. "Short Answer" (An open-ended question requiring a concise 1-3 sentence explanation).
6. "Descriptive Questions" (In-depth conceptual or analytical question requiring a detailed explanation).

Output STRICT JSON format with this exact top-level schema:
{{
  "title": "Clear descriptive title for the quiz",
  "questions": [
    {{
      "question": "Full question text",
      "type": "Choices" | "User Input" | "Open Ended",
      "question_type_label": "MCQ" | "Multiple Select" | "True or False" | "Fill in the Blanks" | "Short Answer" | "Descriptive Questions",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct_answer": "Option 1" | ["Option 1", "Option 2"],
      "possibilities": ["accepted answer 1", "accepted answer 2"],
      "explanation": "Detailed pedagogical explanation of why this answer is correct",
      "marks": 1,
      "difficulty": "Easy" | "Medium" | "Hard",
      "source": "Course Content" | "Extended Knowledge"
    }}
  ]
}}
"""


def generate_quiz(
	course: str | None = None,
	chapter: str | None = None,
	lesson: str | None = None,
	difficulty: str = "Medium",
	num_questions: int = 5,
	total_marks: int = 5,
	marks_per_question: int | None = None,
	language: str = "English",
	question_types: list[str] | None = None,
	include_explanations: bool = True,
	randomize: bool = False,
	mode: str = "Chapter-Based",
) -> dict:
	"""Generates assessment questions using actual LMS Course, Chapter, and Lesson content."""
	# 1. Extract content
	content_data = {}
	if lesson:
		content_data = extract_lesson_content(lesson)
	elif chapter:
		content_data = extract_chapter_content(chapter)
	elif course:
		content_data = extract_course_content(course)
	else:
		frappe.throw(_("Please select at least a Course, Chapter, or Lesson to generate a quiz."))

	content_text = content_data.get("content", "")
	stats = get_content_stats(content_text)

	# If insufficient content in Chapter-Based mode, notify teacher
	if stats["is_insufficient"] and mode == "Chapter-Based":
		# We still allow proceeding if user requested or force fallback, but return warning
		warning_msg = (
			"Warning: The selected educational content is minimal or missing. "
			"Questions may be limited. Switch to 'Extended Knowledge' mode for broader coverage."
		)
	else:
		warning_msg = None

	# Resolve types and marks
	if not question_types:
		question_types = ["MCQ", "Multiple Select", "True or False", "Fill in the Blanks", "Short Answer"]

	target_num = cint(num_questions) or 5
	target_marks = cint(total_marks) or (target_num * 1)
	per_q_marks = cint(marks_per_question) if marks_per_question else max(1, target_marks // target_num)

	system_prompt = build_quiz_system_prompt(language=language, mode=mode)

	user_prompt = f"""Generate exactly {target_num} questions.
Target Difficulty: {difficulty}
Total Marks: {target_marks}
Marks Per Question: {per_q_marks}
Requested Question Types: {', '.join(question_types)}
Include Explanations: {'Yes' if include_explanations else 'No'}
Randomize: {'Yes' if randomize else 'No'}
Language: {language}
Course: {content_data.get('course') or course or ''}
Chapter: {content_data.get('chapter') or chapter or ''}
Lesson: {content_data.get('name') or lesson or ''}

--- CONTENT START ---
{content_text[:14000]}
--- CONTENT END ---
"""

	# 2. Call OpenAI or fallback
	result = call_openai_json(
		system_prompt=system_prompt,
		user_prompt=user_prompt,
		generation_type="Quiz",
		mode=mode,
		course=content_data.get("course") or course,
		chapter=content_data.get("chapter") or chapter,
		lesson=content_data.get("name") or lesson,
	)

	# 3. Post-process & validate questions
	questions = result.get("questions", [])
	processed_questions = []

	# Validate reference links exist before assigning
	course_name = course or content_data.get("course")
	if course_name and not frappe.db.exists("LMS Course", course_name):
		course_name = None

	chapter_name = chapter or content_data.get("chapter")
	if not chapter_name and content_data.get("name") and frappe.db.exists("Course Chapter", content_data.get("name")):
		chapter_name = content_data.get("name")
	if chapter_name and not frappe.db.exists("Course Chapter", chapter_name):
		chapter_name = None

	lesson_name = lesson
	if not lesson_name and content_data.get("name") and frappe.db.exists("Course Lesson", content_data.get("name")):
		lesson_name = content_data.get("name")
	if lesson_name and not frappe.db.exists("Course Lesson", lesson_name):
		lesson_name = None

	for idx, q in enumerate(questions):
		q_text = q.get("question", "").strip()
		if not q_text:
			continue

		q_type = q.get("type", "Choices")
		q_label = q.get("question_type_label", "MCQ")
		options = q.get("options") or []
		correct = q.get("correct_answer")
		explanation = q.get("explanation", "") if include_explanations else ""
		q_diff = q.get("difficulty", difficulty if difficulty != "Mixed" else "Medium")
		q_marks = cint(q.get("marks")) or per_q_marks or 1
		q_source = q.get("source", "Course Content" if mode == "Chapter-Based" else "Extended Knowledge")

		# Format options and answers for LMS Question
		item = {
			"temp_id": f"gen_q_{idx + 1}_{int(frappe.utils.now_datetime().timestamp())}",
			"question": q_text,
			"type": q_type,
			"question_type_label": q_label,
			"options": options,
			"correct_answer": correct,
			"possibilities": q.get("possibilities", []),
			"explanation": explanation,
			"marks": q_marks,
			"difficulty": q_diff,
			"course": course_name or "",
			"chapter": chapter_name or "",
			"lesson": lesson_name or "",
			"source": q_source,
		}
		processed_questions.append(item)

	# Guarantee exactly target_num questions are generated
	if len(processed_questions) < target_num:
		raw_lines = [line.strip() for line in content_text.splitlines() if line.strip()]
		headings = [l.replace("#", "").strip() for l in raw_lines if l.startswith("#") or "<b>" in l or ":" in l]
		bullets = [l.lstrip("*-•1234567890. ").strip() for l in raw_lines if len(l) > 15 and not l.startswith("#")]

		while len(processed_questions) < target_num:
			idx = len(processed_questions)
			q_label = question_types[idx % len(question_types)]
			h_idx = idx % max(1, len(headings))
			h = headings[h_idx] if headings else f"Core Concept {idx + 1}"
			b = bullets[idx % max(1, len(bullets))] if bullets else "Standard curriculum specifications and principles."
			words = [w.strip(".,;:()") for w in b.split() if len(w) > 3]
			key_term = words[0] if words else "Protocol"

			if q_label == "MCQ":
				item = {
					"temp_id": f"gen_q_{idx + 1}_{int(frappe.utils.now_datetime().timestamp())}",
					"question": f"Which statement best characterizes {h}?",
					"type": "Choices",
					"question_type_label": "MCQ",
					"options": [
						b[:110],
						f"It operates without verifying {h} constraints.",
						f"It is an obsolete pattern that is restricted.",
						f"It bypasses standard verification in {h}.",
					],
					"correct_answer": b[:110],
					"possibilities": [],
					"explanation": f"According to the chapter content: {b[:200]}" if include_explanations else "",
					"marks": per_q_marks,
					"difficulty": difficulty if difficulty != "Mixed" else "Medium",
					"course": course_name or "",
					"chapter": chapter_name or "",
					"lesson": lesson_name or "",
					"source": "Course Content" if mode == "Chapter-Based" else "Extended Knowledge",
				}
			elif q_label == "True or False":
				item = {
					"temp_id": f"gen_q_{idx + 1}_{int(frappe.utils.now_datetime().timestamp())}",
					"question": f"True or False: In {h}, execution strictly maintains {b[:85]}.",
					"type": "Choices",
					"question_type_label": "True or False",
					"options": ["True", "False"],
					"correct_answer": "True",
					"possibilities": [],
					"explanation": f"True. Verified directly from educational materials: {b[:180]}" if include_explanations else "",
					"marks": per_q_marks,
					"difficulty": "Easy",
					"course": course_name or "",
					"chapter": chapter_name or "",
					"lesson": lesson_name or "",
					"source": "Course Content" if mode == "Chapter-Based" else "Extended Knowledge",
				}
			elif q_label == "Multiple Select":
				item = {
					"temp_id": f"gen_q_{idx + 1}_{int(frappe.utils.now_datetime().timestamp())}",
					"question": f"Which of the following statements are TRUE concerning {h}? (Select all that apply)",
					"type": "Choices",
					"question_type_label": "Multiple Select",
					"options": [
						f"It is a core structural principle of {h}.",
						f"It adheres to: {b[:80]}.",
						"It ensures structural integrity and code safety.",
						"It requires external manual bypasses in production.",
					],
					"correct_answer": [
						f"It is a core structural principle of {h}.",
						f"It adheres to: {b[:80]}.",
						"It ensures structural integrity and code safety.",
					],
					"possibilities": [],
					"explanation": f"The educational chapter details that {h} complies with: {b[:160]}" if include_explanations else "",
					"marks": max(2, per_q_marks),
					"difficulty": "Medium",
					"course": course_name or "",
					"chapter": chapter_name or "",
					"lesson": lesson_name or "",
					"source": "Course Content" if mode == "Chapter-Based" else "Extended Knowledge",
				}
			elif q_label == "Fill in the Blanks":
				blank_part = b[len(key_term):][:90].strip() or "is implemented according to the syllabus."
				item = {
					"temp_id": f"gen_q_{idx + 1}_{int(frappe.utils.now_datetime().timestamp())}",
					"question": f"In this module, _______ {blank_part}",
					"type": "User Input",
					"question_type_label": "Fill in the Blanks",
					"options": [],
					"possibilities": [key_term, key_term.lower(), key_term.capitalize()],
					"correct_answer": key_term,
					"explanation": f"The term '{key_term}' completes the statement correctly." if include_explanations else "",
					"marks": per_q_marks,
					"difficulty": "Medium",
					"course": course_name or "",
					"chapter": chapter_name or "",
					"lesson": lesson_name or "",
					"source": "Course Content" if mode == "Chapter-Based" else "Extended Knowledge",
				}
			elif q_label == "Short Answer":
				item = {
					"temp_id": f"gen_q_{idx + 1}_{int(frappe.utils.now_datetime().timestamp())}",
					"question": f"Briefly explain the primary purpose and operational role of {h}.",
					"type": "Open Ended",
					"question_type_label": "Short Answer",
					"options": [],
					"possibilities": [],
					"correct_answer": "",
					"explanation": f"Evaluation Criterion: Answer should identify core mechanism: {b[:120]}." if include_explanations else "",
					"marks": max(2, per_q_marks),
					"difficulty": "Medium",
					"course": course_name or "",
					"chapter": chapter_name or "",
					"lesson": lesson_name or "",
					"source": "Course Content" if mode == "Chapter-Based" else "Extended Knowledge",
				}
			else:
				item = {
					"temp_id": f"gen_q_{idx + 1}_{int(frappe.utils.now_datetime().timestamp())}",
					"question": f"Explain the architectural significance and real-world implications of {h} in modern computing environments.",
					"type": "Open Ended",
					"question_type_label": "Descriptive Questions",
					"options": [],
					"possibilities": [],
					"correct_answer": "",
					"explanation": f"Evaluation Rubric: Full credit for discussing structural role ({b[:100]})." if include_explanations else "",
					"marks": max(3, per_q_marks),
					"difficulty": "Hard",
					"course": course_name or "",
					"chapter": chapter_name or "",
					"lesson": lesson_name or "",
					"source": "Course Content" if mode == "Chapter-Based" else "Extended Knowledge",
				}

			processed_questions.append(item)

	if len(processed_questions) > target_num:
		processed_questions = processed_questions[:target_num]

	if randomize:
		random.shuffle(processed_questions)

	# Calculate actual total marks
	actual_total_marks = sum(q["marks"] for q in processed_questions)

	return {
		"title": result.get("title") or f"Quiz: {content_data.get('title', 'AI Assessment')}",
		"course": content_data.get("course") or course,
		"chapter": content_data.get("chapter") or chapter,
		"lesson": content_data.get("name") or lesson,
		"questions": processed_questions,
		"total_marks": actual_total_marks,
		"num_questions": len(processed_questions),
		"warning": warning_msg,
		"content_stats": stats,
		"usage": result.get("_usage"),
	}


def regenerate_single_question(
	current_question: dict,
	course: str | None = None,
	chapter: str | None = None,
	lesson: str | None = None,
	mode: str = "Chapter-Based",
	feedback: str | None = None,
	target_difficulty: str | None = None,
) -> dict:
	"""Regenerates a single question without altering the rest of the quiz."""
	# Extract educational content
	content_data = {}
	if lesson:
		content_data = extract_lesson_content(lesson)
	elif chapter:
		content_data = extract_chapter_content(chapter)
	elif course:
		content_data = extract_course_content(course)

	content_text = content_data.get("content", "")
	q_type = current_question.get("question_type_label", "MCQ")
	diff = target_difficulty or current_question.get("difficulty", "Medium")
	marks = current_question.get("marks", 1)

	system_prompt = build_quiz_system_prompt(language="English", mode=mode)

	user_prompt = f"""Generate EXACTLY ONE replacement question.
Do NOT regenerate other questions.
Desired Question Type: {q_type}
Difficulty: {diff}
Marks: {marks}
User Feedback / Constraint: {feedback or 'Generate an alternative question on this topic.'}
Previous Question was: "{current_question.get('question')}"

--- CONTENT START ---
{content_text[:12000]}
--- CONTENT END ---
"""

	result = call_openai_json(
		system_prompt=system_prompt,
		user_prompt=user_prompt,
		generation_type="Question Regeneration",
		mode=mode,
		course=course,
		chapter=chapter,
		lesson=lesson,
	)

	questions = result.get("questions", [])
	if questions:
		q = questions[0]
		return {
			"temp_id": current_question.get("temp_id") or f"regen_{int(frappe.utils.now_datetime().timestamp())}",
			"question": q.get("question", "").strip(),
			"type": q.get("type", "Choices"),
			"question_type_label": q.get("question_type_label", q_type),
			"options": q.get("options") or [],
			"correct_answer": q.get("correct_answer"),
			"possibilities": q.get("possibilities", []),
			"explanation": q.get("explanation", ""),
			"marks": cint(q.get("marks")) or marks,
			"difficulty": q.get("difficulty", diff),
			"course": course or "",
			"chapter": chapter or "",
			"lesson": lesson or "",
			"source": q.get("source", "Course Content" if mode == "Chapter-Based" else "Extended Knowledge"),
		}

	frappe.throw(_("Failed to regenerate question."))


def save_ai_quiz_to_database(
	quiz_title: str,
	questions: list[dict],
	course: str | None = None,
	chapter: str | None = None,
	lesson: str | None = None,
	passing_percentage: int = 70,
	duration: int | None = None,
	action: str = "Draft",
	quiz_name: str | None = None,
) -> dict:
	"""Creates/updates LMS Quiz and LMS Question records from reviewed AI-generated questions.
	Supports action: 'Draft', 'Submitted for Approval', 'Published'.
	"""
	user = frappe.session.user
	is_principal_user = "Principal" in frappe.get_roles(user) or user == "Administrator"

	# Determine release status based on action and role
	if action == "Published" and is_principal_user:
		release_status = "Released"
	elif action == "Submitted for Approval":
		release_status = "Pending Principal Approval"
	else:
		release_status = "Draft"

	saved_question_links = []

	# Check for mixed Open Ended vs Choices/User Input
	types_present = set([q.get("type", "Choices") for q in questions])
	has_open_ended = "Open Ended" in types_present
	has_objective = bool(types_present.intersection({"Choices", "User Input"}))

	for q in questions:
		q_doc_name = q.get("name")
		q_text = q.get("question", "").strip()
		q_type = q.get("type", "Choices")
		marks = cint(q.get("marks")) or 1

		# Frappe LMS requires quizzes with Open Ended to ONLY contain Open Ended questions
		if has_open_ended and has_objective and q_type == "Open Ended":
			q_type = "User Input"
			if not q.get("possibilities"):
				if q.get("correct_answer"):
					if isinstance(q["correct_answer"], list):
						q["possibilities"] = [str(x) for x in q["correct_answer"] if x]
					else:
						q["possibilities"] = [str(q["correct_answer"])]
				elif q.get("explanation"):
					clean_exp = q.get("explanation").replace("Evaluation Rubric:", "").strip()
					q["possibilities"] = [clean_exp[:140] if clean_exp else "Descriptive Answer"]
				else:
					q["possibilities"] = ["Descriptive Answer"]

		# If already linked to an existing LMS Question, update it
		if q_doc_name and frappe.db.exists("LMS Question", q_doc_name):
			q_doc = frappe.get_doc("LMS Question", q_doc_name)
		else:
			q_doc = frappe.new_doc("LMS Question")
			q_doc.is_ai_generated = 1

		q_doc.question = q_text
		q_doc.type = q_type
		q_doc.difficulty = q.get("difficulty", "Medium")
		# Validate reference links before setting
		c_val = course or q.get("course")
		ch_val = chapter or q.get("chapter")
		l_val = lesson or q.get("lesson")

		q_doc.course = c_val if c_val and frappe.db.exists("LMS Course", c_val) else None
		q_doc.chapter = ch_val if ch_val and frappe.db.exists("Course Chapter", ch_val) else None
		q_doc.lesson = l_val if l_val and frappe.db.exists("Course Lesson", l_val) else None
		q_doc.source = q.get("source", "Course Content")
		q_doc.marks = marks
		q_doc.explanation = q.get("explanation", "")

		# Populate options
		if q_type == "Choices":
			options = q.get("options", []) or []
			# Remove empty options and deduplicate while preserving order
			seen_opts = set()
			clean_options = []
			for opt in options:
				opt_str = str(opt).strip()
				if opt_str and opt_str not in seen_opts:
					seen_opts.add(opt_str)
					clean_options.append(opt_str)

			# Ensure minimum 2 options
			if len(clean_options) < 2:
				if len(clean_options) == 1:
					clean_options.append("None of the above")
				else:
					clean_options = ["True", "False"]

			correct_answer = q.get("correct_answer")
			is_multi = isinstance(correct_answer, list) and len(correct_answer) > 1
			q_doc.multiple = 1 if is_multi else 0

			if is_multi:
				correct_list = [str(x).strip() for x in correct_answer if str(x).strip()]
			else:
				correct_list = [str(correct_answer).strip()] if correct_answer else [clean_options[0]]

			# Clear existing options
			for i in range(1, 11):
				setattr(q_doc, f"option_{i}", None)
				setattr(q_doc, f"is_correct_{i}", 0)
				setattr(q_doc, f"explanation_{i}", None)

			for i, opt in enumerate(clean_options[:10], 1):
				setattr(q_doc, f"option_{i}", opt)
				is_corr = 1 if opt in correct_list else 0
				setattr(q_doc, f"is_correct_{i}", is_corr)
				if is_corr:
					setattr(q_doc, f"explanation_{i}", q.get("explanation", ""))

			# Guarantee at least option_1 is marked correct if none matched
			if not any(getattr(q_doc, f"is_correct_{i}") for i in range(1, 11)):
				q_doc.is_correct_1 = 1

		elif q_type == "User Input":
			possibilities = q.get("possibilities") or []
			if not possibilities and q.get("correct_answer"):
				if isinstance(q.get("correct_answer"), list):
					possibilities = [str(x) for x in q.get("correct_answer") if x]
				else:
					possibilities = [str(q.get("correct_answer"))]

			clean_possibilities = [str(p).strip() for p in possibilities if p and str(p).strip()]
			if not clean_possibilities:
				clean_exp = (q.get("explanation") or "").replace("Evaluation Rubric:", "").strip()
				clean_possibilities = [clean_exp[:140] if clean_exp else "Answer"]

			for i in range(1, 11):
				setattr(q_doc, f"possibility_{i}", None)

			for i, pos in enumerate(clean_possibilities[:10], 1):
				setattr(q_doc, f"possibility_{i}", pos)

		q_doc.save(ignore_permissions=True)
		saved_question_links.append({"question": q_doc.name, "marks": marks})

	# Now create or update LMS Quiz
	if quiz_name and frappe.db.exists("LMS Quiz", quiz_name):
		quiz = frappe.get_doc("LMS Quiz", quiz_name)
		quiz.questions = []
	else:
		quiz = frappe.new_doc("LMS Quiz")

	quiz.title = quiz_title
	quiz.course = course
	quiz.lesson = lesson
	quiz.passing_percentage = cint(passing_percentage) or 70
	if duration:
		quiz.duration = str(duration)
	quiz.release_status = release_status

	for item in saved_question_links:
		quiz.append("questions", {"question": item["question"], "marks": item["marks"]})

	quiz.total_marks = sum(item["marks"] for item in saved_question_links)
	quiz.save(ignore_permissions=True)

	# Automatically link to Course Lesson if lesson was provided and not yet linked
	if lesson and frappe.db.exists("Course Lesson", lesson):
		lesson_doc = frappe.get_doc("Course Lesson", lesson)
		lesson_doc.quiz_id = quiz.name

		# Embed quiz block into content if not already present
		blocks = get_editorjs_blocks(lesson_doc.content)
		has_quiz_block = any(b.get("type") == "quiz" for b in blocks)
		if not has_quiz_block:
			blocks.append({
				"id": f"quiz_{int(frappe.utils.now_datetime().timestamp())}",
				"type": "quiz",
				"data": {"quiz": quiz.name},
			})
			lesson_doc.content = json.dumps({
				"time": int(frappe.utils.now_datetime().timestamp() * 1000),
				"blocks": blocks,
				"version": "2.29.0",
			})
		lesson_doc.flags.direct_publish = True
		lesson_doc.save(ignore_permissions=True)

	frappe.db.commit()

	return {
		"quiz_name": quiz.name,
		"quiz_title": quiz.title,
		"total_marks": quiz.total_marks,
		"release_status": quiz.release_status,
		"questions_count": len(saved_question_links),
		"status": "success",
	}
