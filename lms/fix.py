import frappe

def execute():
    # 1. Ensure Workflow Actions
    actions = ["Publish", "Unpublish"]
    for action in actions:
        if not frappe.db.exists("Workflow Action Master", action):
            frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)
            print(f"Created Workflow Action: {action}")
            frappe.db.commit()

    # 2. Fix Workflows
    for wf_name in ["LMS Course Approval", "LMS Batch Approval"]:
        if frappe.db.exists("Workflow", wf_name):
            doc = frappe.get_doc("Workflow", wf_name)
            
            # Ensure "Published" State allows Principal to Edit
            for s in doc.states:
                if s.state == "Published" and s.allow_edit != "Principal":
                    s.allow_edit = "Principal"
                    print(f"Set allow_edit='Principal' for 'Published' state in {wf_name}")
            
            # Ensure "Approved" State allows Principal to Edit (it already should)
            for s in doc.states:
                if s.state == "Approved" and s.allow_edit != "Principal":
                    s.allow_edit = "Principal"
                    print(f"Set allow_edit='Principal' for 'Approved' state in {wf_name}")

            # Define expected transitions for Principal
            expected_transitions = [
                {"state": "Approved", "action": "Publish", "next_state": "Published", "allowed": "Principal"},
                {"state": "Published", "action": "Unpublish", "next_state": "Approved", "allowed": "Principal"}
            ]

            for expected in expected_transitions:
                exists = any(t.state == expected["state"] and t.action == expected["action"] and t.next_state == expected["next_state"] and t.allowed == expected["allowed"] for t in doc.transitions)
                if not exists:
                    # Remove any existing transition with same state/action to prevent duplicates
                    doc.transitions = [t for t in doc.transitions if not (t.state == expected["state"] and t.action == expected["action"])]
                    doc.append("transitions", expected)
                    print(f"Added transition {expected['state']} -> {expected['action']} -> {expected['next_state']} for {wf_name}")

            doc.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"Successfully configured workflow: {wf_name}")
