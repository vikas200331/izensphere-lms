# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
from lms.lms.ai.document_extractor import parse_questions_from_text
from lms.lms.ai.historical_analyzer import (
	analyze_course_previous_year_papers,
	cluster_repeated_questions,
	clean_question_text,
)
from lms.lms.ai.historical_question_generator import generate_historical_ai_questions
from lms.lms.ai.historical_model_paper_builder import generate_historical_model_paper
from lms.lms.ai.previous_year_api import api_save_approved_questions_to_bank


class TestPreviousYearAI(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		# Create test course if not exists
		if not frappe.db.exists("LMS Course", "test-mca-course"):
			course = frappe.new_doc("LMS Course")
			course.title = "Test MCA Course"
			course.short_introduction = "Master of Computer Applications curriculum."
			course.description = "Advanced computer science, software engineering, and systems programming."
			course.append("instructors", {"instructor": "Administrator"})
			course.published = 1
			course.save(ignore_permissions=True)
			frappe.db.commit()
			cls.course_name = course.name
		else:
			cls.course_name = "test-mca-course"

	def test_01_parse_questions_from_text(self):
		sample_text = """
SECTION A
1. What is Encapsulation in Java? [2 Marks]
2. Which of the following is not a primitive data type? [1 Mark]
(a) int
(b) float
(c) String
(d) boolean
3. True or False: Multiple inheritance is supported in Java through interfaces. [1]

SECTION B
4. Explain the concept of Polymorphism with method overloading and overriding. [5 Marks]
5. Write a Java program to implement a thread using the Runnable interface. [5 Marks]

SECTION C
6. Discuss Exception Handling mechanism in Java with try, catch, finally, throw, and throws. [10 Marks]
"""
		meta = {
			"title": "MCA 2022 Java Programming",
			"examination_year": 2022,
			"course": self.course_name,
			"subject": "Java Programming",
		}
		questions = parse_questions_from_text(sample_text, meta)
		self.assertGreaterEqual(len(questions), 5)
		
		# Check MCQ parsing
		mcq = next((q for q in questions if q.get("type") == "Choices"), None)
		self.assertIsNotNone(mcq)
		self.assertGreaterEqual(len(mcq.get("options", [])), 4)

		# Check 10 marks question
		essay = next((q for q in questions if int(q.get("marks", 0)) == 10), None)
		self.assertIsNotNone(essay)
		self.assertIn("Exception Handling", essay.get("question"))

	def test_02_repeated_questions_clustering(self):
		q1 = {
			"question": "Explain the concept of Polymorphism with suitable examples.",
			"examination_year": 2018,
			"marks": 5,
			"type": "Short Answer",
			"paper_title": "2018 Java Paper",
		}
		q2 = {
			"question": "What is polymorphism in Java? Explain with examples.",
			"examination_year": 2021,
			"marks": 5,
			"type": "Short Answer",
			"paper_title": "2021 Java Paper",
		}
		q3 = {
			"question": "Discuss polymorphism in object oriented programming with code.",
			"examination_year": 2024,
			"marks": 6,
			"type": "Long Answer",
			"paper_title": "2024 Java Paper",
		}
		q4 = {
			"question": "What is binary search tree traversal?",
			"examination_year": 2024,
			"marks": 5,
			"type": "Short Answer",
			"paper_title": "2024 Java Paper",
		}

		clusters = cluster_repeated_questions([q1, q2, q3, q4], similarity_threshold=70)
		self.assertGreaterEqual(len(clusters), 1)
		poly_cluster = clusters[0]
		self.assertGreaterEqual(poly_cluster["frequency"], 3)
		self.assertIn("2018", poly_cluster["examination_years"])
		self.assertIn("2021", poly_cluster["examination_years"])
		self.assertIn("2024", poly_cluster["examination_years"])

	def test_03_collective_multi_year_analysis(self):
		years_data = [
			(2016, "1. What is an Abstract Class? [5]\n2. Explain Multithreading. [5]\n3. Define JVM. [2]"),
			(2018, "1. What is an Abstract Class vs Interface? [5]\n2. Explain Thread lifecycle. [5]\n3. What is Garbage Collection? [5]"),
			(2021, "1. Define Abstract Class in Java. [5]\n2. Explain Multithreading and Synchronization. [10]\n3. What is Exception Handling? [5]"),
			(2024, "1. Explain Abstract Class with code. [5]\n2. Discuss Multithreading in Java. [5]\n3. Explain Collections Framework ArrayList. [5]"),
		]

		for y, text in years_data:
			existing = frappe.get_all(
				"Previous Year Question Papers",
				filters={"course": self.course_name, "examination_year": y},
			)
			if not existing:
				p = frappe.new_doc("Previous Year Question Papers")
				p.title = f"MCA Java {y}"
				p.course = self.course_name
				p.subject = "Java Programming"
				p.examination_year = y
				p.attachment = "/files/dummy.pdf"
				p.ai_processing_status = "Processed"
				p.extracted_text = text
				qs = parse_questions_from_text(text, {"course": self.course_name, "subject": "Java Programming", "examination_year": y, "title": f"MCA Java {y}"})
				p.extracted_questions_json = json.dumps(qs)
				p.extracted_questions_count = len(qs)
				p.save(ignore_permissions=True)

		frappe.db.commit()

		# Run collective analysis across ALL years
		analysis = analyze_course_previous_year_papers(self.course_name, subject="Java Programming")
		self.assertGreaterEqual(analysis["total_uploaded_papers"], 4)
		self.assertGreaterEqual(analysis["total_extracted_questions"], 10)
		self.assertGreaterEqual(len(analysis["topic_importance"]), 1)
		self.assertIn("2016", analysis["academic_years_covered"])
		self.assertIn("2024", analysis["academic_years_covered"])

	def test_04_historical_ai_question_generation(self):
		gen = generate_historical_ai_questions(
			course=self.course_name,
			subject="Java Programming",
			number_of_questions=5,
			question_type="Mixed",
			difficulty="Medium",
		)
		self.assertEqual(gen["status"], "success")
		self.assertEqual(len(gen["questions"]), 5)
		for q in gen["questions"]:
			self.assertTrue(len(q["question"]) > 10)
			self.assertIn("historical_reference", q)

	def test_05_save_approved_questions_to_question_bank(self):
		approved_questions = [
			{
				"question": "What is the primary difference between ArrayList and LinkedList in Java?",
				"type": "Choices",
				"options": ["ArrayList is index-based, LinkedList is node-based", "LinkedList is contiguous", "ArrayList cannot store objects", "LinkedList does not allow duplicates"],
				"correct_answer": "ArrayList is index-based, LinkedList is node-based",
				"marks": 2,
				"difficulty": "Medium",
				"chapter": "Collections",
				"explanation": "ArrayList uses a dynamic resizing array while LinkedList uses a doubly-linked list structure.",
			}
		]
		result = api_save_approved_questions_to_bank(approved_questions, course=self.course_name, subject="Java Programming")
		self.assertEqual(result["status"], "success")
		self.assertEqual(result["saved_count"], 1)

		# Verify saved in LMS Question table
		created_q = frappe.get_doc("LMS Question", result["question_names"][0])
		self.assertEqual(created_q.is_ai_generated, 1)
		self.assertEqual(created_q.source, "Course Content")
		self.assertEqual(created_q.course, self.course_name)

	def test_06_model_paper_builder_validation(self):
		# Test with 100 marks standard blueprint
		res = generate_historical_model_paper(
			title="MCA 2026 Model Examination",
			course=self.course_name,
			subject="Java Programming",
			total_marks=100,
			duration="3 Hours",
		)
		self.assertEqual(res["status"], "success")
		self.assertEqual(res["total_marks"], 100)
		
		# Verify AI Question Paper record created in Draft status
		paper_doc = frappe.get_doc("AI Question Paper", res["paper_name"])
		self.assertEqual(paper_doc.approval_status, "Draft")
		self.assertEqual(paper_doc.total_marks, 100)
		self.assertEqual(len(paper_doc.sections), 4)
