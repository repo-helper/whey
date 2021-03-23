#!/usr/bin/env python3
#
#  __init__.py
"""
:pep:`621` configuration parser.
"""
#
#  Copyright © 2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib
from typing import Any, Dict

# 3rd party
import toml
from dom_toml.parser import AbstractConfigParser, BadConfigError, construct_path
from domdf_python_tools.iterative import natmin
from domdf_python_tools.paths import PathPlus, in_directory
from domdf_python_tools.typing import PathLike
from packaging.specifiers import Specifier
from shippinglabel.requirements import combine_requirements, read_requirements

# this package
from whey.config.pep621 import PEP621Parser, read_readme
from whey.config.whey import WheyParser, backfill_classifiers, get_default_builders

__all__ = [
		"AbstractConfigParser",
		"BadConfigError",
		"PEP621Parser",
		"WheyParser",
		"backfill_classifiers",
		"load_toml",
		"read_readme",
		"construct_path",
		]


def load_toml(filename: PathLike) -> Dict[str, Any]:  # TODO: TypedDict
	"""
	Load the ``whey`` configuration mapping from the given TOML file.

	:param filename:
	"""

	filename = PathPlus(filename)

	project_dir = filename.parent
	config = toml.loads(filename.read_text())

	parsed_config = {}

	with in_directory(filename.parent):

		if "whey" in config.get("tool", {}):
			parsed_config.update(WheyParser().parse(config["tool"]["whey"]))

		if "project" in config:
			parsed_config.update(PEP621Parser().parse(config["project"]))
		else:
			raise KeyError(f"'project' table not found in '{filename!s}'")

	# set defaults
	# project
	parsed_config.setdefault("authors", [])
	parsed_config.setdefault("maintainers", [])
	parsed_config.setdefault("keywords", [])
	parsed_config.setdefault("classifiers", [])
	parsed_config.setdefault("urls", {})
	parsed_config.setdefault("scripts", {})
	parsed_config.setdefault("gui-scripts", {})
	parsed_config.setdefault("entry-points", {})
	parsed_config.setdefault("dependencies", [])
	parsed_config.setdefault("optional-dependencies", {})
	parsed_config.setdefault("requires-python", None)
	parsed_config.setdefault("description", None)
	parsed_config.setdefault("readme", None)

	# tool.whey
	parsed_config.setdefault("package", config["project"]["name"].split('.', 1)[0])
	parsed_config.setdefault("source-dir", '.')
	parsed_config.setdefault("additional-files", [])
	parsed_config.setdefault("license-key", None)
	parsed_config.setdefault("base-classifiers", [])
	parsed_config.setdefault("platforms", None)
	parsed_config.setdefault("python-versions", None)
	parsed_config.setdefault("python-implementations", None)
	parsed_config.setdefault("builders", get_default_builders())

	dynamic_fields = parsed_config.get("dynamic", [])

	if "classifiers" in dynamic_fields:
		parsed_config["classifiers"] = backfill_classifiers(parsed_config)

	if "requires-python" in dynamic_fields and parsed_config["python-versions"]:
		parsed_config["requires-python"] = Specifier(f">={natmin(parsed_config['python-versions'])}")

	if "dependencies" in dynamic_fields:
		if (project_dir / "requirements.txt").is_file():
			dependencies = read_requirements(project_dir / "requirements.txt", include_invalid=True)[0]
			parsed_config["dependencies"] = sorted(combine_requirements(dependencies))
		else:
			raise BadConfigError(
					"'project.dependencies' was listed as a dynamic field "
					"but no 'requirements.txt' file was found."
					)

	if "base-classifiers" in parsed_config:
		del parsed_config["base-classifiers"]

	return parsed_config
