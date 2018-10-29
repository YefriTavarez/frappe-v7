import frappe

@frappe.whitelist()
def get_desk_assets(args):
	from frappe.www.desk import get_desk_assets
	return get_desk_assets(args)