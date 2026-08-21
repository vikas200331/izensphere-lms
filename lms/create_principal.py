import frappe
def execute():
    email = "principal@example.com"
    if not frappe.db.exists("User", email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Principal",
            "send_welcome_email": 0
        })
        user.insert(ignore_permissions=True)
        # Set a default password
        user.new_password = "Password@123"
        user.save(ignore_permissions=True)
        print(f"Created user {email} with password Password@123")
    else:
        user = frappe.get_doc("User", email)
    
    user.add_roles("Principal")
    print("Added Principal role.")
    frappe.db.commit()
