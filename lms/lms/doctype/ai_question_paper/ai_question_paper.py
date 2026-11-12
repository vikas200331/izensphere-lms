# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class AIQuestionPaper(Document):
	def validate(self):
		self.validate_total_marks()
		self.validate_difficulty_distribution()
		self.validate_student_access()

	def validate_total_marks(self):
		if not self.total_marks or cint(self.total_marks) <= 0:
			frappe.throw(_("Total Marks must be a positive number."))

		if self.sections:
			calculated_marks = sum(cint(sec.total_marks) for sec in self.sections)
			if calculated_marks != cint(self.total_marks):
				frappe.throw(
					_(
						"Total marks validation failed: Section marks sum to {0}, but paper total marks is set to {1}. Total marks must match exactly."
					).format(calculated_marks, self.total_marks),
					frappe.ValidationError,
				)

	def validate_difficulty_distribution(self):
		easy = cint(self.difficulty_easy_pct or 0)
		medium = cint(self.difficulty_medium_pct or 0)
		hard = cint(self.difficulty_hard_pct or 0)
		total_pct = easy + medium + hard
		if total_pct > 0 and total_pct != 100:
			frappe.throw(
				_("Difficulty distribution must sum to 100%. Currently: Easy ({0}%) + Medium ({1}%) + Hard ({2}%) = {3}%").format(
					easy, medium, hard, total_pct
				)
			)

	def validate_student_access(self):
		# If current user is student, ensure paper is published
		user = frappe.session.user
		if user and user != "Guest":
			roles = frappe.get_roles(user)
			if "LMS Student" in roles and not any(r in roles for r in ["System Manager", "Course Creator", "Instructor", "Principal", "Moderator"]):
				if self.approval_status not in ("Principal Approved", "Published"):
					frappe.throw(_("Students can only access published and approved question papers."), frappe.PermissionError)

