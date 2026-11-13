# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class LMSCourseReview(Document):
	def validate(self):
		self.validate_enrollment()
		self.validate_if_already_reviewed()

	def validate_enrollment(self):
		enrollment = frappe.db.exists("LMS Enrollment", {"course": self.course, "member": self.owner})
		if not enrollment:
			frappe.throw(_("You must be enrolled in the course to submit a review"))

	def validate_if_already_reviewed(self):
		existing = frappe.db.get_value("LMS Course Review", {"course": self.course, "owner": self.owner}, "name")
		if existing and existing != self.name:
			frappe.throw(_("You have already reviewed this course"))

	def after_insert(self):
		self.update_course_rating()

	def on_update(self):
		self.update_course_rating()

	def after_delete(self):
		self.update_course_rating()

	def on_trash(self):
		self.update_course_rating(exclude_self=True)

	def update_course_rating(self, exclude_self=False):
		if not self.course:
			return
		update_course_rating(self.course, exclude_review=self.name if exclude_self else None)


def update_course_rating(course: str, exclude_review: str | None = None) -> float:
	from lms.lms.utils import get_average_rating

	avg_rating = get_average_rating(course, exclude_review=exclude_review)
	rating_val = flt(avg_rating, frappe.get_system_settings("float_precision") or 3) if avg_rating is not None else 0
	frappe.db.set_value("LMS Course", course, "rating", rating_val)
	frappe.clear_document_cache("LMS Course", course)
	return rating_val
