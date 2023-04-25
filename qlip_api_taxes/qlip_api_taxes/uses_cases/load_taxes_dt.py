import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges


def handle(upd_dt, doc_name):

    dt_obj = frappe.get_doc(upd_dt, doc_name)

    if dt_obj.get('taxes_and_charges') and not dt_obj.get('taxes'):

        taxes = get_taxes_and_charges('Sales Taxes and Charges Template', dt_obj.taxes_and_charges)

        for tax in taxes:
            dt_obj.append('taxes', tax)

        dt_obj.calculate_taxes_and_totals()

        dt_obj.save()
