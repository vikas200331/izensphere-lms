# Copyright (c) 2021, FOSS United and Contributors
# See license.txt

import frappe
from frappe.utils import flt

from lms.lms.test_helpers import BaseTestUtils
from lms.lms.utils import get_course_details


class TestLMSCourseReview(BaseTestUtils):
	def setUp(self):
		super().setUp()
		self.admin = self._create_user(
			"frappe@example.com", "Frappe", "Admin", ["Moderator", "Course Creator", "Batch Evaluator"]
		)
		self.student1 = self._create_user("reviewstudent1@example.com", "Review", "Student1", ["LMS Student"])
		self.student2 = self._create_user("reviewstudent2@example.com", "Review", "Student2", ["LMS Student"])
		self.course = self._create_course(title="Rating Test Course")
		frappe.db.delete("LMS Course Review", {"course": self.course.name})
		frappe.db.delete("LMS Enrollment", {"course": self.course.name})
		frappe.db.set_value("LMS Course", self.course.name, "rating", 0)

	def tearDown(self):
		frappe.set_user("Administrator")
		if hasattr(self, "course"):
			frappe.db.delete("LMS Course Review", {"course": self.course.name})
			frappe.db.delete("LMS Enrollment", {"course": self.course.name})
		super().tearDown()

	def test_review_updates_course_rating_and_count(self):
		# Course initial rating should be 0
		initial_rating = flt(frappe.db.get_value("LMS Course", self.course.name, "rating") or 0)
		self.assertEqual(initial_rating, 0)

		# Enroll student 1
		self._create_enrollment(self.student1.email, self.course.name)

		# Submit 5-star review (stored as 1.0)
		frappe.set_user(self.student1.email)
		rev1 = frappe.new_doc("LMS Course Review")
		rev1.course = self.course.name
		rev1.rating = 1.0  # 5 stars (1.0 * 5 = 5.0)
		rev1.review = "Amazing course!"
		rev1.insert()
		self.cleanup_items.append(("LMS Course Review", rev1.name))

		# Course rating in DB must immediately be 5.0
		course_rating = flt(frappe.db.get_value("LMS Course", self.course.name, "rating"))
		self.assertEqual(course_rating, 5.0)

		# Enroll student 2 and submit 4-star review (0.8)
		self._create_enrollment(self.student2.email, self.course.name)
		frappe.set_user(self.student2.email)
		rev2 = frappe.new_doc("LMS Course Review")
		rev2.course = self.course.name
		rev2.rating = 0.8  # 4 stars (0.8 * 5 = 4.0)
		rev2.review = "Good content"
		rev2.insert()
		self.cleanup_items.append(("LMS Course Review", rev2.name))

		# Average rating in DB should be (5 + 4) / 2 = 4.5
		course_rating = flt(frappe.db.get_value("LMS Course", self.course.name, "rating"))
		self.assertEqual(course_rating, 4.5)

		# get_course_details must return live rating and count
		details = get_course_details(self.course.name)
		self.assertEqual(details.rating, 4.5)
		self.assertEqual(details.rating_count, 2)

		# Update rev2 from 4 stars to 5 stars
		rev2.reload()
		rev2.rating = 1.0
		rev2.save()

		# Rating should update to 5.0
		course_rating = flt(frappe.db.get_value("LMS Course", self.course.name, "rating"))
		self.assertEqual(course_rating, 5.0)

		# Delete rev2 as Administrator
		frappe.set_user("Administrator")
		rev2.delete()
		# Rating should now be 5.0 from rev1 alone
		course_rating = flt(frappe.db.get_value("LMS Course", self.course.name, "rating"))
		self.assertEqual(course_rating, 5.0)
		details = get_course_details(self.course.name)
		self.assertEqual(details.rating, 5.0)
		self.assertEqual(details.rating_count, 1)

		# Delete rev1 as Administrator
		rev1.delete()
		# Rating should reset to 0
		course_rating = flt(frappe.db.get_value("LMS Course", self.course.name, "rating") or 0)
		self.assertEqual(course_rating, 0.0)
		details = get_course_details(self.course.name)
		self.assertEqual(details.rating, 0.0)
		self.assertEqual(details.rating_count, 0)

	def test_unenrolled_student_cannot_review(self):
		frappe.set_user(self.student1.email)
		rev = frappe.new_doc("LMS Course Review")
		rev.course = self.course.name
		rev.rating = 1.0
		rev.review = "Should fail"
		self.assertRaises(frappe.ValidationError, rev.insert)
		frappe.set_user("Administrator")

	def test_duplicate_review_blocked(self):
		self._create_enrollment(self.student1.email, self.course.name)
		frappe.set_user(self.student1.email)
		rev1 = frappe.new_doc("LMS Course Review")
		rev1.course = self.course.name
		rev1.rating = 1.0
		rev1.review = "First review"
		rev1.insert()
		self.cleanup_items.append(("LMS Course Review", rev1.name))

		rev2 = frappe.new_doc("LMS Course Review")
		rev2.course = self.course.name
		rev2.rating = 0.8
		rev2.review = "Second review should fail"
		self.assertRaises(frappe.ValidationError, rev2.insert)
		frappe.set_user("Administrator")
