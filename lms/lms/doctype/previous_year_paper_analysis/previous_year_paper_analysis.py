# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class PreviousYearPaperAnalysis(Document):
	def before_insert(self):
		if not self.analyzed_by:
			self.analyzed_by = frappe.session.user
		if not self.analysis_date:
			self.analysis_date = now_datetime()
		if not self.status:
			self.status = "Draft"

	def validate(self):
		self.validate_student_access()

	def validate_student_access(self):
		user = frappe.session.user
		if user and user != "Guest":
			roles = frappe.get_roles(user)
			allowed_roles = {
				"System Manager",
				"Course Creator",
				"Instructor",
				"Principal",
				"Moderator",
				"Batch Evaluator",
				"Administrator",
			}
			if "LMS Student" in roles and not (set(roles) & allowed_roles):
				frappe.throw(
					_("Students do not have permission to view or run Previous Year Paper Analysis."),
					frappe.PermissionError,
				)
