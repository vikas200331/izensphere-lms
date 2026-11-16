# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate
from lms.lms.ai.student_practice_api import (
	verify_student_course_enrollment,
	api_get_student_enrolled_courses,
	api_get_student_practice_questions,
	api_submit_student_practice_answer,
	api_ask_ai_question_help,
	api_generate_similar_practice_question,
	api_get_student_practice_history,
)


class TestStudentQuestionBankPractice(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")

		# Create Test Course 1 (Science)
		cls.sci_course = "class-10-science"
		if not frappe.db.exists("LMS Course", cls.sci_course):
			c1 = frappe.new_doc("LMS Course")
			c1.title = "Class 10 Science"
			c1.short_introduction = "Science course for Class 10"
			c1.description = "Complete Class 10 Science syllabus."
			c1.append("instructors", {"instructor": "Administrator"})
			c1.published = 1
			c1.save(ignore_permissions=True)
			cls.sci_course = c1.name

		# Create Test Course 2 (Mathematics)
		cls.math_course = "class-10-mathematics"
		if not frappe.db.exists("LMS Course", cls.math_course):
			c2 = frappe.new_doc("LMS Course")
			c2.title = "Class 10 Mathematics"
			c2.short_introduction = "Mathematics course for Class 10"
			c2.description = "Complete Class 10 Mathematics syllabus."
			c2.append("instructors", {"instructor": "Administrator"})
			c2.published = 1
			c2.save(ignore_permissions=True)
			cls.math_course = c2.name

		# Create Test Users: Student A (Science), Student B (Math), Student C (Dual)
		for email, first_name in [
			("student_sci@test.com", "Student Science"),
			("student_math@test.com", "Student Math"),
			("student_dual@test.com", "Student Dual"),
		]:
			if not frappe.db.exists("User", email):
				user = frappe.new_doc("User")
				user.email = email
				user.first_name = first_name
				user.send_welcome_email = 0
				user.save(ignore_permissions=True)

		# Enroll Student A in Science
		if not frappe.db.exists("LMS Enrollment", {"member": "student_sci@test.com", "course": cls.sci_course}):
			e1 = frappe.new_doc("LMS Enrollment")
			e1.member = "student_sci@test.com"
			e1.course = cls.sci_course
			e1.save(ignore_permissions=True)

		# Enroll Student B in Math
		if not frappe.db.exists("LMS Enrollment", {"member": "student_math@test.com", "course": cls.math_course}):
			e2 = frappe.new_doc("LMS Enrollment")
			e2.member = "student_math@test.com"
			e2.course = cls.math_course
			e2.save(ignore_permissions=True)

		# Enroll Student C in both Science & Math
		for crs in [cls.sci_course, cls.math_course]:
			if not frappe.db.exists("LMS Enrollment", {"member": "student_dual@test.com", "course": crs}):
				e3 = frappe.new_doc("LMS Enrollment")
				e3.member = "student_dual@test.com"
				e3.course = crs
				e3.save(ignore_permissions=True)

		# Create Sample Questions for Science: 1 Approved MCQ, 1 Draft MCQ
		from lms.lms.ai.question_bank import create_or_update_bank_question

		if not frappe.db.exists("LMS Question", {"course": cls.sci_course, "question": "What is Photosynthesis?"}):
			res1 = create_or_update_bank_question({
				"course": cls.sci_course,
				"question": "What is Photosynthesis?",
				"type": "Choices",
				"difficulty": "Easy",
				"marks": 1,
				"options": [
					"Process plants make food",
					"Process rocks form",
					"Water evaporation",
					"Animal respiration",
				],
				"correct_answer": "Process plants make food",
				"explanation": "Plants convert sunlight, carbon dioxide, and water into glucose and oxygen.",
				"approval_status": "Approved",
			})
			cls.sci_approved_q = res1["name"]
		else:
			cls.sci_approved_q = frappe.db.get_value("LMS Question", {"course": cls.sci_course, "question": "What is Photosynthesis?"}, "name")

		if not frappe.db.exists("LMS Question", {"course": cls.sci_course, "question": "What is cellular respiration?"}):
			res2 = create_or_update_bank_question({
				"course": cls.sci_course,
				"question": "What is cellular respiration?",
				"type": "Choices",
				"options": ["Breakdown of glucose", "Building of muscles"],
				"correct_answer": "Breakdown of glucose",
				"approval_status": "Draft",  # Unapproved!
			})
			cls.sci_draft_q = res2["name"]
		else:
			cls.sci_draft_q = frappe.db.get_value("LMS Question", {"course": cls.sci_course, "question": "What is cellular respiration?"}, "name")

		# Create Sample Question for Math: Approved MCQ
		if not frappe.db.exists("LMS Question", {"course": cls.math_course, "question": "What is 2 + 2?"}):
			res_m = create_or_update_bank_question({
				"course": cls.math_course,
				"question": "What is 2 + 2?",
				"type": "Choices",
				"marks": 1,
				"options": ["4", "3", "5"],
				"correct_answer": "4",
				"explanation": "2 + 2 equals 4 by basic arithmetic.",
				"approval_status": "Approved",
			})
			cls.math_approved_q = res_m["name"]
		else:
			cls.math_approved_q = frappe.db.get_value("LMS Question", {"course": cls.math_course, "question": "What is 2 + 2?"}, "name")

		frappe.db.commit()

	def test_01_student_science_can_access_science_course_and_questions(self):
		"""Student A enrolled in Science can fetch Science course and questions."""
		frappe.set_user("student_sci@test.com")
		courses_data = api_get_student_enrolled_courses()
		course_names = [c["name"] for c in courses_data["courses"]]
		self.assertIn(self.sci_course, course_names)
		self.assertNotIn(self.math_course, course_names)

		questions_res = api_get_student_practice_questions(self.sci_course)
		q_ids = [q["name"] for q in questions_res["questions"]]
		self.assertIn(self.sci_approved_q, q_ids)
		# Correct answers and explanation must be stripped for testing integrity
		for q in questions_res["questions"]:
			self.assertNotIn("correct_answer", q)
			self.assertNotIn("explanation", q)

	def test_02_student_science_cannot_access_mathematics_course(self):
		"""Student A enrolled in Science is blocked with PermissionError when requesting Math."""
		frappe.set_user("student_sci@test.com")
		with self.assertRaises(frappe.PermissionError):
			api_get_student_practice_questions(self.math_course)

	def test_03_student_math_can_access_mathematics_course_and_questions(self):
		"""Student B enrolled in Math can fetch Math course and questions, but not Science."""
		frappe.set_user("student_math@test.com")
		courses_data = api_get_student_enrolled_courses()
		course_names = [c["name"] for c in courses_data["courses"]]
		self.assertIn(self.math_course, course_names)
		self.assertNotIn(self.sci_course, course_names)

		with self.assertRaises(frappe.PermissionError):
			api_get_student_practice_questions(self.sci_course)

	def test_04_dual_enrolled_student_can_access_both_courses(self):
		"""Student C enrolled in both Science and Math can access both courses seamlessly."""
		frappe.set_user("student_dual@test.com")
		courses_data = api_get_student_enrolled_courses()
		course_names = [c["name"] for c in courses_data["courses"]]
		self.assertIn(self.sci_course, course_names)
		self.assertIn(self.math_course, course_names)

		# Access both
		sci_res = api_get_student_practice_questions(self.sci_course)
		math_res = api_get_student_practice_questions(self.math_course)
		self.assertTrue(sci_res["total_count"] >= 1)
		self.assertTrue(math_res["total_count"] >= 1)

	def test_05_unapproved_draft_questions_are_never_returned(self):
		"""Unapproved (Draft/Rejected) questions are filtered out at the database level."""
		frappe.set_user("student_sci@test.com")
		questions_res = api_get_student_practice_questions(self.sci_course)
		q_ids = [q["name"] for q in questions_res["questions"]]
		self.assertNotIn(self.sci_draft_q, q_ids)

	def test_06_direct_api_submission_security_validation(self):
		"""Submitting answer to unauthorized course is rejected even with valid question ID."""
		frappe.set_user("student_sci@test.com")
		# Student Sci tries to submit answer to Math question
		with self.assertRaises(frappe.PermissionError):
			api_submit_student_practice_answer(self.math_approved_q, "4", self.math_course)

	def test_07_interactive_practice_answer_submission_and_log(self):
		"""Student submits answer, gets evaluated, log is created, and explanation is revealed."""
		frappe.set_user("student_sci@test.com")
		res = api_submit_student_practice_answer(
			self.sci_approved_q,
			"Process plants make food",
			self.sci_course
		)
		self.assertTrue(res["is_correct"])
		self.assertEqual(res["marks_obtained"], 1.0)
		self.assertIn("sunlight", res["explanation"])

		# Verify log created
		log = frappe.db.get_value(
			"AI Question Practice Log",
			{"member": "student_sci@test.com", "question": self.sci_approved_q},
			["name", "is_correct"],
			as_dict=True,
		)
		self.assertIsNotNone(log)
		self.assertEqual(log.is_correct, 1)

	def test_08_practice_history_and_analytics(self):
		"""Student practice history calculates attempts, accuracy, and chapter mastery."""
		frappe.set_user("student_sci@test.com")
		history = api_get_student_practice_history(self.sci_course)
		self.assertTrue(history["total_attempted"] >= 1)
		self.assertTrue(history["total_correct"] >= 1)
		self.assertEqual(history["accuracy_percentage"], 100.0)

	def test_09_expired_course_blocks_student_access(self):
		"""Expired course enrollment revokes student question bank access."""
		frappe.set_user("Administrator")
		# Temporarily set expiry_date on test-science-course in past
		frappe.db.set_value("LMS Course", self.sci_course, "expiry_date", add_days(nowdate(), -10))
		frappe.db.commit()

		try:
			frappe.set_user("student_sci@test.com")
			with self.assertRaises(frappe.PermissionError):
				api_get_student_practice_questions(self.sci_course)
		finally:
			# Restore course expiry
			frappe.set_user("Administrator")
			frappe.db.set_value("LMS Course", self.sci_course, "expiry_date", None)
			frappe.db.commit()

	def test_10_teacher_retains_full_master_question_bank_access(self):
		"""Teachers and Admins retain full question bank management access."""
		frappe.set_user("Administrator")
		from lms.lms.ai.question_bank import search_question_bank
		res = search_question_bank(course=self.sci_course, approval_status="All")
		# Admin sees both approved and draft questions
		q_ids = [q["name"] for q in res["questions"]]
		self.assertIn(self.sci_approved_q, q_ids)
		self.assertIn(self.sci_draft_q, q_ids)
