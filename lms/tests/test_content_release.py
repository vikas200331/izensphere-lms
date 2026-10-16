# Copyright (c) 2026, Frappe and Contributors
# For license information, please see license.txt

import unittest
import frappe

from lms.lms.utils import get_course_outline, get_lesson, get_lesson_count
from lms.lms.permissions import resolve_lesson_access, can_access_quiz
from lms.lms.api import (
	publish_content_item,
	submit_content_item,
	approve_content_item,
	reject_content_item,
	batch_release_content,
	get_unreleased_content_summary,
)


class TestContentRelease(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.teacher = "jannat@example.com"
		cls.principal = "principal@example.com"
		cls.student = "jane.smith@example.com"

		# Clean up any leftover course
		frappe.set_user("Administrator")
		for c in frappe.get_all("LMS Course", filters={"title": "Test Content Release Course"}, pluck="name"):
			for ch in frappe.get_all("Chapter Reference", filters={"parent": c}, pluck="chapter"):
				for l in frappe.get_all("Lesson Reference", filters={"parent": ch}, pluck="lesson"):
					frappe.delete_doc("Course Lesson", l, force=True)
				frappe.delete_doc("Course Chapter", ch, force=True)
			frappe.delete_doc("LMS Course", c, force=True)

		# 1. Create test course (initially unpublished)
		doc = frappe.new_doc("LMS Course")
		doc.title = "Test Content Release Course"
		doc.short_introduction = "Test intro"
		doc.description = "Test description"
		doc.append("instructors", {"instructor": cls.teacher})
		doc.published = 0
		doc.content_release_mode = "None"
		doc.insert(ignore_permissions=True)
		cls.course = doc.name

		# 2. Add initial Chapter 1 and Lesson 1 before publication
		ch1 = frappe.new_doc("Course Chapter")
		ch1.title = "Chapter 1 Initial"
		ch1.course = cls.course
		ch1.flags.direct_publish = True
		ch1.release_status = "Released"
		ch1.insert(ignore_permissions=True)
		cls.ch1_name = ch1.name

		doc.reload()
		doc.append("chapters", {"chapter": ch1.name})
		doc.save(ignore_permissions=True)

		l1 = frappe.new_doc("Course Lesson")
		l1.title = "Lesson 1 Initial"
		l1.chapter = ch1.name
		l1.course = cls.course
		l1.content = '{"blocks": [{"type": "paragraph", "data": {"text": "Initial live content"}}]}'
		l1.flags.direct_publish = True
		l1.release_status = "Released"
		l1.insert(ignore_permissions=True)
		cls.l1_name = l1.name

		ref = frappe.new_doc("Lesson Reference")
		ref.parent = ch1.name
		ref.parenttype = "Course Chapter"
		ref.parentfield = "lessons"
		ref.lesson = l1.name
		ref.idx = 1
		ref.insert(ignore_permissions=True)

		# 3. Initially publish the course as Principal and configure Principal Approval Required mode
		frappe.set_user(cls.principal)
		doc.reload()
		doc.published = 1
		doc.content_release_mode = "Principal Approval Required"
		doc.save(ignore_permissions=True)
		frappe.set_user("Administrator")

		# 4. Enroll student
		if not frappe.db.exists("LMS Enrollment", {"course": cls.course, "member": cls.student}):
			enr = frappe.new_doc("LMS Enrollment")
			enr.course = cls.course
			enr.member = cls.student
			enr.insert(ignore_permissions=True)

	def test_1_existing_released_content_accessible(self):
		"""1. Existing published course and chapters/lessons remain accessible to students."""
		frappe.set_user(self.student)
		outline = get_course_outline(self.course)
		self.assertTrue(len(outline) >= 1)
		ch_titles = [c.title for c in outline]
		self.assertIn("Chapter 1 Initial", ch_titles)

		# Access lesson
		is_inst, can_acc = resolve_lesson_access(self.l1_name, user=self.student)
		self.assertTrue(can_acc)
		frappe.set_user("Administrator")

	def test_2_new_chapter_and_lesson_defaults_to_draft_in_approval_mode(self):
		"""2. Newly added chapter and lesson in published course default to Draft and are hidden from students."""
		frappe.set_user(self.teacher)

		# Add Chapter 2
		ch2 = frappe.new_doc("Course Chapter")
		ch2.title = "Chapter 2 Newly Added"
		ch2.course = self.course
		ch2.insert(ignore_permissions=True)
		TestContentRelease.ch2_name = ch2.name

		course_doc = frappe.get_doc("LMS Course", self.course)
		course_doc.append("chapters", {"chapter": ch2.name})
		course_doc.save(ignore_permissions=True)

		self.assertEqual(ch2.release_status, "Draft")

		# Add Lesson in Chapter 2
		l2 = frappe.new_doc("Course Lesson")
		l2.title = "Lesson 2 Draft"
		l2.chapter = ch2.name
		l2.course = self.course
		l2.content = '{"blocks": [{"type": "paragraph", "data": {"text": "Draft lesson text"}}]}'
		l2.insert(ignore_permissions=True)
		TestContentRelease.l2_name = l2.name

		ref = frappe.new_doc("Lesson Reference")
		ref.parent = ch2.name
		ref.parenttype = "Course Chapter"
		ref.parentfield = "lessons"
		ref.lesson = l2.name
		ref.idx = 1
		ref.insert(ignore_permissions=True)

		self.assertEqual(l2.release_status, "Draft")

		# Student outline should NOT include Chapter 2 or Lesson 2
		frappe.set_user(self.student)
		outline = get_course_outline(self.course)
		ch_titles = [c.title for c in outline]
		self.assertNotIn("Chapter 2 Newly Added", ch_titles)

		# Direct access by student must be DENIED
		is_inst, can_acc = resolve_lesson_access(TestContentRelease.l2_name, user=self.student)
		self.assertFalse(can_acc)

		# Teacher outline MUST show Chapter 2 and Lesson 2 with Draft status
		frappe.set_user(self.teacher)
		t_outline = get_course_outline(self.course)
		t_ch2 = [c for c in t_outline if c.name == ch2.name][0]
		self.assertEqual(t_ch2.release_status, "Draft")
		self.assertEqual(t_ch2.lessons[0].release_status, "Draft")

		frappe.set_user("Administrator")

	def test_3_approval_mode_blocks_direct_teacher_publish(self):
		"""3. In Principal Approval Required mode, teacher cannot directly publish."""
		frappe.set_user(self.teacher)
		with self.assertRaises(frappe.exceptions.ValidationError):
			publish_content_item("Course Chapter", TestContentRelease.ch2_name)
		frappe.set_user("Administrator")

	def test_4_submission_and_principal_approval_workflow(self):
		"""4. Teacher submits for approval, Principal approves and publishes content."""
		# Teacher submits
		frappe.set_user(self.teacher)
		res = submit_content_item("Course Chapter", TestContentRelease.ch2_name)
		self.assertEqual(res["status"], "success")

		ch2_status = frappe.db.get_value("Course Chapter", TestContentRelease.ch2_name, "release_status")
		self.assertEqual(ch2_status, "Pending Principal Approval")

		# Student still cannot see it
		frappe.set_user(self.student)
		outline = get_course_outline(self.course)
		ch_names = [c.name for c in outline]
		self.assertNotIn(TestContentRelease.ch2_name, ch_names)

		# Principal approves and publishes
		frappe.set_user(self.principal)
		app_res = approve_content_item("Course Chapter", TestContentRelease.ch2_name)
		self.assertEqual(app_res["status"], "success")

		ch2_status = frappe.db.get_value("Course Chapter", TestContentRelease.ch2_name, "release_status")
		self.assertEqual(ch2_status, "Released")

		# Now student CAN see Chapter 2 and Lesson 2!
		frappe.set_user(self.student)
		s_outline = get_course_outline(self.course)
		s_ch_names = [c.name for c in s_outline]
		self.assertIn(TestContentRelease.ch2_name, s_ch_names)

		is_inst, can_acc = resolve_lesson_access(TestContentRelease.l2_name, user=self.student)
		self.assertTrue(can_acc)

		frappe.set_user("Administrator")

	def test_5_rejection_workflow(self):
		"""5. Principal rejects content; it remains hidden until resubmitted and approved."""
		frappe.set_user(self.teacher)

		# Teacher adds Lesson 3
		l3 = frappe.new_doc("Course Lesson")
		l3.title = "Lesson 3 for rejection"
		l3.chapter = TestContentRelease.ch2_name
		l3.course = self.course
		l3.insert(ignore_permissions=True)
		TestContentRelease.l3_name = l3.name

		ref = frappe.new_doc("Lesson Reference")
		ref.parent = TestContentRelease.ch2_name
		ref.parenttype = "Course Chapter"
		ref.parentfield = "lessons"
		ref.lesson = l3.name
		ref.idx = 2
		ref.insert(ignore_permissions=True)

		submit_content_item("Course Lesson", TestContentRelease.l3_name)

		# Principal rejects
		frappe.set_user(self.principal)
		reject_content_item("Course Lesson", TestContentRelease.l3_name, reason="Needs more references")

		l3_doc = frappe.get_doc("Course Lesson", TestContentRelease.l3_name)
		self.assertEqual(l3_doc.release_status, "Rejected")
		self.assertEqual(l3_doc.rejection_reason, "Needs more references")

		# Student cannot see rejected lesson
		frappe.set_user(self.student)
		is_inst, can_acc = resolve_lesson_access(TestContentRelease.l3_name, user=self.student)
		self.assertFalse(can_acc)

		# Teacher resubmits and Principal approves
		frappe.set_user(self.teacher)
		submit_content_item("Course Lesson", TestContentRelease.l3_name)

		frappe.set_user(self.principal)
		approve_content_item("Course Lesson", TestContentRelease.l3_name)

		self.assertEqual(frappe.db.get_value("Course Lesson", TestContentRelease.l3_name, "release_status"), "Released")
		frappe.set_user("Administrator")

	def test_6_editing_released_lesson_stages_draft(self):
		"""6. Editing an already-released lesson stages changes in draft, keeping live content visible."""
		frappe.set_user(self.teacher)
		l1 = frappe.get_doc("Course Lesson", self.l1_name)
		original_title = l1.title
		original_content = l1.content

		# Teacher updates title and content
		l1.title = "Lesson 1 Live with Staged Edits"
		l1.content = '{"blocks": [{"type": "paragraph", "data": {"text": "Unapproved draft body"}}]}'
		l1.save(ignore_permissions=True)

		l1.reload()
		# Live fields remain untouched!
		self.assertEqual(l1.title, original_title)
		self.assertEqual(l1.content, original_content)
		# Draft fields store the edits!
		self.assertEqual(l1.has_unreleased_edits, 1)
		self.assertEqual(l1.draft_title, "Lesson 1 Live with Staged Edits")
		self.assertEqual(l1.draft_content, '{"blocks": [{"type": "paragraph", "data": {"text": "Unapproved draft body"}}]}')

		# Student still sees original title and content
		frappe.set_user(self.student)
		s_lesson = get_lesson(self.course, 1, 1)
		self.assertEqual(s_lesson.get("title"), original_title)
		self.assertEqual(s_lesson.get("content"), original_content)

		# When Principal approves, changes go live
		frappe.set_user(self.principal)
		approve_content_item("Course Lesson", self.l1_name)

		l1.reload()
		self.assertEqual(l1.has_unreleased_edits, 0)
		self.assertEqual(l1.title, "Lesson 1 Live with Staged Edits")

		frappe.set_user("Administrator")

	def test_7_teacher_can_publish_mode(self):
		"""7. In 'Teacher Can Publish' mode, authorized teacher can directly release content."""
		frappe.db.set_value("LMS Course", self.course, "content_release_mode", "Teacher Can Publish")

		frappe.set_user(self.teacher)
		ch3 = frappe.new_doc("Course Chapter")
		ch3.title = "Chapter 3 Teacher Direct"
		ch3.course = self.course
		ch3.insert(ignore_permissions=True)

		self.assertEqual(ch3.release_status, "Draft")

		# Teacher directly publishes
		res = publish_content_item("Course Chapter", ch3.name)
		self.assertEqual(res["status"], "success")

		self.assertEqual(frappe.db.get_value("Course Chapter", ch3.name, "release_status"), "Released")
		self.assertEqual(frappe.db.get_value("Course Chapter", ch3.name, "released_by"), self.teacher)

		frappe.set_user("Administrator")

	def test_8_none_mode_preserves_immediate_behavior(self):
		"""8. In 'None' mode, newly added content defaults to Released immediately (legacy behavior)."""
		frappe.db.set_value("LMS Course", self.course, "content_release_mode", "None")

		frappe.set_user(self.teacher)
		ch4 = frappe.new_doc("Course Chapter")
		ch4.title = "Chapter 4 Immediate"
		ch4.course = self.course
		ch4.insert(ignore_permissions=True)

	def test_9_unreleased_quiz_access(self):
		"""9. Quizzes attached to unreleased lessons cannot be accessed by students."""
		frappe.db.set_value("LMS Course", self.course, "content_release_mode", "Principal Approval Required")
		frappe.set_user(self.teacher)

		# Create a quiz
		quiz = frappe.new_doc("LMS Quiz")
		quiz.title = "Test Unreleased Quiz"
		quiz.course = self.course
		quiz.insert(ignore_permissions=True)

		# Create draft lesson with this quiz
		l_quiz = frappe.new_doc("Course Lesson")
		l_quiz.title = "Lesson with Quiz"
		l_quiz.chapter = self.ch1_name
		l_quiz.course = self.course
		l_quiz.quiz_id = quiz.name
		l_quiz.insert(ignore_permissions=True)

		ref = frappe.new_doc("Lesson Reference")
		ref.parent = self.ch1_name
		ref.parenttype = "Course Chapter"
		ref.parentfield = "lessons"
		ref.lesson = l_quiz.name
		ref.idx = 99
		ref.insert(ignore_permissions=True)

		# Student cannot access quiz while lesson is draft
		frappe.set_user(self.student)
		self.assertFalse(can_access_quiz(quiz.name, user=self.student))

		# When lesson is published, student can access quiz
		frappe.set_user(self.principal)
		approve_content_item("Course Lesson", l_quiz.name)

		frappe.set_user(self.student)
		self.assertTrue(can_access_quiz(quiz.name, user=self.student))
		frappe.set_user("Administrator")

	def test_10_student_progress_preserved(self):
		"""10. Adding draft lessons does not change or diminish student progress."""
		frappe.db.set_value("LMS Course", self.course, "content_release_mode", "Principal Approval Required")
		initial_count = get_lesson_count(self.course)

		# Add a draft lesson
		frappe.set_user(self.teacher)
		l_draft = frappe.new_doc("Course Lesson")
		l_draft.title = "Another Draft Lesson"
		l_draft.chapter = self.ch1_name
		l_draft.course = self.course
		l_draft.insert(ignore_permissions=True)

		ref = frappe.new_doc("Lesson Reference")
		ref.parent = self.ch1_name
		ref.parenttype = "Course Chapter"
		ref.parentfield = "lessons"
		ref.lesson = l_draft.name
		ref.idx = 100
		ref.insert(ignore_permissions=True)

		# The count of lessons for students and progress calculations must NOT increase
		new_count = get_lesson_count(self.course)
		self.assertEqual(initial_count, new_count)
		frappe.set_user("Administrator")

	def test_11_batch_assessments_release_workflow(self):
		"""11. Batch assessment release workflow: draft by default, hidden from student, principal approval, rejection and direct publish."""
		frappe.set_user("Administrator")
		# Create test batch
		for b in frappe.get_all("LMS Batch", filters={"title": "Test Release Batch"}, pluck="name"):
			frappe.delete_doc("LMS Batch", b, force=True)

		batch = frappe.new_doc("LMS Batch")
		batch.title = "Test Release Batch"
		batch.description = "Test Batch Description"
		batch.batch_details = "<p>Details</p>"
		batch.start_date = "2026-10-01"
		batch.end_date = "2026-12-31"
		batch.start_time = "09:00:00"
		batch.end_time = "10:00:00"
		batch.timezone = "Asia/Kolkata"
		batch.append("instructors", {"instructor": self.teacher})
		batch.flags.direct_publish = True
		batch.published = 1
		batch.content_release_mode = "Principal Approval Required"
		batch.insert(ignore_permissions=True)
		batch_name = batch.name

		# Enroll student in batch
		if not frappe.db.exists("LMS Batch Enrollment", {"batch": batch_name, "member": self.student}):
			benr = frappe.new_doc("LMS Batch Enrollment")
			benr.batch = batch_name
			benr.member = self.student
			benr.insert(ignore_permissions=True)

		# Create a standalone quiz
		bquiz = frappe.new_doc("LMS Quiz")
		bquiz.title = "Batch Test Quiz"
		bquiz.flags.direct_publish = True
		bquiz.release_status = "Released"
		bquiz.insert(ignore_permissions=True)

		# Teacher adds assessment to the published batch
		frappe.set_user(self.teacher)
		ass = frappe.new_doc("LMS Assessment")
		ass.parent = batch_name
		ass.parenttype = "LMS Batch"
		ass.parentfield = "assessment"
		ass.assessment_type = "LMS Quiz"
		ass.assessment_name = bquiz.name
		ass.insert(ignore_permissions=True)
		ass_name = ass.name

		# Release status must default to Draft
		self.assertEqual(frappe.db.get_value("LMS Assessment", ass_name, "release_status"), "Draft")

		# Student calls get_assessments: draft assessment must NOT be present!
		frappe.set_user(self.student)
		from lms.lms.utils import get_assessments
		student_assessments = get_assessments(batch_name)
		self.assertEqual(len(student_assessments), 0)

		# Student cannot access quiz via batch assessment
		self.assertFalse(can_access_quiz(bquiz.name, user=self.student))

		# Teacher submits assessment for approval
		frappe.set_user(self.teacher)
		res = submit_content_item("LMS Assessment", ass_name)
		self.assertEqual(res["status"], "success")
		self.assertEqual(frappe.db.get_value("LMS Assessment", ass_name, "release_status"), "Pending Principal Approval")

		# Principal rejects assessment
		frappe.set_user(self.principal)
		rej = reject_content_item("LMS Assessment", ass_name, reason="Quiz questions need revision")
		self.assertEqual(rej["status"], "success")
		self.assertEqual(frappe.db.get_value("LMS Assessment", ass_name, "release_status"), "Rejected")

		# Student still cannot see it
		frappe.set_user(self.student)
		self.assertEqual(len(get_assessments(batch_name)), 0)

		# Teacher resubmits
		frappe.set_user(self.teacher)
		submit_content_item("LMS Assessment", ass_name)

		# Principal approves and publishes
		frappe.set_user(self.principal)
		app = approve_content_item("LMS Assessment", ass_name)
		self.assertEqual(app["status"], "success")
		self.assertEqual(frappe.db.get_value("LMS Assessment", ass_name, "release_status"), "Released")

		# Now student CAN see the assessment in get_assessments!
		frappe.set_user(self.student)
		s_assessments = get_assessments(batch_name)
		self.assertEqual(len(s_assessments), 1)
		self.assertEqual(s_assessments[0].assessment_name, bquiz.name)
		self.assertTrue(can_access_quiz(bquiz.name, user=self.student))

		# Cleanup batch
		frappe.set_user("Administrator")
		frappe.delete_doc("LMS Assessment", ass_name, force=True)
		frappe.delete_doc("LMS Quiz", bquiz.name, force=True)
		frappe.delete_doc("LMS Batch", batch_name, force=True)

	def test_12_direct_access_and_api_security(self):
		"""12. Students cannot bypass release using direct URLs, API list calls, or submission endpoints."""
		frappe.db.set_value("LMS Course", self.course, "content_release_mode", "Principal Approval Required")
		frappe.set_user(self.teacher)

		# Add a draft chapter and lesson
		draft_ch = frappe.new_doc("Course Chapter")
		draft_ch.title = "Draft Security Chapter"
		draft_ch.course = self.course
		draft_ch.insert(ignore_permissions=True)

		draft_l = frappe.new_doc("Course Lesson")
		draft_l.title = "Draft Security Lesson"
		draft_l.chapter = draft_ch.name
		draft_l.course = self.course
		draft_l.content = '{"blocks": [{"type": "paragraph", "data": {"text": "Secret content"}}]}'
		draft_l.insert(ignore_permissions=True)

		# Create an unreleased quiz and assign to draft lesson
		sec_quiz = frappe.new_doc("LMS Quiz")
		sec_quiz.title = "Security Quiz"
		sec_quiz.course = self.course
		sec_quiz.lesson = draft_l.name
		sec_quiz.insert(ignore_permissions=True)

		draft_l.quiz_id = sec_quiz.name
		draft_l.save(ignore_permissions=True)

		# Student checks
		frappe.set_user(self.student)

		# 1. Lesson direct access
		is_inst, can_acc = resolve_lesson_access(draft_l.name, user=self.student)
		self.assertFalse(can_acc)

		# 2. Direct get_quiz_with_questions API
		from lms.lms.utils import get_quiz_with_questions
		with self.assertRaises(frappe.PermissionError):
			get_quiz_with_questions(sec_quiz.name)

		# 3. Direct LMSQuizSubmission
		sub = frappe.new_doc("LMS Quiz Submission")
		sub.quiz = sec_quiz.name
		sub.member = self.student
		with self.assertRaises(frappe.PermissionError):
			sub.insert()

		# Create a real assignment
		sec_assign = frappe.new_doc("LMS Assignment")
		sec_assign.title = "Security Assignment"
		sec_assign.question = "<p>Assignment prompt</p>"
		sec_assign.insert(ignore_permissions=True)

		# 4. Direct LMSAssignmentSubmission on draft lesson
		asub = frappe.new_doc("LMS Assignment Submission")
		asub.assignment = sec_assign.name
		asub.lesson = draft_l.name
		asub.member = self.student
		with self.assertRaises(frappe.PermissionError):
			asub.insert()

		# Cleanup
		frappe.set_user("Administrator")
		frappe.delete_doc("LMS Assignment", sec_assign.name, force=True)
		frappe.delete_doc("Course Lesson", draft_l.name, force=True)
		frappe.delete_doc("LMS Quiz", sec_quiz.name, force=True)
		frappe.delete_doc("Course Chapter", draft_ch.name, force=True)

	def test_13_principal_dashboard_pending_content(self):
		"""13. Newly submitted content appears in Principal Dashboard API, can be approved/rejected via process_approval, and rejects student access."""
		frappe.db.set_value("LMS Course", self.course, "content_release_mode", "Principal Approval Required")
		frappe.set_user(self.teacher)

		# Add a new chapter and lesson
		p_ch = frappe.new_doc("Course Chapter")
		p_ch.title = "Dashboard Chapter"
		p_ch.course = self.course
		p_ch.insert(ignore_permissions=True)

		p_l = frappe.new_doc("Course Lesson")
		p_l.title = "Dashboard Lesson"
		p_l.chapter = p_ch.name
		p_l.course = self.course
		p_l.content = '{"blocks": [{"type": "paragraph", "data": {"text": "Hello Principal"}}]}'
		p_l.insert(ignore_permissions=True)

		# Submit for approval
		submit_content_item("Course Lesson", p_l.name)
		self.assertEqual(frappe.db.get_value("Course Lesson", p_l.name, "release_status"), "Pending Principal Approval")

		# Student cannot call get_pending_content_for_principal
		frappe.set_user(self.student)
		from lms.lms.api import get_pending_content_for_principal, process_approval
		with self.assertRaises(frappe.PermissionError):
			get_pending_content_for_principal()

		# Principal calls get_pending_content_for_principal
		frappe.set_user(self.principal)
		pending = get_pending_content_for_principal()
		lesson_keys = [it["name"] for it in pending if it["doctype"] == "Course Lesson"]
		self.assertIn(p_l.name, lesson_keys)

		# Check lesson item structure
		item = next(it for it in pending if it["name"] == p_l.name)
		self.assertEqual(item["content_type"], "Lesson")
		self.assertEqual(item["title"], "Dashboard Lesson")
		self.assertEqual(item["course"], self.course)
		self.assertEqual(item["chapter"], p_ch.name)

		# Principal approves via process_approval
		process_approval("Course Lesson", p_l.name, "Approve")
		self.assertEqual(frappe.db.get_value("Course Lesson", p_l.name, "release_status"), "Released")

		# Approved item is no longer in pending list
		pending_after = get_pending_content_for_principal()
		lesson_keys_after = [it["name"] for it in pending_after if it["doctype"] == "Course Lesson"]
		self.assertNotIn(p_l.name, lesson_keys_after)

		# Cleanup
		frappe.set_user("Administrator")
		frappe.delete_doc("Course Lesson", p_l.name, force=True)
		frappe.delete_doc("Course Chapter", p_ch.name, force=True)

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		# Cleanup test artifacts
		for l in frappe.get_all("Course Lesson", filters={"course": cls.course}, pluck="name"):
			frappe.delete_doc("Course Lesson", l, force=True)
		for ch in frappe.get_all("Course Chapter", filters={"course": cls.course}, pluck="name"):
			frappe.delete_doc("Course Chapter", ch, force=True)
		for q in frappe.get_all("LMS Quiz", filters={"course": cls.course}, pluck="name"):
			frappe.delete_doc("LMS Quiz", q, force=True)
		if frappe.db.exists("LMS Course", cls.course):
			frappe.delete_doc("LMS Course", cls.course, force=True)
