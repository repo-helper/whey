#!/usr/bin/env python3
#
#  __init__.py
"""
``pyproject.toml`` configuration parsing.
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
import re
from typing import Any, Dict

# 3rd party
import dom_toml
from dom_toml.parser import BadConfigError
from domdf_python_tools.iterative import natmin
from domdf_python_tools.paths import PathPlus, in_directory
from domdf_python_tools.typing import PathLike
from packaging.specifiers import Specifier
from shippinglabel.requirements import combine_requirements, read_requirements

# this package
from whey.config.pep621 import PEP621Parser
from whey.config.whey import WheyParser, backfill_classifiers

__all__ = [
		"BadConfigError",
		"PEP621Parser",
		"WheyParser",
		"backfill_classifiers",
		"load_toml",
		]

_name_to_package_re = re.compile("-(?!stubs)")


def _get_default_package(name: str) -> str:
	return _name_to_package_re.sub('_', name.split('.', 1)[0])


def load_toml(filename: PathLike) -> Dict[str, Any]:  # TODO: TypedDict
	"""
	Load the ``whey`` configuration mapping from the given TOML file.

	:param filename:
	"""

	filename = PathPlus(filename)

	project_dir = filename.parent
	config = dom_toml.load(filename)

	parsed_config = {}
	tool_table = config.get("tool", {})

	with in_directory(project_dir):

		parsed_config.update(WheyParser().parse(tool_table.get("whey", {}), set_defaults=True))

		if "project" in config:
			parsed_config.update(PEP621Parser().parse(config["project"], set_defaults=True))
		else:
			raise KeyError(f"'project' table not found in '{filename!s}'")

		if parsed_config.get("readme", None) is not None:
			parsed_config["readme"] = parsed_config["readme"].resolve()

		if parsed_config.get("license", None) is not None:
			parsed_config["license"] = parsed_config["license"].resolve()

	# set defaults
	parsed_config.setdefault("package", _get_default_package(config["project"]["name"]))

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
