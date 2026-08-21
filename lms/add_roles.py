import frappe
def execute():
    for user in ['Administrator', 'vikasksmca2026@gmail.com']:
        try:
            doc = frappe.get_doc('User', user)
            doc.add_roles('Principal')
            print(f'Added Principal to {user}')
        except Exception as e:
            pass
    frappe.db.commit()
