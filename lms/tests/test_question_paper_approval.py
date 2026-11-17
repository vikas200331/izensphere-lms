# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from lms.lms.api import get_pending_content_for_principal, process_approval, is_authorized_approver


class TestQuestionPaperApproval(FrappeTestCase):
	def setUp(self):
		self.principal = "principal@example.com"
		if not frappe.db.exists("User", self.principal):
			u = frappe.new_doc("User")
			u.email = self.principal
			u.first_name = "Principal"
			u.enabled = 1
			u.append("roles", {"role": "Principal"})
			u.insert(ignore_permissions=True)
		else:
			if not frappe.db.exists("Has Role", {"parent": self.principal, "role": "Principal"}):
				frappe.get_doc("User", self.principal).add_roles("Principal")

	def test_question_paper_approval_workflow(self):
		"""Verify that AI Question Paper with 'Submitted for Approval' appears on Principal Dashboard
		and can be Approved/Published or Rejected via process_approval."""
		# 1. Create a test AI Question Paper
		paper = frappe.new_doc("AI Question Paper")
		paper.title = "Test Midterm Question Paper 2026"
		paper.subject = "Computer Science"
		paper.class_level = "Class 10"
		paper.total_marks = 80
		paper.approval_status = "Submitted for Approval"
		paper.created_by_teacher = "Administrator"
		paper.insert(ignore_permissions=True)
		frappe.db.commit()

		paper_name = paper.name

		try:
			# 2. Check that it appears in Principal Dashboard pending content
			frappe.set_user(self.principal)
			pending = get_pending_content_for_principal()
			qp_items = [it for it in pending if it.get("doctype") == "AI Question Paper" and it.get("name") == paper_name]
			self.assertTrue(len(qp_items) == 1, "Submitted question paper must be visible in get_pending_content_for_principal")

			item = qp_items[0]
			self.assertEqual(item["content_type"], "Question Paper")
			self.assertEqual(item["title"], "Test Midterm Question Paper 2026")
			self.assertEqual(item["total_marks"], 80)
			self.assertEqual(item["subject"], "Computer Science")

			# 3. Principal Rejects with comments
			process_approval("AI Question Paper", paper_name, "Reject", comments="Please revise Section B marks")
			status = frappe.db.get_value("AI Question Paper", paper_name, "approval_status")
			reason = frappe.db.get_value("AI Question Paper", paper_name, "rejection_reason")
			self.assertEqual(status, "Rejected")
			self.assertEqual(reason, "Please revise Section B marks")

			# 4. Rejected item is no longer in pending list
			pending_after_reject = get_pending_content_for_principal()
			qp_after_reject = [it for it in pending_after_reject if it.get("doctype") == "AI Question Paper" and it.get("name") == paper_name]
			self.assertEqual(len(qp_after_reject), 0, "Rejected paper must not be in pending list")

			# 5. Teacher resubmits
			frappe.db.set_value("AI Question Paper", paper_name, "approval_status", "Submitted for Approval")
			pending_after_resubmit = get_pending_content_for_principal()
			qp_resubmit = [it for it in pending_after_resubmit if it.get("doctype") == "AI Question Paper" and it.get("name") == paper_name]
			self.assertEqual(len(qp_resubmit), 1, "Resubmitted paper must reappear in pending list")

			# 6. Principal Approves
			process_approval("AI Question Paper", paper_name, "Approve")
			status_approved = frappe.db.get_value("AI Question Paper", paper_name, "approval_status")
			self.assertEqual(status_approved, "Published")

			# 7. Published item is no longer in pending list
			pending_final = get_pending_content_for_principal()
			qp_final = [it for it in pending_final if it.get("doctype") == "AI Question Paper" and it.get("name") == paper_name]
			self.assertEqual(len(qp_final), 0, "Published paper must no longer be in pending list")

		finally:
			frappe.set_user("Administrator")
			if frappe.db.exists("AI Question Paper", paper_name):
				frappe.delete_doc("AI Question Paper", paper_name, force=True)
