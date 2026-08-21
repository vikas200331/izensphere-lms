import frappe
def execute():
    for user in ['Administrator', 'vikasksmca2026@gmail.com']:
        try:
            doc = frappe.get_doc('User', user)
            doc.remove_roles('Principal')
            print(f'Removed Principal from {user}')
        except Exception as e:
            pass
    frappe.db.commit()
