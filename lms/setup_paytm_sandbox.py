import frappe
from frappe.utils.password import update_password

def setup():

    try:
        # 1. Enable Payments App if not enabled
        frappe.flags.in_install = True
        
        # 2. Configure Paytm Settings
        if not frappe.db.exists("Paytm Settings", "Paytm Settings"):
            doc = frappe.new_doc("Paytm Settings")
            doc.merchant_id = "TEST_MERCHANT_ID"
            doc.merchant_key = "TEST_MERCHANT_KEY"
            doc.staging = 1
            doc.insert(ignore_permissions=True)
            update_password("Paytm Settings", doc.name, "merchant_key", "TEST_MERCHANT_KEY")
        else:
            doc = frappe.get_doc("Paytm Settings", "Paytm Settings")
            doc.merchant_id = "TEST_MERCHANT_ID"
            doc.merchant_key = "TEST_MERCHANT_KEY"
            doc.staging = 1
            doc.save(ignore_permissions=True)
            update_password("Paytm Settings", doc.name, "merchant_key", "TEST_MERCHANT_KEY")

        # 3. Configure Payment Gateway for Paytm
        if not frappe.db.exists("Payment Gateway", "Paytm"):
            doc = frappe.new_doc("Payment Gateway")
            doc.gateway = "Paytm"
            doc.gateway_settings = "Paytm Settings"
            doc.gateway_controller = "Paytm Settings"
            doc.insert(ignore_permissions=True)
            
        # 4. Set Paytm as LMS Payment Gateway
        lms_settings = frappe.get_doc("LMS Settings", "LMS Settings")
        lms_settings.payment_gateway = "Paytm"
        lms_settings.save(ignore_permissions=True)

        frappe.db.commit()
        print("Paytm Sandbox Configured successfully")
    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    setup()
