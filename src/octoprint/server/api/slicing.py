# coding=utf-8
from __future__ import absolute_import

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"

from flask import request, jsonify, make_response, url_for

from octoprint.server import slicingManager
from octoprint.server.util.flask import restricted_access
from octoprint.server.api import api, NO_CONTENT


@api.route("/slicing/profiles", methods=["GET"])
def slicingListProfiles():
	result = dict()
	for slicer in slicingManager.registered_slicers:
		result[slicer] = _getSlicingProfilesData(slicer)
	return jsonify(result)

@api.route("/slicing/<string:slicer>/profiles", methods=["GET"])
def slicingListSlicerProfiles(slicer):
	if not slicer in slicingManager.registered_slicers:
		return make_response("Unknown slicer {slicer}".format(**locals()), 404)

	return jsonify(_getSlicingProfilesData(slicer))

@api.route("/slicing/<string:slicer>/profiles/<string:name>", methods=["GET"])
def slicingGetSlicerProfile(slicer, name):
	if not slicer in slicingManager.registered_slicers:
		return make_response("Unknown slicer {slicer}".format(**locals()), 404)

	profile = slicingManager.load_profile(slicer, name)
	if not profile:
		return make_response("Profile not found", 404)

	result = _getSlicingProfileData(slicer, name, profile)
	result["data"] = profile.data
	return jsonify(result)

@api.route("/slicing/<string:slicer>/profiles/<string:name>", methods=["PUT"])
@restricted_access
def slicingAddSlicerProfile(slicer, name):
	if not slicer in slicingManager.registered_slicers:
		return make_response("Unknown slicer {slicer}".format(**locals()), 404)

	if not "application/json" in request.headers["Content-Type"]:
		return None, None, make_response("Expected content-type JSON", 400)

	json_data = request.json

	data = dict()
	display_name = None
	description = None
	if "data" in json_data:
		data = json_data["data"]
	if "displayName" in json_data:
		display_name = json_data["displayName"]
	if "description" in json_data:
		description = json_data["description"]

	profile = slicingManager.save_profile(slicer, name, data, display_name=display_name, description=description)

	result = _getSlicingProfileData(slicer, name, profile)
	r = make_response(jsonify(result), 201)
	r.headers["Location"] = result["resource"]
	return r

@api.route("/slicing/<string:slicer>/profiles/<string:name>", methods=["PATCH"])
@restricted_access
def slicingPatchSlicerProfile(slicer, name):
	if not slicer in slicingManager.registered_slicers:
		return make_response("Unknown slicer {slicer}".format(**locals()), 404)

	if not "application/json" in request.headers["Content-Type"]:
		return None, None, make_response("Expected content-type JSON", 400)

	profile = slicingManager.load_profile(slicer, name)
	if not profile:
		return make_response("Profile not found", 404)

	json_data = request.json

	data = dict()
	display_name = None
	description = None
	if "data" in json_data:
		data = json_data["data"]
	if "displayName" in json_data:
		display_name = json_data["displayName"]
	if "description" in json_data:
		description = json_data["description"]

	slicingManager.save_profile(slicer, name, profile, overrides=data, display_name=display_name, description=description)
	return NO_CONTENT

@api.route("/slicing/<string:slicer>/profiles/<string:name>", methods=["DELETE"])
@restricted_access
def slicingDelSlicerProfile(slicer, name):
	if not slicer in slicingManager.registered_slicers:
		return make_response("Unknown slicer {slicer}".format(**locals()), 404)

	slicingManager.delete_profile(slicer, name)
	return NO_CONTENT

def _getSlicingProfilesData(slicer):
	profiles = slicingManager.all_profiles(slicer)
	if not profiles:
		return dict()

	result = dict()
	for name, profile in profiles.items():
		result[name] = _getSlicingProfileData(slicer, name, profile)
	return result

def _getSlicingProfileData(slicer, name, profile):
	result = dict(
		resource=url_for(".slicingGetSlicerProfile", slicer=slicer, name=name, _external=True)
	)
	if profile.display_name is not None:
		result["displayName"] = profile.display_name
	if profile.description is not None:
		result["description"] = profile.description
	return result