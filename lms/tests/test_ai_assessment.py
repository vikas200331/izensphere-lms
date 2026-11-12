# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import unittest
import frappe
from frappe.tests.utils import FrappeTestCase

from lms.lms.ai.content_extractor import (
	extract_batch_content,
	extract_chapter_content,
	extract_course_content,
	extract_lesson_content,
	get_content_stats,
	parse_editorjs_json,
)
from lms.lms.ai.ai_service import (
	calculate_cost,
	get_ai_settings,
	get_openai_api_key,
	test_ai_connection,
)
from lms.lms.ai.quiz_generator import (
	generate_quiz,
	regenerate_single_question,
	save_ai_quiz_to_database,
)
from lms.lms.ai.question_paper_generator import (
	generate_question_paper,
	save_ai_question_paper,
	validate_paper_structure,
)
from lms.lms.ai.question_bank import (
	create_or_update_bank_question,
	detect_duplicate_question,
	search_question_bank,
)
from lms.lms.ai.pdf_generator import (
	generate_paper_pdf_file,
	get_paper_html,
)
from lms.lms.ai.analytics import get_quiz_assessment_report
from lms.lms.ai.ai_assessment_api import (
	api_save_ai_settings,
	api_test_ai_connection,
)


class TestAIAssessmentGenerator(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		# 1. Create or get test course
		if not frappe.db.exists("LMS Course", "test-ai-computer-science"):
			course = frappe.new_doc("LMS Course")
			course.title = "Test AI Computer Science"
			course.short_introduction = "A comprehensive introduction to computer science and programming."
			course.description = "Detailed curriculum exploring computer architecture, algorithms, and data structures."
			course.append("instructors", {"instructor": "Administrator"})
			course.insert(ignore_permissions=True)
		else:
			course = frappe.get_doc("LMS Course", "test-ai-computer-science")
		cls.test_course = course.name

		# 2. Create Chapter 1
		ch1 = frappe.new_doc("Course Chapter")
		ch1.title = "Test Architecture Chapter"
		ch1.course = cls.test_course
		ch1.insert(ignore_permissions=True)
		cls.test_chapter = ch1.name

		# Lesson 1 in Chapter 1
		l1 = frappe.new_doc("Course Lesson")
		l1.title = "Test Lesson on Architecture"
		l1.chapter = cls.test_chapter
		l1.course = cls.test_course
		editorjs_sample = {
			"time": 1700000000000,
			"blocks": [
				{"type": "header", "data": {"text": "Computer Architecture Fundamentals", "level": 2}},
				{"type": "paragraph", "data": {"text": "The Central Processing Unit (CPU) executes instructions stored in main memory. It contains the Arithmetic Logic Unit (ALU) and Control Unit."}},
				{"type": "list", "data": {"style": "unordered", "items": [{"content": "ALU performs arithmetic and logic"}, {"content": "Registers hold immediate data"}]}},
			],
		}
		l1.content = json.dumps(editorjs_sample)
		l1.body = "Additional notes on von Neumann architecture and memory hierarchies."
		l1.insert(ignore_permissions=True)
		cls.test_lesson = l1.name

		# 3. Create Chapter 2 (for multi-chapter tests)
		ch2 = frappe.new_doc("Course Chapter")
		ch2.title = "Test Algorithms and Complexity"
		ch2.course = cls.test_course
		ch2.insert(ignore_permissions=True)
		cls.test_chapter_2 = ch2.name

		l2 = frappe.new_doc("Course Lesson")
		l2.title = "Test Lesson on Sorting Algorithms"
		l2.chapter = cls.test_chapter_2
		l2.course = cls.test_course
		l2.body = "Sorting algorithms rearrange elements in a list. QuickSort uses divide and conquer with average O(n log n) time complexity. BubbleSort has O(n^2) worst case complexity."
		l2.insert(ignore_permissions=True)
		cls.test_lesson_2 = l2.name

		# 4. Create Batch linking test course
		if not frappe.db.exists("LMS Batch", "test-ai-batch-2026"):
			b = frappe.new_doc("LMS Batch")
			b.title = "Test AI Batch 2026"
			b.category = "Programming"
			b.start_date = "2026-08-01"
			b.end_date = "2026-11-01"
			b.start_time = "09:00:00"
			b.end_time = "17:00:00"
			b.timezone = "Asia/Kolkata"
			b.description = "A fast-track intensive 12-week batch on Computer Architecture and Algorithms."
			b.batch_details = "<p>Syllabus covers CPU Pipelines, Cache Memory, Sorting Analysis, and Practical Labs.</p>"
			b.append("instructors", {"instructor": "Administrator"})
			b.append("courses", {"course": cls.test_course, "title": "Test AI Computer Science"})
			b.insert(ignore_permissions=True)
			cls.test_batch = b.name
		else:
			cls.test_batch = "test-ai-batch-2026"

		frappe.db.commit()

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_ai_provider_connection_and_settings(self):
		"""Verify Ollama and OpenAI connection tests and configuration management."""
		# Test Ollama connection check
		ollama_check = test_ai_connection(provider="Ollama", base_url="http://localhost:11434")
		self.assertEqual(ollama_check["provider"], "Ollama")
		self.assertIn("message", ollama_check)

		# Test OpenAI connection check without key
		openai_check = test_ai_connection(provider="OpenAI", api_key="")
		self.assertEqual(openai_check["provider"], "OpenAI")
		self.assertFalse(openai_check["success"])
		self.assertIn("missing", openai_check["message"].lower())

		# Save provider settings via API
		save_res = api_save_ai_settings({
			"provider": "Ollama",
			"ollama_base_url": "http://localhost:11434",
			"ollama_model": "llama3.2",
			"temperature": 0.65,
			"max_tokens": 3500,
		})
		self.assertTrue(save_res["success"])
		cfg = get_ai_settings()
		self.assertEqual(cfg["provider"], "Ollama")
		self.assertEqual(cfg["temperature"], 0.65)

	def test_content_extraction_and_editorjs_parsing(self):
		"""Verify Editor.js JSON blocks and lesson notes are extracted into clean Markdown."""
		lesson_data = extract_lesson_content(self.test_lesson)
		self.assertFalse(lesson_data["insufficient"])
		self.assertIn("Computer Architecture Fundamentals", lesson_data["content"])
		self.assertIn("Arithmetic Logic Unit", lesson_data["content"])
		self.assertGreater(lesson_data["stats"]["word_count"], 15)

		# Chapter extraction
		chapter_data = extract_chapter_content(self.test_chapter)
		self.assertIn("Test Lesson on Architecture", chapter_data["content"])
		self.assertFalse(chapter_data["insufficient"])

	def test_insufficient_content_threshold(self):
		"""Verify warning is issued when content has fewer than 100 characters."""
		stats = get_content_stats("Short text.")
		self.assertTrue(stats["is_insufficient"])
		self.assertIsNotNone(stats["warning"])

		stats_sufficient = get_content_stats("A " * 60)
		self.assertFalse(stats_sufficient["is_insufficient"])
		self.assertIsNone(stats_sufficient["warning"])

	def test_quiz_generation_from_single_chapter_10_questions(self):
		"""Scenario 1: Generate a 10-question quiz from one chapter."""
		quiz_res = generate_quiz(
			chapter=self.test_chapter,
			difficulty="Medium",
			num_questions=10,
			total_marks=10,
			mode="Chapter-Based",
		)
		self.assertGreaterEqual(len(quiz_res["questions"]), 4)
		self.assertGreater(quiz_res["total_marks"], 0)

		for q in quiz_res["questions"]:
			self.assertIn(q["type"], ["Choices", "User Input", "Open Ended"])
			self.assertIsNotNone(q.get("explanation"))
			self.assertEqual(q["source"], "Course Content")

	def test_quiz_generation_from_multiple_chapters_20_questions(self):
		"""Scenario 2: Generate a 20-question quiz across multiple chapters."""
		quiz_res = generate_quiz(
			course=self.test_course,
			difficulty="Mixed",
			num_questions=20,
			total_marks=20,
			mode="Chapter-Based",
		)
		self.assertGreater(len(quiz_res["questions"]), 0)
		self.assertGreater(quiz_res["total_marks"], 0)

	def test_single_question_regeneration(self):
		"""Verify regenerating a single question returns an updated question without resetting the quiz."""
		original = {
			"question": "Which component performs calculations in a CPU?",
			"type": "Choices",
			"question_type_label": "MCQ",
			"options": ["ALU", "SSD", "RAM", "GPU"],
			"correct_answer": "ALU",
			"marks": 1,
			"difficulty": "Easy",
		}
		regenerated = regenerate_single_question(
			original,
			chapter=self.test_chapter,
			mode="Chapter-Based",
			target_difficulty="Hard",
		)
		self.assertIsNotNone(regenerated["question"])
		self.assertEqual(regenerated["difficulty"], "Hard")

	def test_save_quiz_to_database_and_approval_workflow(self):
		"""Verify saving AI-generated questions into LMS Quiz and LMS Question records."""
		questions = [
			{
				"question": "What is the primary function of the ALU?",
				"type": "Choices",
				"options": ["Arithmetic & Logic operations", "Audio playback", "Network routing", "Power cooling"],
				"correct_answer": "Arithmetic & Logic operations",
				"marks": 1,
				"difficulty": "Easy",
				"source": "Course Content",
				"explanation": "ALU handles math and logical decisions.",
			},
			{
				"question": "State True or False: Registers store immediate data.",
				"type": "Choices",
				"options": ["True", "False"],
				"correct_answer": "True",
				"marks": 1,
				"difficulty": "Easy",
				"source": "Course Content",
				"explanation": "Registers are CPU internal storage.",
			},
		]

		saved = save_ai_quiz_to_database(
			quiz_title="Unit Test: CPU Architecture",
			questions=questions,
			course=self.test_course,
			chapter=self.test_chapter,
			action="Submitted for Approval",
		)

		self.assertTrue(frappe.db.exists("LMS Quiz", saved["quiz_name"]))
		quiz_doc = frappe.get_doc("LMS Quiz", saved["quiz_name"])
		self.assertEqual(quiz_doc.release_status, "Pending Principal Approval")
		self.assertEqual(len(quiz_doc.questions), 2)
		self.assertEqual(quiz_doc.total_marks, 2)

		# Principal approval action
		from lms.lms.ai.ai_assessment_api import api_approve_assessment
		frappe.set_user("Administrator")
		approve_res = api_approve_assessment("LMS Quiz", quiz_doc.name)
		self.assertEqual(approve_res["release_status"], "Released")

	def test_complete_model_paper_for_100_marks_with_5_sections(self):
		"""Scenario 3: Generate a complete model question paper for 100 marks across 5 sections."""
		paper = generate_question_paper(
			academic_year="2026-27",
			class_level="Class 10",
			subject="Computer Science",
			examination_type="Annual Examination",
			selected_chapters=[self.test_chapter, self.test_chapter_2],
			total_marks=100,
			mode="Chapter-Based",
		)
		self.assertTrue(paper["validation"]["is_valid"])
		self.assertEqual(paper["total_marks"], 100)
		self.assertEqual(paper["validation"]["calculated_total_marks"], 100)
		self.assertEqual(len(paper["sections"]), 5)

		# Verify all 5 section names: Section A through Section E
		section_names = [s["section_name"] for s in paper["sections"]]
		self.assertEqual(section_names, ["Section A", "Section B", "Section C", "Section D", "Section E"])

		# Save valid 100 marks paper
		saved = save_ai_question_paper(paper, action="Draft")
		self.assertTrue(frappe.db.exists("AI Question Paper", saved["name"]))

	def test_question_paper_generation_and_strict_marks_validation(self):
		"""Verify Question Paper generation, section calculation, and marks validation."""
		paper = generate_question_paper(
			academic_year="2026-27",
			class_level="Class 10",
			subject="Computer Science",
			examination_type="Midterm Examination",
			selected_chapters=[self.test_chapter],
			total_marks=20,
			mode="Chapter-Based",
		)
		self.assertTrue(paper["validation"]["is_valid"])
		self.assertEqual(paper["validation"]["calculated_total_marks"], 20)

		# Save valid paper
		saved = save_ai_question_paper(paper, action="Draft")
		self.assertTrue(frappe.db.exists("AI Question Paper", saved["name"]))

		# Test failure on invalid marks
		invalid_paper = dict(paper)
		invalid_paper["total_marks"] = 99  # Mismatch against section sum (20)
		with self.assertRaises(frappe.ValidationError):
			save_ai_question_paper(invalid_paper, action="Draft")

	def test_question_paper_generation_based_on_course_and_batch_content(self):
		"""Verify Question Paper generation based on both Course and Batch content."""
		# 1. Test batch content extraction
		batch_data = extract_batch_content(self.test_batch, course_name=self.test_course)
		self.assertFalse(batch_data["insufficient"])
		self.assertIn("Test AI Batch 2026", batch_data["content"])
		self.assertIn("Test AI Computer Science", batch_data["content"])
		self.assertIn("Computer Architecture Fundamentals", batch_data["content"])

		# 2. Test Question Paper Generation with batch and course
		paper = generate_question_paper(
			academic_year="2026-27",
			class_level="Test AI Batch 2026",
			subject="Computer Science",
			examination_type="Midterm Examination",
			batch=self.test_batch,
			course=self.test_course,
			total_marks=50,
			mode="Chapter-Based",
		)
		self.assertTrue(paper["validation"]["is_valid"])
		self.assertEqual(paper["total_marks"], 50)
		self.assertEqual(paper["validation"]["calculated_total_marks"], 50)
		self.assertEqual(paper.get("batch"), self.test_batch)
		self.assertEqual(paper.get("course"), self.test_course)

		# 3. Save Question Paper and verify persistence of batch link in database
		saved = save_ai_question_paper(paper, action="Draft")
		self.assertTrue(frappe.db.exists("AI Question Paper", saved["name"]))
		saved_doc = frappe.get_doc("AI Question Paper", saved["name"])
		self.assertEqual(saved_doc.batch, self.test_batch)
		self.assertEqual(saved_doc.course, self.test_course)
		self.assertEqual(saved_doc.total_marks, 50)

	def test_question_paper_pdf_generation_and_student_restriction(self):
		"""Verify Question Paper, Answer Key, and Solutions PDFs are generated, and students are restricted."""
		paper = generate_question_paper(
			subject="Science",
			selected_chapters=[self.test_chapter],
			total_marks=20,
		)
		saved = save_ai_question_paper(paper, action="Draft")

		# Generate Question Paper PDF
		qp_pdf = generate_paper_pdf_file(saved["name"], doc_type="question_paper")
		self.assertGreater(len(qp_pdf), 1000)

		# Generate Answer Key & Solutions
		ans_pdf = generate_paper_pdf_file(saved["name"], doc_type="answer_key")
		self.assertGreater(len(ans_pdf), 1000)

		# Test student security restriction
		if not frappe.db.exists("User", "test_student@example.com"):
			student = frappe.new_doc("User")
			student.email = "test_student@example.com"
			student.first_name = "Test Student"
			student.add_roles("LMS Student")
			student.insert(ignore_permissions=True)

		frappe.set_user("test_student@example.com")
		with self.assertRaises(frappe.PermissionError):
			get_paper_html(saved["name"], doc_type="answer_key")

	def test_question_bank_and_duplicate_detection(self):
		"""Verify storing in Question Bank, filtering, and detecting duplicates."""
		frappe.set_user("Administrator")
		q1 = {
			"question": "What does ALU stand for in computing systems?",
			"type": "Choices",
			"difficulty": "Easy",
			"marks": 1,
			"options": ["Arithmetic Logic Unit", "Array Line Utility", "Async Logic User", "Audio Level Unit"],
			"correct_answer": "Arithmetic Logic Unit",
			"course": self.test_course,
			"explanation": "Arithmetic Logic Unit.",
		}
		res1 = create_or_update_bank_question(q1)
		self.assertTrue(frappe.db.exists("LMS Question", res1["name"]))

		# Duplicate detection
		dup_check = detect_duplicate_question("What does ALU stand for in computing systems?")
		self.assertTrue(dup_check["is_duplicate"])
		self.assertGreaterEqual(dup_check["similarity"], 85)

		# Search question bank
		bank_res = search_question_bank(course=self.test_course, search_query="ALU")
		self.assertGreaterEqual(bank_res["total_count"], 1)

	def test_analytics_and_recommendations(self):
		"""Verify quiz assessment reports, difficulty distribution, and pedagogical recommendations."""
		report = get_quiz_assessment_report("do-you-know-frappe-learning")
		self.assertIn("quiz_title", report)
		self.assertIn("recommendations", report)
		self.assertIsInstance(report["recommendations"], list)
