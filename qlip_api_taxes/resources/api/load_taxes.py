import frappe

from qlip_api_taxes.resources.api.response import handle as response
from qlip_api_taxes.qlip_api_taxes.uses_cases.load_taxes_dt import handle as load_taxes


@frappe.whitelist()
def qp_update_dt(upd_dt, doc_name):

    result = None

    origin = "qp_update_dt"

    error_msg = "Error load taxes doctype: {} name: {}".format(upd_dt, doc_name)

    def callback():

        load_taxes(upd_dt, doc_name)
                
        return {
            "status": 200,
            "data" : "ok"
        }

    res = response(callback, origin, error_msg)

    return res