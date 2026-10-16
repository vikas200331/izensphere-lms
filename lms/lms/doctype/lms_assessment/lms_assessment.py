import frappe
from frappe.model.document import Document


class LMSAssessment(Document):
	def before_insert(self):
		self.set_initial_release_status()

	def set_initial_release_status(self):
		if getattr(self.flags, "direct_publish", False):
			self.release_status = "Released"
			return

		if self.parent and self.parenttype == "LMS Batch":
			batch_doc = frappe.db.get_value(
				"LMS Batch",
				self.parent,
				["published", "content_release_mode"],
				as_dict=True,
			)
			if (
				batch_doc
				and batch_doc.published
				and batch_doc.content_release_mode
				and batch_doc.content_release_mode not in ("None", "")
			):
				self.release_status = "Draft"
			elif not self.release_status:
				self.release_status = "Released"
		elif not self.release_status:
			self.release_status = "Released"

