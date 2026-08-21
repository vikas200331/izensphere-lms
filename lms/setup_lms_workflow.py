import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup():
    frappe.flags.in_test = True
    
    # 1. Create Principal Role
    if not frappe.db.exists("Role", "Principal"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "Principal",
            "desk_access": 1
        }).insert(ignore_permissions=True)
        print("Created Role: Principal")

    # 2. Add custom field 'workflow_state' to LMS Course and LMS Batch if not exists
    custom_fields = {
        "LMS Course": [
            {
                "fieldname": "workflow_state",
                "label": "Workflow State",
                "fieldtype": "Link",
                "options": "Workflow State",
                "insert_after": "status",
                "read_only": 1,
                "hidden": 1
            }
        ],
        "LMS Batch": [
            {
                "fieldname": "workflow_state",
                "label": "Workflow State",
                "fieldtype": "Link",
                "options": "Workflow State",
                "insert_after": "published",
                "read_only": 1,
                "hidden": 1
            }
        ]
    }
    create_custom_fields(custom_fields)
    print("Created workflow_state custom fields.")

    # 3. Create Workflow States
    states = [
        {"name": "Draft", "style": "Primary"},
        {"name": "Pending Principal Approval", "style": "Warning"},
        {"name": "Approved", "style": "Success"},
        {"name": "Published", "style": "Success"},
        {"name": "Rejected", "style": "Danger"}
    ]
    for s in states:
        if not frappe.db.exists("Workflow State", s["name"]):
            frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": s["name"],
                "style": s["style"]
            }).insert(ignore_permissions=True)
            print(f"Created Workflow State: {s['name']}")

    # 4. Create Workflow Actions
    actions = ["Submit for Approval", "Approve", "Publish", "Reject", "Edit and Resubmit"]
    for a in actions:
        if not frappe.db.exists("Workflow Action Master", a):
            frappe.get_doc({
                "doctype": "Workflow Action Master",
                "workflow_action_name": a
            }).insert(ignore_permissions=True)
            print(f"Created Workflow Action: {a}")

    # 5. Create Workflow for LMS Course
    create_workflow("LMS Course Approval", "LMS Course")

    # 6. Create Workflow for LMS Batch
    create_workflow("LMS Batch Approval", "LMS Batch")
    
    frappe.db.commit()


def create_workflow(workflow_name, document_type):
    if frappe.db.exists("Workflow", workflow_name):
        print(f"Workflow {workflow_name} already exists.")
        return

    doc = frappe.new_doc("Workflow")
    doc.workflow_name = workflow_name
    doc.document_type = document_type
    doc.is_active = 1
    doc.workflow_state_field = "workflow_state"
    
    # We update the 'published' field based on state
    # States
    doc.append("states", {
        "state": "Draft",
        "doc_status": 0,
        "update_field": "published",
        "update_value": "0",
        "allow_edit": "Course Creator"
    })
    doc.append("states", {
        "state": "Pending Principal Approval",
        "doc_status": 0,
        "update_field": "published",
        "update_value": "0",
        "allow_edit": "Principal"
    })
    doc.append("states", {
        "state": "Approved",
        "doc_status": 0,
        "update_field": "published",
        "update_value": "0",
        "allow_edit": "Principal"
    })
    doc.append("states", {
        "state": "Published",
        "doc_status": 0,
        "update_field": "published",
        "update_value": "1",
        "allow_edit": "Principal"
    })
    doc.append("states", {
        "state": "Rejected",
        "doc_status": 0,
        "update_field": "published",
        "update_value": "0",
        "allow_edit": "Course Creator"
    })
    
    # Transitions
    doc.append("transitions", {
        "state": "Draft",
        "action": "Submit for Approval",
        "next_state": "Pending Principal Approval",
        "allowed": "Course Creator",
        "allow_self_approval": 1
    })
    doc.append("transitions", {
        "state": "Pending Principal Approval",
        "action": "Approve",
        "next_state": "Approved",
        "allowed": "Principal",
        "allow_self_approval": 1
    })
    doc.append("transitions", {
        "state": "Pending Principal Approval",
        "action": "Reject",
        "next_state": "Rejected",
        "allowed": "Principal",
        "allow_self_approval": 1
    })
    doc.append("transitions", {
        "state": "Rejected",
        "action": "Edit and Resubmit",
        "next_state": "Pending Principal Approval",
        "allowed": "Course Creator",
        "allow_self_approval": 1
    })
    doc.append("transitions", {
        "state": "Approved",
        "action": "Publish",
        "next_state": "Published",
        "allowed": "Principal",
        "allow_self_approval": 1
    })
    
    doc.insert(ignore_permissions=True)
    print(f"Created Workflow: {workflow_name}")
