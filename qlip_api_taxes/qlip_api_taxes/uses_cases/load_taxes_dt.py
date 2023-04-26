import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges


def handle(upd_dt, doc_name):

    if upd_dt == "Sales Invoice":

        set_taxes_sales_invoice(upd_dt, doc_name)

    elif upd_dt == "Payment Entry":

        set_taxes_payment_entry(upd_dt, doc_name)
        


def set_taxes_sales_invoice(upd_dt, doc_name):

    dt_obj = frappe.get_doc(upd_dt, doc_name)

    if dt_obj.get('taxes_and_charges') and not dt_obj.get('taxes'):

        taxes = get_taxes_and_charges('Sales Taxes and Charges Template', dt_obj.taxes_and_charges)

        for tax in taxes:
            dt_obj.append('taxes', tax)

        dt_obj.calculate_taxes_and_totals()

        dt_obj.save()


def set_taxes_payment_entry(upd_dt, doc_name):

    master_doctype = ''
    taxes_and_charges = ''

    dt_obj = frappe.get_doc(upd_dt, doc_name)

    if dt_obj.party_type == 'Supplier':

        master_doctype = 'Purchase Taxes and Charges Template'
        taxes_and_charges = dt_obj.purchase_taxes_and_charges_template

    elif dt_obj.party_type == 'Customer':

        master_doctype = 'Sales Taxes and Charges Template'
        taxes_and_charges = dt_obj.sales_taxes_and_charges_template

    if not taxes_and_charges:

        return

    taxes = get_taxes_and_charges(master_doctype, taxes_and_charges)

    for tax in taxes:

        if tax.charge_type == 'On Net Total':
            tax.charge_type = 'On Paid Amount'

        
        # TODO: Determinar valor que corresponde según tipo de tercero
        tax.add_deduct_tax = 'Add'

        dt_obj.append('taxes', tax)


    dt_obj.apply_taxes()

    dt_obj.set_amounts()

    dt_obj.save()
