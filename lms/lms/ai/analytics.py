# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import cint, flt


def get_quiz_assessment_report(quiz_id: str) -> dict:
	"""Generates in-depth teacher analytics for a quiz:
	- Student-wise scores and rank
	- Chapter-wise & topic-wise accuracy
	- Question-wise accuracy & error rates
	- Difficulty-wise performance (Easy vs Medium vs Hard)
	- Weak-topic identification
	- Pedagogical recommendations for instructional improvement
	"""
	if not frappe.db.exists("LMS Quiz", quiz_id):
		frappe.throw(_("Quiz {0} not found.").format(quiz_id), frappe.DoesNotExistError)

	quiz = frappe.get_doc("LMS Quiz", quiz_id)

	# Fetch all submissions for this quiz
	submissions = frappe.get_all(
		"LMS Quiz Submission",
		filters={"quiz": quiz_id},
		fields=["name", "member", "member_name", "score", "score_out_of", "percentage", "passing_percentage", "creation", "is_late"],
		order_by="score desc",
	)

	total_submissions = len(submissions)
	if total_submissions == 0:
		return {
			"quiz_title": quiz.title,
			"quiz_name": quiz.name,
			"total_marks": quiz.total_marks,
			"total_submissions": 0,
			"average_score": 0,
			"pass_rate": 0,
			"student_scores": [],
			"question_performance": [],
			"chapter_performance": [],
			"difficulty_performance": {},
			"weak_topics": [],
			"recommendations": [
				"No student submissions recorded yet. Once students complete the quiz, real-time analytics will populate here."
			],
		}

	scores = [s.score for s in submissions]
	avg_score = round(sum(scores) / total_submissions, 2)
	passed_count = sum(1 for s in submissions if s.percentage >= s.passing_percentage)
	pass_rate = round((passed_count / total_submissions) * 100, 1)

	# Fetch detailed question results for all submissions
	sub_names = [s.name for s in submissions]
	results = frappe.get_all(
		"LMS Quiz Result",
		filters={"parent": ["in", sub_names]},
		fields=["parent", "question_name", "marks", "marks_out_of", "is_correct"],
	)

	# Question metadata map
	question_names = list(set([r.question_name for r in results if r.question_name]))
	q_meta = {}
	if question_names:
		q_docs = frappe.get_all(
			"LMS Question",
			filters={"name": ["in", question_names]},
			fields=["name", "question", "type", "difficulty", "chapter", "course"],
		)
		for qd in q_docs:
			q_meta[qd.name] = qd

	# Aggregate question performance
	q_stats = {}
	for r in results:
		q_id = r.question_name or "Unknown"
		if q_id not in q_stats:
			meta = q_meta.get(q_id, {})
			q_stats[q_id] = {
				"question_id": q_id,
				"question_text": meta.get("question", "")[:90] or q_id,
				"difficulty": meta.get("difficulty", "Medium"),
				"chapter": meta.get("chapter", "General"),
				"attempts": 0,
				"correct_count": 0,
				"total_marks_obtained": 0,
				"total_marks_possible": 0,
			}
		q_stats[q_id]["attempts"] += 1
		if r.is_correct:
			q_stats[q_id]["correct_count"] += 1
		q_stats[q_id]["total_marks_obtained"] += r.marks or 0
		q_stats[q_id]["total_marks_possible"] += r.marks_out_of or 1

	q_perf_list = []
	for q_id, data in q_stats.items():
		acc = round((data["correct_count"] / data["attempts"]) * 100, 1) if data["attempts"] > 0 else 0
		data["accuracy_percentage"] = acc
		q_perf_list.append(data)

	# Sort questions by lowest accuracy (hardest first)
	q_perf_list.sort(key=lambda x: x["accuracy_percentage"])

	# Chapter-wise performance
	chapter_stats = {}
	for q in q_perf_list:
		ch = q["chapter"] or "General Curriculum"
		if ch not in chapter_stats:
			chapter_stats[ch] = {"chapter": ch, "attempts": 0, "correct": 0}
		chapter_stats[ch]["attempts"] += q["attempts"]
		chapter_stats[ch]["correct"] += q["correct_count"]

	ch_perf_list = []
	for ch, data in chapter_stats.items():
		acc = round((data["correct"] / data["attempts"]) * 100, 1) if data["attempts"] > 0 else 0
		ch_perf_list.append({"chapter": ch, "accuracy": acc, "attempts": data["attempts"]})
	ch_perf_list.sort(key=lambda x: x["accuracy"])

	# Difficulty-wise performance
	diff_stats = {"Easy": {"attempts": 0, "correct": 0}, "Medium": {"attempts": 0, "correct": 0}, "Hard": {"attempts": 0, "correct": 0}}
	for q in q_perf_list:
		diff = q.get("difficulty", "Medium")
		if diff not in diff_stats:
			diff_stats[diff] = {"attempts": 0, "correct": 0}
		diff_stats[diff]["attempts"] += q["attempts"]
		diff_stats[diff]["correct"] += q["correct_count"]

	diff_perf = {}
	for d, data in diff_stats.items():
		acc = round((data["correct"] / data["attempts"]) * 100, 1) if data["attempts"] > 0 else 0
		diff_perf[d] = {"accuracy": acc, "attempts": data["attempts"]}

	# Identify Weak Topics (< 60% accuracy)
	weak_topics = []
	for ch in ch_perf_list:
		if ch["accuracy"] < 60.0:
			weak_topics.append(f"{ch['chapter']} ({ch['accuracy']}% accuracy)")

	# Formulate Pedagogical Recommendations
	recommendations = []
	if pass_rate < 50.0:
		recommendations.append(
			"Low overall pass rate (under 50%). Consider scheduling a dedicated revision class and reviewing foundational concepts."
		)
	if weak_topics:
		recommendations.append(
			f"Weak student performance identified in: {', '.join(weak_topics[:3])}. Recommend assigning targeted supplementary readings and remedial exercises."
		)
	if diff_perf.get("Hard", {}).get("accuracy", 100) < 35.0:
		recommendations.append(
			"Students scored below 35% on high-difficulty questions. Practice multi-step problem solving and application-oriented reasoning in upcoming lessons."
		)
	if not recommendations:
		recommendations.append(
			"Overall cohort performance is strong across chapters. Students demonstrated proficiency in both objective and conceptual evaluations."
		)

	return {
		"quiz_title": quiz.title,
		"quiz_name": quiz.name,
		"total_marks": quiz.total_marks,
		"total_submissions": total_submissions,
		"average_score": avg_score,
		"pass_rate": pass_rate,
		"student_scores": submissions,
		"question_performance": q_perf_list,
		"chapter_performance": ch_perf_list,
		"difficulty_performance": diff_perf,
		"weak_topics": weak_topics,
		"recommendations": recommendations,
	}

