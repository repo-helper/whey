#!/usr/bin/env python3
#
#  whey.py
"""
Parser for whey's own configuration.
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
import itertools
from typing import Dict, Iterable, List, Set, Type

# 3rd party
from dom_toml.parser import TOML_TYPES, AbstractConfigParser, BadConfigError
from domdf_python_tools.compat import importlib_metadata
from natsort import natsorted
from shippinglabel.classifiers import validate_classifiers

# this package
from whey.builder import AbstractBuilder, SDistBuilder, WheelBuilder

__all__ = ["WheyParser", "backfill_classifiers", "get_default_builders", "get_entry_points"]

#: Mapping of license short codes to license names used in trove classifiers.
license_lookup = {
		"Apache-2.0": "Apache Software License",
		"BSD": "BSD License",
		"BSD-2-Clause": "BSD License",
		"BSD-3-Clause": "BSD License",
		"AGPL-3.0-only": "GNU Affero General Public License v3",
		"AGPL-3.0": "GNU Affero General Public License v3",
		"AGPL-3.0-or-later": "GNU Affero General Public License v3 or later (AGPLv3+)",
		"AGPL-3.0+": "GNU Affero General Public License v3 or later (AGPLv3+)",
		"FDL": "GNU Free Documentation License (FDL)",
		"GFDL-1.1-only": "GNU Free Documentation License (FDL)",
		"GFDL-1.1-or-later": "GNU Free Documentation License (FDL)",
		"GFDL-1.2-only": "GNU Free Documentation License (FDL)",
		"GFDL-1.2-or-later": "GNU Free Documentation License (FDL)",
		"GFDL-1.3-only": "GNU Free Documentation License (FDL)",
		"GFDL-1.3-or-later": "GNU Free Documentation License (FDL)",
		"GFDL-1.2": "GNU Free Documentation License (FDL)",
		"GFDL-1.1": "GNU Free Documentation License (FDL)",
		"GFDL-1.3": "GNU Free Documentation License (FDL)",
		"GPL": "GNU General Public License (GPL)",
		"GPL-1.0-only": "GNU General Public License (GPL)",
		"GPL-1.0-or-later": "GNU General Public License (GPL)",
		"GPLv2": "GNU General Public License v2 (GPLv2)",
		"GPL-2.0-only": "GNU General Public License v2 (GPLv2)",
		"GPLv2+": "GNU General Public License v2 or later (GPLv2+)",
		"GPL-2.0-or-later": "GNU General Public License v2 or later (GPLv2+)",
		"GPLv3": "GNU General Public License v3 (GPLv3)",
		"GPL-3.0-only": "GNU General Public License v3 (GPLv3)",
		"GPLv3+": "GNU General Public License v3 or later (GPLv3+)",
		"GPL-3.0-or-later": "GNU General Public License v3 or later (GPLv3+)",
		"LGPLv2": "GNU Lesser General Public License v2 (LGPLv2)",
		"LGPLv2+": "GNU Lesser General Public License v2 or later (LGPLv2+)",
		"LGPLv3": "GNU Lesser General Public License v3 (LGPLv3)",
		"LGPL-3.0-only": "GNU Lesser General Public License v3 (LGPLv3)",
		"LGPLv3+": "GNU Lesser General Public License v3 or later (LGPLv3+)",
		"LGPL-3.0-or-later": "GNU Lesser General Public License v3 or later (LGPLv3+)",
		"LGPL": "GNU Library or Lesser General Public License (LGPL)",
		"MIT": "MIT License",
		"PSF-2.0": "Python Software Foundation License",
		}


def get_default_builders() -> Dict[str, Type[AbstractBuilder]]:
	"""
	Returns a mapping of builder categories to builder classes to use as the default builders.
	"""

	return {"sdist": SDistBuilder, "binary": WheelBuilder, "wheel": WheelBuilder}


class WheyParser(AbstractConfigParser):
	"""
	Parser for the ``[tool.whey]`` table from ``pyproject.toml``.

	.. autosummary-widths:: 1/2
		:html: 45/100
	"""

	defaults = {
			"source-dir": '.',
			"license-key": None,
			"platforms": None,
			"python-versions": None,
			"python-implementations": None,
			}
	factories = {
			"additional-files": list,
			"base-classifiers": list,
			"builders": get_default_builders,
			}

	def parse_package(self, config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the ``package`` key, giving the name of the importable package.

		This defaults to :pep621:`project.name <name>` if unspecified.

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""

		package = config["package"]

		self.assert_type(package, str, ["tool", "whey", "package"])

		return package

	def parse_source_dir(self, config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the ``source-dir`` key, giving the name of the directory containing the project's source.

		This defaults to ``'.'`` if unspecified.

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""

		source_dir = config["source-dir"]

		self.assert_type(source_dir, str, ["tool", "whey", "source-dir"])

		return source_dir

	def parse_license_key(self, config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the ``license-key`` key, giving the identifier of the project's license. Optional.

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""

		license_key = config["license-key"]

		self.assert_type(license_key, str, ["tool", "whey", "license-key"])

		return license_key

	def parse_additional_files(self, config: Dict[str, TOML_TYPES]) -> List[str]:
		"""
		Parse the ``additional-files`` key, giving `MANIFEST.in`_-style
		entries for additional files to include in distributions.

		.. _MANIFEST.in: https://packaging.python.org/guides/using-manifest-in/

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""  # noqa: D400

		additional_files = config["additional-files"]

		for idx, file in enumerate(additional_files):
			self.assert_indexed_type(file, str, ["tool", "whey", "additional-files"], idx=idx)

		return additional_files

	def parse_platforms(self, config: Dict[str, TOML_TYPES]) -> List[str]:
		"""
		Parse the ``platforms`` key, giving a list of supported platforms. Optional.

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""

		platforms = config["platforms"]

		for idx, plat in enumerate(platforms):
			self.assert_indexed_type(plat, str, ["tool", "whey", "platforms"], idx=idx)

		return platforms

	@staticmethod
	def parse_python_versions(config: Dict[str, TOML_TYPES]) -> List[str]:
		"""
		Parse the ``python-versions`` key, giving a list of supported Python versions. Optional.

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""

		python_versions = config["python-versions"]

		for idx, version in enumerate(python_versions):
			if not isinstance(version, (str, int, float)):
				raise TypeError(
						f"Invalid type for 'tool.whey.python-versions[{idx}]': "
						f"expected {str!r}, {int!r} or {float!r}, got {type(version)!r}"
						)
			if str(version) in "12":
				raise BadConfigError(
						f"Invalid value for 'tool.whey.python-versions[{idx}]': whey only supports Python 3-only projects."
						)

		return list(map(str, python_versions))

	def parse_python_implementations(self, config: Dict[str, TOML_TYPES]) -> List[str]:
		"""
		Parse the ``python-implementations`` key, giving a list of supported Python implementations. Optional.

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.

		:rtype:

		.. latex:clearpage::
		"""

		python_implementations = config["python-implementations"]

		for idx, impl in enumerate(python_implementations):
			self.assert_indexed_type(impl, str, ["tool", "whey", "python-implementations"], idx=idx)

		return python_implementations

	def parse_base_classifiers(self, config: Dict[str, TOML_TYPES]) -> Set[str]:
		"""
		Parse the ``base-classifiers`` key, giving a list `trove classifiers <https://pypi.org/classifiers/>`__.

		This list will be extended with the appropriate classifiers for supported platforms,
		Python versions and implementations, and the project's license.
		Ignored if :pep621:`classifiers` is not listed in :pep621:`dynamic`

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""

		parsed_classifiers = set()

		for idx, classifier in enumerate(config["base-classifiers"]):
			self.assert_indexed_type(classifier, str, ["tool", "whey", "python-implementations"], idx=idx)
			parsed_classifiers.add(classifier)

		return parsed_classifiers

	def parse_builders(self, config: Dict[str, TOML_TYPES]) -> Dict[str, Type[AbstractBuilder]]:
		"""
		Parse the ``builders`` table, which lists gives the entry points to use for the sdist and wheel builders.

		This allows the user to select a custom builder with additional functionality.

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""

		parsed_builders = get_default_builders()
		builders = config["builders"]

		entry_points: Dict[str, importlib_metadata.EntryPoint] = get_entry_points()

		self.assert_type(builders, dict, ["tool", "whey", "builders"])

		for builder_type in ["binary", "sdist", "wheel"]:
			if builder_type in builders:
				entry_point_name = builders[builder_type]
				if entry_point_name not in entry_points:
					raise BadConfigError(
							f"Unknown {builder_type} builder {entry_point_name}. \n"
							f"Is it registered as an entry point under 'whey.builder'?"
							)

				parsed_builders[builder_type] = entry_points[entry_point_name].load()

		return parsed_builders

	@property
	def keys(self) -> List[str]:
		"""
		The keys to parse from the TOML file.
		"""

		return [
				"package",
				"source-dir",
				"additional-files",
				"license-key",
				"base-classifiers",
				"platforms",
				"python-versions",
				"python-implementations",
				"builders",
				]


def backfill_classifiers(config: Dict[str, TOML_TYPES]) -> List[str]:
	"""
	Backfill `trove classifiers <https://pypi.org/classifiers/>`_ for supported platforms,
	Python versions and implementations, and the project's license, as appropriate.

	:param config: The parsed config from ``pyproject.toml``.
	"""  # noqa: D400

	# TODO: Typing :: Typed

	parsed_classifiers = set(config["base-classifiers"])

	platforms = config["platforms"]
	license_key = config["license-key"]
	python_versions = config["python-versions"]
	python_implementations = config["python-implementations"]

	if license_key in license_lookup:
		parsed_classifiers.add(f"License :: OSI Approved :: {license_lookup[license_key]}")

	if platforms:

		if set(platforms) == {"Windows", "macOS", "Linux"}:
			parsed_classifiers.add("Operating System :: OS Independent")
		else:
			if "Windows" in platforms:
				parsed_classifiers.add("Operating System :: Microsoft :: Windows")
			if "Linux" in platforms:
				parsed_classifiers.add("Operating System :: POSIX :: Linux")
			if "macOS" in platforms:
				parsed_classifiers.add("Operating System :: MacOS")

	if python_versions:
		for version in python_versions:
			parsed_classifiers.add(f"Programming Language :: Python :: {version}")

		parsed_classifiers.add("Programming Language :: Python :: 3 :: Only")

	if python_implementations:
		for implementation in python_implementations:
			parsed_classifiers.add(f"Programming Language :: Python :: Implementation :: {implementation}")

	parsed_classifiers.add("Programming Language :: Python")

	validate_classifiers(parsed_classifiers)

	return natsorted(parsed_classifiers)


def get_entry_points() -> Dict[str, importlib_metadata.EntryPoint]:
	r"""
	Returns an iterable over `EntryPoint`_ objects in the ``whey.builder`` group.

	:rtype: :class:`Iterable <typing.Iterable>`\[`EntryPoint`_\]

	.. _EntryPoint: https://docs.python.org/3/library/importlib.metadata.html#entry-points
	"""

	eps = itertools.chain.from_iterable(dist.entry_points for dist in importlib_metadata.distributions())

	entry_points: Dict[str, "importlib_metadata.EntryPoint"] = {}

	for entry_point in eps:
		if entry_point.group == "whey.builder":
			entry_points[entry_point.name] = entry_point

	return entry_points
