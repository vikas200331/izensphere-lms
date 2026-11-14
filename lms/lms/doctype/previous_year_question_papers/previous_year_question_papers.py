# Copyright (c) 2026, Izensphere and contributors
# For license information, please see license.txt

import hashlib
import os
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg"}


class PreviousYearQuestionPapers(Document):
	def before_insert(self):
		if not self.uploaded_by:
			self.uploaded_by = frappe.session.user
		if not self.upload_date:
			self.upload_date = now_datetime()
		if not self.ai_processing_status:
			self.ai_processing_status = "Pending"

	def validate(self):
		self.validate_student_access()
		self.validate_attachment()
		self.compute_file_checksum()

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
					_("Students do not have permission to access or modify Previous Year Question Papers."),
					frappe.PermissionError,
				)

	def validate_attachment(self):
		if not self.attachment:
			frappe.throw(_("Question paper attachment is mandatory."))

		ext = os.path.splitext(self.attachment)[1].lower()
		if ext not in SUPPORTED_EXTENSIONS:
			frappe.throw(
				_("Unsupported file format '{0}'. Supported formats are: PDF, DOCX, PNG, JPG, JPEG.").format(ext)
			)

	def compute_file_checksum(self):
		if not self.attachment:
			return

		try:
			file_doc = frappe.get_doc("File", {"file_url": self.attachment})
			file_path = file_doc.get_full_path()
			if os.path.exists(file_path):
				with open(file_path, "rb") as f:
					hasher = hashlib.md5()
					for chunk in iter(lambda: f.read(65536), b""):
						hasher.update(chunk)
					self.file_checksum = hasher.hexdigest()
		except Exception:
			# Non-fatal if File record not yet linked in database
			pass
