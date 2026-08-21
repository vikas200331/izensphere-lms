import frappe
def execute():
    frappe.db.set_value('Workflow', 'Course Approval Workflow', 'send_email_alert', 0)
    frappe.db.set_value('Workflow', 'Batch Approval Workflow', 'send_email_alert', 0)
    frappe.db.commit()
    print("Workflow emails disabled")
