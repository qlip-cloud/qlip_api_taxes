import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges, add_taxes_from_tax_template
from erpnext.accounts.doctype.payment_entry.payment_entry import get_reference_details


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

    elif not dt_obj.get('taxes_and_charges') and not dt_obj.get('taxes'):

        for item in dt_obj.items:

            if item.name:

                add_taxes_from_tax_template(item, dt_obj)

        dt_obj.calculate_taxes_and_totals()

        dt_obj.save()


def set_taxes_payment_entry(upd_dt, doc_name):

    master_doctype = ''
    taxes_and_charges = ''

    dt_obj = frappe.get_doc(upd_dt, doc_name)

    # Respaldar referencias para luego cargarlas tomando en cuenta los impuestos
    ref_aux = dt_obj.get("references")
    dt_obj.references = []

    # Proceder a Calcular los impuestos

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

    # Restaurar líneas de la referencia

    for item_ref in ref_aux:

        ref_details = get_reference_details(item_ref.reference_doctype,
            item_ref.reference_name, dt_obj.party_account_currency)

        if dt_obj.unallocated_amount > item_ref.outstanding_amount:
            allocated_amount = item_ref.outstanding_amount
        else:
            allocated_amount = dt_obj.unallocated_amount

        item_ref.allocated_amount = allocated_amount

        dt_obj.append("references", item_ref)

    dt_obj.save()
