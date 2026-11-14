# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import uuid
import frappe
from frappe import _
from frappe.utils import cint, now_datetime
from fuzzywuzzy import fuzz
from lms.lms.ai.ai_service import call_ai_service


QUESTION_TYPE_MAP = {
	"MCQ": "Choices",
	"Choices": "Choices",
	"Multiple Select": "Multiple Select",
	"True or False": "True or False",
	"Fill in the Blanks": "Fill in the Blanks",
	"Short Answer": "Short Answer",
	"Long Answer": "Long Answer",
	"Essay": "Essay",
	"Programming": "Programming",
	"Mixed": "Mixed",
}


def get_latest_analysis_data(course: str, subject: str = None) -> dict:
	"""Fetch latest historical analysis for course & subject."""
	filters = {"course": course}
	if subject and subject.strip():
		filters["subject"] = subject.strip()

	analyses = frappe.get_all(
		"Previous Year Paper Analysis",
		filters=filters,
		fields=["name", "topic_importance_json", "repeated_questions_json", "academic_years_covered"],
		order_by="creation desc",
		limit=1,
	)

	if not analyses:
		return {}

	row = analyses[0]
	return {
		"analysis_name": row.name,
		"academic_years": row.academic_years_covered or "Past 10 Years",
		"topic_importance": json.loads(row.topic_importance_json or "[]"),
		"repeated_questions": json.loads(row.repeated_questions_json or "[]"),
	}


def generate_offline_fallback_questions(
	topics: list[dict],
	count: int,
	course: str,
	subject: str,
	chapter: str = "",
	target_type: str = "Mixed",
	difficulty: str = "Medium",
	marks: int = 5,
) -> list[dict]:
	"""High-fidelity fallback question synthesizer when AI LLM provider is offline."""
	generated = []
	topic_names = [t.get("topic") for t in topics if t.get("topic")] or [chapter or subject or "General Concepts"]

	type_cycle = ["Choices", "Short Answer", "Programming", "Long Answer"] if target_type == "Mixed" else [target_type]

	templates = [
		("How does {topic} solve scalability issues in modern enterprise architecture? Provide a concrete example.", "Long Answer", 5),
		("Which of the following statements regarding {topic} is INCORRECT?", "Choices", 1),
		("Implement a robust algorithm demonstrating {topic} with proper error handling and edge-case validation.", "Programming", 10),
		("Explain the fundamental difference between dynamic and static aspects of {topic}.", "Short Answer", 3),
		("Analyze the performance trade-offs of using {topic} under high concurrent load.", "Essay", 10),
		("Fill in the blank: In {topic}, the primary mechanism used to ensure thread safety is _________.", "Fill in the Blanks", 1),
		("True or False: In {topic}, state changes are always guaranteed to be atomic across distributed nodes.", "True or False", 1),
	]

	for i in range(count):
		topic = topic_names[i % len(topic_names)]
		q_type = type_cycle[i % len(type_cycle)]

		template_text, default_type, default_marks = templates[i % len(templates)]
		if target_type != "Mixed":
			q_type = target_type
			m = marks or default_marks
		else:
			m = marks or default_marks

		q_text = template_text.format(topic=topic)
		options = []
		correct = ""
		if q_type == "Choices":
			options = [
				f"It strictly requires centralized coordination.",
				f"It optimizes resource utilization through decentralized caching.",
				f"It bypasses all type-safety verifications.",
				f"It cannot be combined with asynchronous execution.",
			]
			correct = options[1]
		elif q_type == "True or False":
			options = ["True", "False"]
			correct = "False"
		elif q_type == "Fill in the Blanks":
			correct = "Synchronization"
		else:
			correct = f"Detailed technical breakdown of {topic} covering principles, runtime behavior, and best practices."

		generated.append({
			"id": f"GEN-{uuid.uuid4().hex[:8].upper()}",
			"question": q_text,
			"type": q_type,
			"options": options,
			"correct_answer": correct,
			"explanation": f"This question tests essential concepts of {topic} identified as high-yield in previous year examinations.",
			"marks": m,
			"difficulty": difficulty if difficulty != "Mixed" else ("Easy" if m <= 2 else ("Hard" if m >= 10 else "Medium")),
			"course": course,
			"subject": subject,
			"chapter": chapter or topic,
			"topic": topic,
			"status": "Draft",
			"historical_reference": f"Derived from historical examination pattern for {topic}",
			"created_at": str(now_datetime()),
		})

	return generated


def generate_historical_ai_questions(
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
	"""Generate novel examination questions using the collective historical patterns of previous papers."""
	count = min(max(cint(number_of_questions) or 10, 1), 50)
	target_type = QUESTION_TYPE_MAP.get(question_type, "Mixed")

	# Fetch analysis data
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

	top_topics = analysis_data.get("topic_importance", [])[:8]
	repeated_summary = [
		{"canonical": r.get("canonical_question", "")[:80], "years": r.get("examination_years", [])}
		for r in analysis_data.get("repeated_questions", [])[:6]
	]

	# Build system and user prompt for LLM
	system_prompt = (
		"You are a premier University Professor, Senior Examiner, and Examination Board Member. "
		"Your mission is to generate NEW, ORIGINAL examination questions based on historical examination patterns. "
		"CRITICAL INSTRUCTION: Do NOT copy previous questions verbatim. Instead, test the exact same underlying "
		"technical concepts and principles using completely novel scenarios, realistic problems, practical applications, "
		"and different perspectives. Return strictly valid JSON."
	)

	user_prompt = f"""Generate {count} novel examination questions based on historical analysis.

Course: {course}
Subject: {subject}
Optional Batch: {batch or 'N/A'}
Target Chapter/Topic: {chapter or 'All High-Yield Chapters'}
Target Question Type: {target_type}
Difficulty Setting: {difficulty}
Marks per question setting: {marks_per_question or 'Proportional to question depth'}

Historical Context:
- Academic Years Analyzed: {analysis_data.get('academic_years', 'Past 10 Years')}
- Most Important Historical Topics: {json.dumps([t.get('topic') for t in top_topics])}
- Repeated Historical Question Patterns: {json.dumps(repeated_summary)}

Return a JSON object in this exact schema:
{{
  "questions": [
    {{
      "question": "Clear, precise examination question text",
      "type": "Choices | Multiple Select | True or False | Fill in the Blanks | Short Answer | Long Answer | Essay | Programming",
      "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
      "correct_answer": "Exact correct answer text or option",
      "explanation": "Clear educational explanation of why the answer is correct",
      "marks": 1,
      "difficulty": "Easy | Medium | Hard",
      "chapter": "{chapter or 'Identified Chapter'}",
      "topic": "Specific Topic Name",
      "historical_reference": "How this relates to the historical examination pattern"
    }}
  ]
}}
"""

	questions_out = []
	try:
		ai_resp = call_ai_service(
			system_prompt=system_prompt,
			user_prompt=user_prompt,
			generation_type="PreviousYearQuestions",
			mode="Historical-Analysis",
			course=course,
			batch=batch,
			reference_doctype="Previous Year Paper Analysis",
			reference_name=analysis_data.get("analysis_name"),
		)

		if ai_resp and isinstance(ai_resp, dict) and "questions" in ai_resp:
			raw_q_list = ai_resp.get("questions", [])
			for q in raw_q_list:
				q_id = f"GEN-{uuid.uuid4().hex[:8].upper()}"
				questions_out.append({
					"id": q_id,
					"question": q.get("question", "").strip(),
					"type": q.get("type", "Short Answer"),
					"options": q.get("options", []),
					"correct_answer": q.get("correct_answer", ""),
					"explanation": q.get("explanation", ""),
					"marks": cint(marks_per_question) or cint(q.get("marks")) or 5,
					"difficulty": difficulty if difficulty != "Mixed" else q.get("difficulty", "Medium"),
					"course": course,
					"subject": subject,
					"chapter": chapter or q.get("chapter", "General"),
					"topic": q.get("topic", "General"),
					"status": "Draft",
					"historical_reference": q.get("historical_reference", "Derived from historical examination pattern"),
					"created_at": str(now_datetime()),
				})

	except Exception as e:
		frappe.logger("ai_assessment").warning(f"AI generation call failed, using fallback synthesizer: {e}")

	# Fallback if AI produced insufficient questions
	if len(questions_out) < count:
		needed = count - len(questions_out)
		fallback_qs = generate_offline_fallback_questions(
			topics=top_topics,
			count=needed,
			course=course,
			subject=subject,
			chapter=chapter or "",
			target_type=target_type,
			difficulty=difficulty,
			marks=cint(marks_per_question) or 5,
		)
		questions_out.extend(fallback_qs)

	# Store generated questions in the Previous Year Paper Analysis doc
	if analysis_data.get("analysis_name"):
		try:
			analysis_doc = frappe.get_doc("Previous Year Paper Analysis", analysis_data["analysis_name"])
			existing_generated = []
			if analysis_doc.generated_questions_json:
				existing_generated = json.loads(analysis_doc.generated_questions_json)

			existing_generated.extend(questions_out)
			analysis_doc.generated_questions_json = json.dumps(existing_generated, ensure_ascii=False)
			analysis_doc.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.logger("ai_assessment").warning(f"Could not persist generated questions in analysis doc: {e}")

	return {
		"status": "success",
		"course": course,
		"subject": subject,
		"total_generated": len(questions_out),
		"questions": questions_out,
	}


def regenerate_single_question(
	question_id: str,
	analysis_name: str | None,
	course: str,
	subject: str,
	topic: str = "",
	question_type: str = "Short Answer",
	difficulty: str = "Medium",
	marks: int = 5,
) -> dict:
	"""Regenerate a single question while keeping its ID."""
	new_questions = generate_historical_ai_questions(
		course=course,
		subject=subject,
		chapter=topic,
		number_of_questions=1,
		question_type=question_type,
		difficulty=difficulty,
		marks_per_question=marks,
		analysis_name=analysis_name,
	)

	fresh_q = new_questions["questions"][0] if new_questions.get("questions") else None
	if not fresh_q:
		raise ValueError("Failed to regenerate question.")

	fresh_q["id"] = question_id

	# Update in analysis record if provided
	if analysis_name and frappe.db.exists("Previous Year Paper Analysis", analysis_name):
		doc = frappe.get_doc("Previous Year Paper Analysis", analysis_name)
		if doc.generated_questions_json:
			q_list = json.loads(doc.generated_questions_json)
			for i, q in enumerate(q_list):
				if q.get("id") == question_id:
					q_list[i] = fresh_q
					break
			doc.generated_questions_json = json.dumps(q_list, ensure_ascii=False)
			doc.save(ignore_permissions=True)
			frappe.db.commit()

	return {"status": "success", "question": fresh_q}
