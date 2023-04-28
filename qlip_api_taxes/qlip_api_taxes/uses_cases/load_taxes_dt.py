import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges, add_taxes_from_tax_template
from erpnext.accounts.doctype.payment_entry.payment_entry import get_reference_details

from erpnext.stock.get_item_details import get_item_tax_info


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

        item_codes = []
        item_rates = {}

        for item in dt_obj.items:

            if item.item_code:
                item_codes.append([item.item_code, item.name])
                item_rates[item.name] = item.net_rate

        if len(item_codes):

            res_out = get_item_tax_info(dt_obj.company, dt_obj.tax_category, item_codes, item_rates)

            for item in dt_obj.items:

                if item.name:
                    item.item_tax_template = res_out[item.name].get('item_tax_template')
                    item.item_tax_rate = res_out[item.name].get('item_tax_rate')
                    # add_taxes_from_item_tax_template(item.item_tax_rate) # Se ejecuta el método que sigue
                    add_taxes_from_tax_template(item, dt_obj)
                else:
                    item.item_tax_template = ""
                    item.item_tax_rate = ""

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
