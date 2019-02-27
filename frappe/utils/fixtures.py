# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import frappe, os
from frappe.core.page.data_import_tool.data_import_tool import import_doc, export_json

def sync_fixtures(app=None):
	"""Import, overwrite fixtures from `[app]/fixtures`"""
	if app:
		apps = [app]
	else:
		apps = frappe.get_installed_apps()

	frappe.flags.in_fixtures = True

	for app in apps:
		if os.path.exists(frappe.get_app_path(app, "fixtures")):
			fixture_files = sorted(os.listdir(frappe.get_app_path(app, "fixtures")))
			for fname in fixture_files:

				# we are assuming that we are dealing only with json
				# files and this is why we try read as such

				_json = frappe.get_app_path(app, "fixtures", fname)

				try:

					# it's easier to apologize rather than asking
					# for permission

					_content = frappe.get_file_json(_json)

				except:

					# we will set the `content` var to an empty list
					# in case of an error

					_content = []

				# skip flag is set to false
				# if we found it to be true then we can
				# skip the last step

				skip = False

				for record in _content:

					# if this is a Custom Script record
					# then it should have its own doctype
					# and name

					doctype = record.get("doctype", None)
					name = record.get("name", None)

					# skip if we are dealing with a doctype that is not
					# a Custom Script

					if doctype is None \
						or doctype != "Custom Field":

						# lets continue iterating the next record
						# even though it is very likely that all the records
						# are going to be of the same type

						continue

					# this is getting serious now
					# so, lets import the db module
					# to make some tests

					from frappe import db

					# if the doctype itself exists or
					# there is a DocField with the same name
					# and parent then we should skip it as
					# it already exists

					if db.exists(doctype, {
						"fieldname": record.get("fieldname"),
						"dt": record.get("dt"),
						}) \
						or db.exists("DocField", {
							"fieldname": record.get("fieldname"),
							"parent": record.get("dt"),
							"parenttype": "DocType",
							"parentfield": "fields",
						}):

						# set the skip flag to true

						skip = True

						# and continue to the next item
						# as this is already in the database

						continue

					# if we got to this point is because this is a
					# Custom Script record and there is not evidence of
					# it in the database, so, lets add it

					doc = frappe.get_doc(record)

					# add some flags to be safe

					doc.flags.ignore_links = True
					doc.flags.ignore_validate = True
					doc.flags.ignore_permissions = True
					doc.flags.ignore_mandatory = True

					# and finally save
					# the newly created Custom Field

					doc.insert()

				# if the skip flag is on
				# that means that what we have done is
				# enough as of now

				if skip: continue

				# continue business a usual

				if fname.endswith(".json") or fname.endswith(".csv"):
					import_doc(frappe.get_app_path(app, "fixtures", fname),
						ignore_links=True, overwrite=True)

		import_custom_scripts(app)

	frappe.flags.in_fixtures = False

	frappe.db.commit()

def import_custom_scripts(app):
	"""Import custom scripts from `[app]/fixtures/custom_scripts`"""
	if os.path.exists(frappe.get_app_path(app, "fixtures", "custom_scripts")):
		for fname in os.listdir(frappe.get_app_path(app, "fixtures", "custom_scripts")):
			if fname.endswith(".js"):
				with open(frappe.get_app_path(app, "fixtures",
					"custom_scripts") + os.path.sep + fname) as f:
					doctype = fname.rsplit(".", 1)[0]
					script = f.read()
					if frappe.db.exists("Custom Script", {"dt": doctype}):
						custom_script = frappe.get_doc("Custom Script", {"dt": doctype})
						custom_script.script = script
						custom_script.save()
					else:
						frappe.get_doc({
							"doctype":"Custom Script",
							"dt": doctype,
							"script_type": "Client",
							"script": script
						}).insert()

def export_fixtures():
	"""Export fixtures as JSON to `[app]/fixtures`"""
	for app in frappe.get_installed_apps():
		for fixture in frappe.get_hooks("fixtures", app_name=app):
			filters = None
			if isinstance(fixture, dict):
				filters = fixture.get("filters")
				fixture = fixture.get("doctype") or fixture.get("dt")
			print "Exporting {0} app {1} filters {2}".format(fixture, app, filters)
			if not os.path.exists(frappe.get_app_path(app, "fixtures")):
				os.mkdir(frappe.get_app_path(app, "fixtures"))

			export_json(fixture, frappe.get_app_path(app, "fixtures", frappe.scrub(fixture) + ".json"), filters=filters)
