# coding=utf-8
from __future__ import absolute_import

__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2014 The OctoPrint Project - Released under terms of the AGPLv3 License"

import logging
import os

import octoprint.plugin

import octoprint.slicing

default_settings = {
	"cura_engine": None,
	"default_profile": None
}
s = octoprint.plugin.plugin_settings("cura", defaults=default_settings)

from .profile import Profile

class CuraPlugin(octoprint.plugin.SlicerPlugin):

	def __init__(self):
		self._logger = logging.getLogger("octoprint.plugins." + __name__)

	def get_slicer_type(self):
		return "cura"

	def get_slicer_default_profile(self):
		path = s.get(["default_profile"])
		if not path:
			path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "profiles", "default.profile.yaml")
		return self.get_slicer_profile(path)

	def get_slicer_profile(self, path):
		profile_dict = self._load_profile(path)

		display_name = None
		description = None
		if "_display_name" in profile_dict:
			display_name = profile_dict["_display_name"]
			del profile_dict["_display_name"]
		if "_description" in profile_dict:
			description = profile_dict["_description"]
			del profile_dict["_description"]

		return octoprint.slicing.SlicingProfile(self.get_slicer_type(), "unknown", profile_dict, display_name=display_name, description=description)

	def save_slicer_profile(self, path, profile, allow_overwrite=True, overrides=None):
		new_profile = Profile.merge_profile(profile.data, overrides=overrides)

		if profile.display_name is not None:
			new_profile["_display_name"] = profile.display_name
		if profile.description is not None:
			new_profile["_description"] = profile.description

		self._save_profile(path, new_profile, allow_overwrite=allow_overwrite)

	def do_slice(self, model_path, machinecode_path=None, profile_path=None):
		if not profile_path:
			profile_path = s.get(["default_profile"])
		if not machinecode_path:
			path, _ = os.path.splitext(model_path)
			machinecode_path = path + ".gco"

		engine_settings = self._convert_to_engine(profile_path)

		executable = s.get(["cura_engine"])
		working_dir, _ = os.path.split(executable)
		args = ['"%s"' % executable, '-v', '-p']
		for k, v in engine_settings.items():
			args += ["-s", '"%s=%s"' % (k, str(v))]
		args += ['-o', '"%s"' % machinecode_path, '"%s"' % model_path]

		import sarge
		command = " ".join(args)
		self._logger.info("Running %r in %s" % (command, working_dir))
		try:
			p = sarge.run(command, cwd=working_dir)
			if p.returncode == 0:
				return True, None
			else:
				self._logger.warn("Could not slice via Cura, got return code %r" % p.returncode)
				return False, "Got returncode %r" % p.returncode
		except:
			self._logger.exception("Could not slice via Cura, got an unknown error")
			return False, "Unknown error, please consult the log file"


	def _load_profile(self, path):
		import yaml
		profile_dict = dict()
		with open(path, "r") as f:
			try:
				profile_dict = yaml.safe_load(f)
			except:
				raise IOError("Couldn't read profile from {path}".format(path=path))
		return profile_dict

	def _save_profile(self, path, profile, allow_overwrite=True):
		if not allow_overwrite and os.path.exists(path):
			raise IOError("Cannot overwrite {path}".format(path=path))

		import yaml
		with open(path, "wb") as f:
			yaml.safe_dump(profile, f, default_flow_style=False, indent="  ", allow_unicode=True)

	def _convert_to_engine(self, profile_path):
		profile = Profile(self._load_profile(profile_path))
		return profile.convert_to_engine()


__plugin_name__ = "cura"
__plugin_version__ = "0.1"
__plugin_implementations__ = [CuraPlugin()]