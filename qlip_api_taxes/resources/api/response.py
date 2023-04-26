import frappe
import traceback
from frappe import _

def handle(callback, origin, error_msg):
    
    try:

        result =  callback()

        frappe.db.commit()

        return result
        
    except Exception as error:

        frappe.db.rollback()

        frappe.log_error(message=frappe.get_traceback(), title = origin)
        
        traceback.print_exc()

        print(error)

        return {
            'status': 400, 
            'msg': _(error_msg)
        }
