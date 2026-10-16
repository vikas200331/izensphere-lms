# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from lms.lms.utils import get_lesson_count


class CourseChapter(Document):
	def before_insert(self):
		self.set_initial_release_status()

	def set_initial_release_status(self):
		if getattr(self.flags, "direct_publish", False):
			self.release_status = "Released"
			return

		if not self.course:
			return
		course_doc = frappe.db.get_value(
			"LMS Course",
			self.course,
			["published", "content_release_mode"],
			as_dict=True,
		)
		if (
			course_doc
			and course_doc.published
			and course_doc.content_release_mode
			and course_doc.content_release_mode not in ("None", "")
		):
			self.release_status = "Draft"
		elif not self.release_status:
			self.release_status = "Released"

	def on_update(self):
		self.update_lesson_count()

	def update_lesson_count(self):
		"""Update lesson count in the course"""
		frappe.db.set_value("LMS Course", self.course, "lessons", get_lesson_count(self.course))
