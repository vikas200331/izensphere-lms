# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import re
from collections import Counter, defaultdict
import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime
from fuzzywuzzy import fuzz
from lms.lms.ai.document_extractor import process_question_paper_document
from lms.lms.ai.ai_service import call_ai_service


def get_course_chapters_and_topics(course: str) -> list[dict]:
	"""Retrieve existing chapters and lessons from LMS Course to anchor topic matching."""
	chapters_data = []
	if not course:
		return chapters_data

	try:
		chapters = frappe.get_all(
			"Course Chapter",
			filters={"course": course},
			fields=["name", "title"],
			order_by="idx asc",
		)
		for ch in chapters:
			# Get lessons under this chapter
			lessons = frappe.get_all(
				"Course Lesson",
				filters={"chapter": ch.name},
				fields=["name", "title"],
				order_by="idx asc",
			)
			chapters_data.append({
				"chapter": ch.title or ch.name,
				"chapter_name": ch.name,
				"lessons": [l.title for l in lessons if l.title],
			})
	except Exception as e:
		frappe.logger("ai_assessment").warning(f"Could not load chapters for {course}: {e}")

	return chapters_data


def clean_question_text(text: str) -> str:
	"""Normalize question text for fuzzy clustering."""
	if not text:
		return ""
	# Remove question prefixes e.g. "1.", "Q1:", "(a)"
	cleaned = re.sub(r"^(?:(?:Q(?:uestion)?\.?\s*\d+[a-z]?)|(?:\d{1,3}[\.\)\-]))\s*", "", text, flags=re.I)
	# Remove marks indicators e.g. [5 Marks], (10M)
	cleaned = re.sub(r"\[\s*\d+\s*(?:marks?|m)?\s*\]|\(\s*\d+\s*(?:marks?|m)?\s*\)|=\s*\d+\s*marks?", "", cleaned, flags=re.I)
	# Remove extra punctuation and whitespace
	cleaned = re.sub(r"[^\w\s]", " ", cleaned).lower()
	return re.sub(r"\s+", " ", cleaned).strip()


def detect_question_difficulty(question: str, marks: int, q_type: str) -> str:
	"""Heuristic difficulty estimation based on marks, verbs, and question complexity."""
	lower = (question or "").lower()
	marks = cint(marks) or 1

	if marks >= 10 or any(w in lower for w in ["critically analyze", "design", "evaluate", "implement", "synthesize", "prove that"]):
		return "Hard"
	elif marks >= 5 or any(w in lower for w in ["explain", "compare", "differentiate", "derive", "discuss", "illustrate", "write a program"]):
		return "Medium"
	elif marks <= 2 or q_type in ["Choices", "True or False", "Fill in the Blanks"] or any(w in lower for w in ["what is", "define", "name the", "list", "state"]):
		return "Easy"
	else:
		return "Medium"


def map_question_to_chapter_or_topic(question_text: str, course_chapters: list[dict], subject: str = "") -> str:
	"""Map a question to an existing course chapter or infer prominent subject topic."""
	clean = clean_question_text(question_text)

	# 1. Check direct match against Course Chapters & Lessons
	for ch_info in course_chapters:
		ch_title = ch_info["chapter"].lower()
		if len(ch_title) > 3 and ch_title in clean:
			return ch_info["chapter"]
		for lesson in ch_info.get("lessons", []):
			l_title = lesson.lower()
			if len(l_title) > 3 and l_title in clean:
				return ch_info["chapter"]

	# 2. Common CS & Engineering Topic Keywords Dictionary
	topic_rules = [
		(r"\b(oop|object oriented|class|object|encapsulation|polymorphism|inheritance|abstraction)\b", "Object-Oriented Programming"),
		(r"\b(exception|try|catch|throw|finally|error handling)\b", "Exception Handling"),
		(r"\b(multithreading|thread|concurrency|synchronization|runnable)\b", "Multithreading & Concurrency"),
		(r"\b(collection|arraylist|hashmap|linkedlist|vector|stack|queue|iterator)\b", "Collections Framework"),
		(r"\b(database|sql|select|join|acid|normalization|rdbms|jdbc|transaction)\b", "Database Management & SQL"),
		(r"\b(interface|abstract class|packages|namespace|imports)\b", "Interfaces & Packages"),
		(r"\b(file|stream|io|serialization|deserialization|buffer)\b", "File I/O & Streams"),
		(r"\b(string|stringbuffer|stringbuilder|regex|character)\b", "String Manipulation"),
		(r"\b(recursion|pointer|dynamic memory|malloc|free|garbage collection)\b", "Memory Management & Pointers"),
		(r"\b(tree|graph|binary search|sorting|algorithm|complexity|big o|dijkstra)\b", "Data Structures & Algorithms"),
		(r"\b(network|tcp|udp|ip|osi model|socket|client|server|http)\b", "Computer Networks"),
		(r"\b(html|css|javascript|dom|frontend|react|vue|rest api|web)\b", "Web Technologies"),
		(r"\b(operating system|process|deadlock|scheduling|paging|virtual memory)\b", "Operating Systems"),
		(r"\b(security|cryptography|encryption|decryption|rsa|sha|firewall)\b", "Network Security"),
		(r"\b(testing|junit|unit test|integration test|debugging)\b", "Software Engineering & Testing"),
	]

	for pattern, topic_name in topic_rules:
		if re.search(pattern, clean):
			return topic_name

	# Fallback: Extract prominent nouns or return Subject Foundation
	words = [w for w in clean.split() if len(w) > 4 and w not in {
		"explain", "describe", "discuss", "between", "difference", "write", "program",
		"following", "example", "brief", "detail", "using", "state", "define"
	}]
	if words:
		return words[0].capitalize() + " Concepts"

	return subject or "General Concepts"


EXAM_STOP_WORDS = {
	"what", "is", "are", "explain", "describe", "discuss", "between", "difference",
	"write", "program", "following", "example", "brief", "detail", "using", "state",
	"define", "with", "suitable", "examples", "in", "the", "of", "and", "a", "an",
	"code", "to", "how", "short", "notes", "on", "types", "various"
}


def cluster_repeated_questions(all_questions: list[dict], similarity_threshold: int = 78) -> list[dict]:
	"""Cluster similar or identical questions appearing across different examination years.
	Identifies repeated questions, semantic variations, and their examination years.
	"""
	clusters = []
	assigned_indices = set()

	# Sort questions by length descending to use comprehensive wording as cluster representative
	indexed_questions = list(enumerate(all_questions))
	indexed_questions.sort(key=lambda item: len(item[1].get("question", "")), reverse=True)

	for i, q1 in indexed_questions:
		if i in assigned_indices:
			continue

		clean1 = clean_question_text(q1.get("question", ""))
		if len(clean1) < 8:
			continue

		tokens1 = {w for w in clean1.split() if len(w) > 3} - EXAM_STOP_WORDS

		cluster_members = [q1]
		assigned_indices.add(i)

		for j, q2 in indexed_questions:
			if j in assigned_indices:
				continue

			clean2 = clean_question_text(q2.get("question", ""))
			if len(clean2) < 8:
				continue

			# Calculate fuzzy similarity
			sim = fuzz.token_set_ratio(clean1, clean2)
			tokens2 = {w for w in clean2.split() if len(w) > 3} - EXAM_STOP_WORDS
			shared_concept = tokens1 & tokens2

			is_match = False
			if sim >= similarity_threshold:
				is_match = True
			elif shared_concept and sim >= 50:
				is_match = True
			elif q1.get("topic") and q1.get("topic") != "General" and q1.get("topic") == q2.get("topic") and shared_concept:
				is_match = True

			if is_match:
				cluster_members.append(q2)
				assigned_indices.add(j)

		# If question appeared more than once OR appeared in multiple distinct years
		years = sorted(list({str(m.get("examination_year")) for m in cluster_members if m.get("examination_year")}))
		if len(cluster_members) > 1 or len(years) > 1:
			clusters.append({
				"canonical_question": q1.get("question", ""),
				"topic": q1.get("topic", "General"),
				"frequency": len(cluster_members),
				"distinct_years_count": len(years),
				"examination_years": years,
				"marks_typical": q1.get("marks", 5),
				"type": q1.get("type", "Short Answer"),
				"variations": [
					{
						"question": m.get("question", ""),
						"year": m.get("examination_year", ""),
						"paper_title": m.get("paper_title", ""),
						"marks": m.get("marks", 1),
					}
					for m in cluster_members
				],
			})

	# Sort clusters by frequency descending, then distinct years descending
	clusters.sort(key=lambda c: (c["frequency"], c["distinct_years_count"]), reverse=True)
	return clusters


def analyze_course_previous_year_papers(
	course: str,
	subject: str | None = None,
	batch: str | None = None,
) -> dict:
	"""Collective historical AI analysis of ALL uploaded previous year examination papers for a Course.
	Analyzes patterns, repeated questions, topics importance, and distributions across all years.
	"""
	if not course:
		frappe.throw(_("Course is required for historical analysis."))

	filters = {"course": course}
	if subject and subject.strip():
		filters["subject"] = subject.strip()
	if batch and batch.strip():
		filters["batch"] = batch.strip()

	paper_records = frappe.get_all(
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
			"max_marks",
			"attachment",
			"ai_processing_status",
			"extracted_questions_count",
			"extracted_questions_json",
		],
		order_by="examination_year asc",
	)

	if not paper_records:
		frappe.throw(
			_("No uploaded question papers found for Course '{0}' (Subject: {1}). Please upload papers first.").format(
				course, subject or "All"
			)
		)

	# 1. Ensure all papers are processed
	all_extracted_questions = []
	processed_papers_count = 0
	course_chapters = get_course_chapters_and_topics(course)

	for paper in paper_records:
		questions_json = paper.get("extracted_questions_json")
		status = paper.get("ai_processing_status")

		if not questions_json or status != "Processed" or paper.get("extracted_questions_count", 0) == 0:
			# Auto process document
			proc_result = process_question_paper_document(paper.name)
			if proc_result.get("status") == "success":
				paper_doc = frappe.get_doc("Previous Year Question Papers", paper.name)
				questions_json = paper_doc.extracted_questions_json
				processed_papers_count += 1
		else:
			processed_papers_count += 1

		if questions_json:
			try:
				questions_list = json.loads(questions_json)
				for q in questions_list:
					q["paper_name"] = paper.name
					q["paper_title"] = paper.title
					q["examination_year"] = paper.examination_year or paper.academic_year
					q["course"] = paper.course
					q["subject"] = paper.subject
					q["difficulty"] = detect_question_difficulty(
						q.get("question", ""), q.get("marks", 1), q.get("type", "Short Answer")
					)
					q["topic"] = map_question_to_chapter_or_topic(
						q.get("question", ""), course_chapters, subject=paper.subject or ""
					)
					all_extracted_questions.append(q)
			except Exception as e:
				frappe.logger("ai_assessment").warning(f"Failed to parse questions json for {paper.name}: {e}")

	total_questions = len(all_extracted_questions)
	if total_questions == 0:
		frappe.throw(_("No questions could be extracted from the uploaded papers. Please verify document readability."))

	# 2. Extract examination years range
	years = sorted(list({cint(q.get("examination_year")) for q in all_extracted_questions if cint(q.get("examination_year")) > 1900}))
	year_range_str = f"{years[0]} - {years[-1]}" if years else "Multi-Year"

	# 3. Detect repeated questions across years
	repeated_clusters = cluster_repeated_questions(all_extracted_questions, similarity_threshold=78)
	total_repeated_count = sum(c["frequency"] for c in repeated_clusters)

	# 4. Compute Topic Importance and Chapter Frequency
	topic_counts = Counter()
	topic_marks = Counter()
	topic_years = defaultdict(set)

	for q in all_extracted_questions:
		t = q.get("topic") or "General"
		topic_counts[t] += 1
		topic_marks[t] += cint(q.get("marks", 1))
		if q.get("examination_year"):
			topic_years[t].add(str(q.get("examination_year")))

	# Categorize importance: High, Medium, Low & calculate Trend
	topic_importance_list = []
	sorted_topics = topic_counts.most_common()

	# Split years into older half and newer half for trend calculation
	mid_year = (years[0] + years[-1]) / 2 if len(years) > 1 else (years[0] if years else 2020)

	for topic_name, count in sorted_topics:
		pct = round((count / total_questions) * 100, 1)
		total_m = topic_marks[topic_name]

		if count >= 10 or pct >= 15.0:
			importance = "High"
		elif count >= 4 or pct >= 6.0:
			importance = "Medium"
		else:
			importance = "Low"

		# Trend analysis: compare appearances before mid_year vs after mid_year
		recent_count = sum(
			1 for q in all_extracted_questions
			if q.get("topic") == topic_name and cint(q.get("examination_year")) >= mid_year
		)
		older_count = count - recent_count

		if recent_count > older_count + 1:
			trend = "Increasing Frequency"
		elif older_count > recent_count + 1:
			trend = "Decreasing Frequency"
		else:
			trend = "Consistent"

		topic_importance_list.append({
			"topic": topic_name,
			"questions_count": count,
			"importance": importance,
			"percentage": pct,
			"total_marks": total_m,
			"distinct_years_count": len(topic_years[topic_name]),
			"years_appeared": sorted(list(topic_years[topic_name])),
			"trend": trend,
		})

	# 5. Year-wise question and marks distribution
	year_dist = defaultdict(lambda: {"questions_count": 0, "total_marks": 0})
	for q in all_extracted_questions:
		y = str(q.get("examination_year") or "Unknown")
		year_dist[y]["questions_count"] += 1
		year_dist[y]["total_marks"] += cint(q.get("marks", 1))

	# Format sorted by year
	year_distribution_sorted = [
		{"year": y, "questions_count": data["questions_count"], "total_marks": data["total_marks"]}
		for y, data in sorted(year_dist.items(), key=lambda item: item[0])
	]

	# 6. Marks distribution
	marks_dist = {"1 Mark": 0, "2 Marks": 0, "3-5 Marks": 0, "6-10 Marks": 0, "11+ Marks": 0}
	for q in all_extracted_questions:
		m = cint(q.get("marks", 1))
		if m <= 1:
			marks_dist["1 Mark"] += 1
		elif m == 2:
			marks_dist["2 Marks"] += 1
		elif 3 <= m <= 5:
			marks_dist["3-5 Marks"] += 1
		elif 6 <= m <= 10:
			marks_dist["6-10 Marks"] += 1
		else:
			marks_dist["11+ Marks"] += 1

	# 7. Difficulty distribution
	diff_counts = Counter(q.get("difficulty", "Medium") for q in all_extracted_questions)
	diff_dist = {
		"Easy": diff_counts.get("Easy", 0),
		"Medium": diff_counts.get("Medium", 0),
		"Hard": diff_counts.get("Hard", 0),
		"Easy_pct": round((diff_counts.get("Easy", 0) / total_questions) * 100, 1) if total_questions else 0,
		"Medium_pct": round((diff_counts.get("Medium", 0) / total_questions) * 100, 1) if total_questions else 0,
		"Hard_pct": round((diff_counts.get("Hard", 0) / total_questions) * 100, 1) if total_questions else 0,
	}

	# 8. Chapter Frequency
	chapter_counts = Counter(q.get("topic", "General") for q in all_extracted_questions)
	chapter_freq_list = [
		{"chapter": ch, "count": count, "percentage": round((count / total_questions) * 100, 1)}
		for ch, count in chapter_counts.most_common()
	]

	# 9. Frequently asked topics
	frequently_asked = [
		item for item in topic_importance_list if item["importance"] in ["High", "Medium"]
	]

	# 10. Persist or Update into Previous Year Paper Analysis DocType
	analysis_title = f"Historical Analysis: {subject or 'All Subjects'} - {course} ({year_range_str})"
	analysis_doc = None

	existing_analyses = frappe.get_all(
		"Previous Year Paper Analysis",
		filters={"course": course, "subject": subject or "All"},
		fields=["name"],
		order_by="creation desc",
		limit=1,
	)

	if existing_analyses:
		analysis_doc = frappe.get_doc("Previous Year Paper Analysis", existing_analyses[0].name)
	else:
		analysis_doc = frappe.new_doc("Previous Year Paper Analysis")
		analysis_doc.course = course
		analysis_doc.subject = subject or "All"
		analysis_doc.batch = batch

	analysis_doc.title = analysis_title
	analysis_doc.academic_years_covered = year_range_str
	analysis_doc.total_papers_analyzed = processed_papers_count
	analysis_doc.total_questions_extracted = total_questions
	analysis_doc.total_repeated_questions = total_repeated_count
	analysis_doc.status = "Completed"
	analysis_doc.analysis_date = now_datetime()
	analysis_doc.analyzed_by = frappe.session.user

	# Store serialized data
	analysis_doc.topic_importance_json = json.dumps(topic_importance_list, ensure_ascii=False)
	analysis_doc.repeated_questions_json = json.dumps(repeated_clusters, ensure_ascii=False)
	analysis_doc.year_distribution_json = json.dumps(year_distribution_sorted, ensure_ascii=False)
	analysis_doc.marks_distribution_json = json.dumps(marks_dist, ensure_ascii=False)
	analysis_doc.difficulty_distribution_json = json.dumps(diff_dist, ensure_ascii=False)
	analysis_doc.chapter_frequency_json = json.dumps(chapter_freq_list, ensure_ascii=False)
	analysis_doc.frequently_asked_topics_json = json.dumps(frequently_asked, ensure_ascii=False)
	analysis_doc.error_message = None

	analysis_doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"analysis_name": analysis_doc.name,
		"course": course,
		"subject": subject or "All",
		"batch": batch,
		"academic_years_covered": year_range_str,
		"total_uploaded_papers": len(paper_records),
		"total_processed_papers": processed_papers_count,
		"total_extracted_questions": total_questions,
		"total_repeated_questions": total_repeated_count,
		"topic_importance": topic_importance_list,
		"repeated_questions": repeated_clusters[:50],  # Top 50 clusters
		"year_distribution": year_distribution_sorted,
		"marks_distribution": marks_dist,
		"difficulty_distribution": diff_dist,
		"chapter_frequency": chapter_freq_list,
		"frequently_asked_topics": frequently_asked,
	}
