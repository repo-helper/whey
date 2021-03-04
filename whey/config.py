#!/usr/bin/env python3
#
#  config.py
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
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Type, Union

# 3rd party
import readme_renderer.markdown  # type: ignore
import readme_renderer.rst  # type: ignore
import toml
from apeye import URL
from domdf_python_tools.iterative import natmin
from domdf_python_tools.paths import PathPlus, in_directory
from domdf_python_tools.typing import PathLike
from domdf_python_tools.words import word_join
from email_validator import EmailSyntaxError, validate_email  # type: ignore
from natsort import natsorted, ns
from packaging.specifiers import InvalidSpecifier, Specifier, SpecifierSet
from packaging.version import InvalidVersion, Version
from shippinglabel import normalize
from shippinglabel.classifiers import validate_classifiers
from shippinglabel.requirements import ComparableRequirement, combine_requirements, read_requirements

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

TOML_TYPES = Any
name_re = re.compile("^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", flags=re.IGNORECASE)

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


class BadConfigError(ValueError):
	"""
	Indicates an error in the ``pyproject.toml`` configuration.
	"""


def construct_path(path: Iterable[str]) -> str:
	"""
	Construct a dotted path to a key.

	:param path: The path elements.
	"""

	return '.'.join([toml.dumps({elem: 0})[:-5] for elem in path])


def read_readme(readme_file: PathLike, encoding="UTF-8") -> Tuple[str, str]:
	"""
	Reads the readme file and returns the content of the file and its content type.

	:param readme_file:
	:param encoding:
	"""

	readme_file = PathPlus(readme_file)

	if readme_file.suffix.lower() == ".md":
		content = readme_file.read_text(encoding=encoding)
		readme_renderer.markdown.render(content)
		return content, "text/markdown"
	elif readme_file.suffix.lower() == ".rst":
		content = readme_file.read_text(encoding=encoding)
		readme_renderer.rst.render(content)
		return content, "text/x-rst"
	elif readme_file.suffix.lower() == ".txt":
		return readme_file.read_text(encoding=encoding), "text/plain"
	else:
		raise ValueError(f"Unrecognised filetype for '{readme_file!s}'")


class AbstractConfigParser(ABC):
	"""
	Abstract base class for TOML configuration parsers.
	"""

	@staticmethod
	def assert_type(
			obj: Any,
			expected_type: Type,
			path: Iterable[str],
			what: str = "type",
			) -> None:
		"""
		Assert that ``obj`` is of type ``expected_type``, otherwise raise an error with a helpful message.

		:param obj: The object to check the type of.
		:param expected_type: The expected type.
		:param path: The elements of the path to ``obj`` in the TOML mapping.
		:param what: What ``obj`` is, e.g. ``'type'``, ``'key type'``, ``'value type'``.

		.. seealso:: :meth:`~.assert_key_type` and :meth:`~.assert_value_type`
		"""

		if not isinstance(obj, expected_type):
			name = construct_path(path)
			raise TypeError(f"Invalid {what} for {name!r}: expected {expected_type!r}, got {type(obj)!r}")

	@staticmethod
	def assert_indexed_type(
			obj: Any,
			expected_type: Type,
			path: Iterable[str],
			idx: int = 0,
			) -> None:
		"""
		Assert that ``obj`` is of type ``expected_type``, otherwise raise an error with a helpful message.

		:param obj: The object to check the type of.
		:param expected_type: The expected type.
		:param path: The elements of the path to ``obj`` in the TOML mapping.
		:param idx: The index of ``obj`` in the array.

		.. seealso:: :meth:`~.assert_type`, :meth:`~.assert_key_type` and :meth:`~.assert_value_type`
		"""

		if not isinstance(obj, expected_type):
			name = construct_path(path) + f"[{idx}]"
			raise TypeError(f"Invalid type for {name!r}: expected {expected_type!r}, got {type(obj)!r}")

	def assert_key_type(self, obj: Any, expected_type: Type, path: Iterable[str]):
		"""
		Assert that the key ``obj`` is of type ``expected_type``, otherwise raise an error with a helpful message.

		:param obj: The object to check the type of.
		:param expected_type: The expected type.
		:param path: The elements of the path to ``obj`` in the TOML mapping.

		.. seealso:: :meth:`~.assert_type` and :meth:`~.assert_value_type`
		"""

		self.assert_type(obj, expected_type, path, "key type")

	def assert_value_type(self, obj: Any, expected_type: Type, path: Iterable[str]):
		"""
		Assert that the value ``obj`` is of type ``expected_type``, otherwise raise an error with a helpful message.

		:param obj: The object to check the type of.
		:param expected_type: The expected type.
		:param path: The elements of the path to ``obj`` in the TOML mapping.

		.. seealso:: :meth:`~.assert_type` and :meth:`~.assert_key_type`
		"""

		self.assert_type(obj, expected_type, path, "value type")

	@property
	@abstractmethod
	def keys(self) -> List[str]:
		"""
		The keys to parse from the TOML file.
		"""

		raise NotImplementedError

	def parse(self, config: Dict[str, TOML_TYPES]) -> Dict[str, TOML_TYPES]:
		"""
		Parse the TOML configuration.

		:param config:
		"""

		parsed_config = {}

		for key in self.keys:
			if key not in config:
				# Ignore absent values
				pass

			elif hasattr(self, f"parse_{key.replace('-', '_')}"):
				parsed_config[key] = getattr(self, f"parse_{key.replace('-', '_')}")(config)

			elif key in config:
				parsed_config[key] = config[key]

		return parsed_config


class PEP621Parser(AbstractConfigParser):
	"""
	Parser for :pep:`621` metadata from ``pyproject.toml``.
	"""

	@staticmethod
	def parse_name(config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the `name <https://www.python.org/dev/peps/pep-0621/#name>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		normalized_name = normalize(config["name"])

		# https://packaging.python.org/specifications/core-metadata/#name
		if not name_re.match(normalized_name):
			raise BadConfigError("The value for 'project.name' is invalid.")

		return normalized_name

	@staticmethod
	def parse_version(config: Dict[str, TOML_TYPES]) -> Version:
		"""
		Parse the `version <https://www.python.org/dev/peps/pep-0621/#version>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		version = str(config["version"])

		try:
			return Version(str(version))
		except InvalidVersion as e:
			raise BadConfigError(str(e))

	def parse_description(self, config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the `description <https://www.python.org/dev/peps/pep-0621/#description>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		description = config["description"]

		self.assert_type(description, str, ["project", "description"])

		return description

	@staticmethod
	def parse_readme(config: Dict[str, TOML_TYPES]) -> Dict[str, str]:
		"""
		Parse the `readme <https://www.python.org/dev/peps/pep-0621/#readme>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		readme: Union[Dict, str] = config["readme"]

		if isinstance(readme, str):
			# path to readme_file
			readme_text, readme_content_type = read_readme(readme)
			return {"text": readme_text, "content-type": readme_content_type}

		elif isinstance(readme, dict):
			if "file" in readme and "text" in readme:
				raise BadConfigError(
						"The 'project.readme.file' and 'project.readme.text' keys "
						"are mutually exclusive."
						)

			elif "file" in readme:
				readme_encoding = readme.get("charset", "UTF-8")
				readme_text, readme_content_type = read_readme(readme["file"], readme_encoding)
				return {"text": readme_text, "content-type": readme_content_type}

			elif "text" in readme:
				if "content-type" not in readme:
					raise BadConfigError(
							"The 'project.readme.content-type' key must be provided "
							"when 'project.readme.text' is given."
							)
				elif readme["content-type"] not in {"text/markdown", "text/x-rst", "text/plain"}:
					raise BadConfigError(f"Unrecognised value for 'content-type': {readme['content-type']!r}")

				readme_encoding = readme.get("charset", "UTF-8")
				return {
						"text": readme["text"].encode(readme_encoding).decode("UTF-8"),
						"content-type": readme["content-type"]
						}

		raise TypeError(f"Unsupported type for 'project.readme': {type(readme)!r}")
		# return {"text": '', "content-type": "text/plain"}

	@staticmethod
	def parse_requires_python(config: Dict[str, TOML_TYPES]) -> Specifier:
		"""
		Parse the `requires-python <https://www.python.org/dev/peps/pep-0621/#requires-python>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		version = str(config["requires-python"])

		try:
			return SpecifierSet(str(version))
		except InvalidSpecifier as e:
			raise BadConfigError(str(e))

	@staticmethod
	def parse_license(config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the `license <https://www.python.org/dev/peps/pep-0621/#license>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		license = config["license"]  # noqa: A001  # pylint: disable=redefined-builtin

		if "text" in license and "file" in license:
			raise BadConfigError(
					"The 'project.license.file' and 'project.license.text' keys "
					"are mutually exclusive."
					)
		elif "text" in license:
			return str(license["text"])
		elif "file" in license:
			return PathPlus(license["file"]).read_text()
		else:
			raise BadConfigError("The 'project.license' table should contain one of 'text' or 'file'.")

	@staticmethod
	def _parse_authors(config: Dict[str, TOML_TYPES], key_name: str = "authors") -> List[Dict[str, Optional[str]]]:
		all_authors: List[Dict[str, Optional[str]]] = []

		for idx, author in enumerate(config[key_name]):
			name = author.get("name", None)
			email = author.get("email", None)

			if name is not None and ',' in name:
				raise BadConfigError(f"The 'project.{key_name}[{idx}].name' key cannot contain commas.")

			if email is not None:
				try:
					email = validate_email(email, check_deliverability=False).email
				except EmailSyntaxError as e:
					raise BadConfigError(f"Invalid email {email}: {e} ")

			all_authors.append({"name": name, "email": email})

		return all_authors

	def parse_authors(self, config: Dict[str, TOML_TYPES]) -> List[Dict[str, Optional[str]]]:
		"""
		Parse the `authors <https://www.python.org/dev/peps/pep-0621/#authors-maintainers>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		return self._parse_authors(config, "authors")

	def parse_maintainers(self, config: Dict[str, TOML_TYPES]) -> List[Dict[str, Optional[str]]]:
		"""
		Parse the `authors <https://www.python.org/dev/peps/pep-0621/#authors-maintainers>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		return self._parse_authors(config, "maintainers")

	def parse_keywords(self, config: Dict[str, TOML_TYPES]) -> List[str]:
		"""
		Parse the `keywords <https://www.python.org/dev/peps/pep-0621/#keywords>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		parsed_keywords = set()

		for idx, keyword in enumerate(config["keywords"]):
			self.assert_indexed_type(keyword, str, ["project", "keywords"], idx=idx)
			parsed_keywords.add(keyword)

		return natsorted(parsed_keywords, alg=ns.GROUPLETTERS)

	def parse_classifiers(self, config: Dict[str, TOML_TYPES]) -> List[str]:
		"""
		Parse the `classifiers <https://www.python.org/dev/peps/pep-0621/#classifiers>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		parsed_classifiers = set()

		for idx, keyword in enumerate(config["classifiers"]):
			self.assert_indexed_type(keyword, str, ["project", "classifiers"], idx=idx)
			parsed_classifiers.add(keyword)

		validate_classifiers(parsed_classifiers)

		return natsorted(parsed_classifiers)

	def parse_urls(self, config: Dict[str, TOML_TYPES]) -> Dict[str, str]:
		"""
		Parse the `urls <https://www.python.org/dev/peps/pep-0621/#urls>`_ table.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		parsed_urls = {}

		project_urls = config["urls"]

		self.assert_type(project_urls, dict, ["project", "urls"])

		for category, url in project_urls.items():
			self.assert_key_type(category, str, ["project", "urls", category])
			self.assert_value_type(url, str, ["project", "urls", category])

			parsed_urls[category] = str(URL(url))

		return parsed_urls

	def parse_scripts(self, config: Dict[str, TOML_TYPES]) -> Dict[str, str]:
		"""
		Parse the `scripts <https://www.python.org/dev/peps/pep-0621/#entry-points>`_ table.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		scripts = config["scripts"]

		self.assert_type(scripts, dict, ["project", "scripts"])

		for name, func in scripts.items():
			self.assert_key_type(name, str, ["project", "scripts", name])
			self.assert_value_type(func, str, ["project", "scripts", name])

		return scripts

	def parse_gui_scripts(self, config: Dict[str, TOML_TYPES]) -> Dict[str, str]:
		"""
		Parse the `gui-scripts <https://www.python.org/dev/peps/pep-0621/#entry-points>`_ table.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		gui_scripts = config["gui-scripts"]

		self.assert_type(gui_scripts, dict, ["project", "gui-scripts"])

		for name, func in gui_scripts.items():
			self.assert_key_type(name, str, ["project", "gui-scripts", name])
			self.assert_value_type(func, str, ["project", "gui-scripts", name])

		return gui_scripts

	def parse_entry_points(self, config: Dict[str, TOML_TYPES]) -> Dict[str, str]:
		"""
		Parse the `entry-points <https://www.python.org/dev/peps/pep-0621/#entry-points>`_ table.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""

		entry_points = config["entry-points"]

		self.assert_type(entry_points, dict, ["project", "entry-points"])

		for group, sub_table in entry_points.items():

			self.assert_key_type(group, str, ["project", "entry-points", group])
			self.assert_value_type(sub_table, dict, ["project", "entry-points", group])

			for name, func in sub_table.items():
				self.assert_key_type(name, str, ["project", "entry-points", group, name])
				self.assert_value_type(func, str, ["project", "entry-points", group, name])

		return entry_points

	def parse_dependencies(self, config: Dict[str, TOML_TYPES]) -> List[ComparableRequirement]:
		"""
		Parse the
		`dependencies <https://www.python.org/dev/peps/pep-0621/#dependencies-optional-dependencies>`_ key.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""  # noqa: D400

		parsed_dependencies = set()

		for idx, keyword in enumerate(config["dependencies"]):
			self.assert_indexed_type(keyword, str, ["project", "dependencies"], idx=idx)
			parsed_dependencies.add(ComparableRequirement(keyword))

		return sorted(combine_requirements(parsed_dependencies))

	@staticmethod
	def parse_optional_dependencies(config: Dict[str, TOML_TYPES]) -> Dict[str, List[ComparableRequirement]]:
		"""
		Parse the
		`optional-dependencies <https://www.python.org/dev/peps/pep-0621/#dependencies-optional-dependencies>`_ table.

		:param config: The unparsed TOML config for the ``[project]`` table.
		"""  # noqa: D400

		parsed_optional_dependencies = defaultdict(set)

		optional_dependencies = config["optional-dependencies"]

		if not isinstance(optional_dependencies, dict):
			raise TypeError(
					f"Invalid type for 'project.optional-dependencies': expected {dict!r}, got {type(optional_dependencies)!r}"
					)

		for extra, dependencies in optional_dependencies.items():
			for idx, keyword in enumerate(dependencies):
				if not isinstance(keyword, str):
					raise TypeError(
							f"Invalid type for 'project.optional-dependencies.{extra}[{idx}]': expected {str!r}, got {type(keyword)!r}"
							)
				else:
					parsed_optional_dependencies[extra].add(ComparableRequirement(keyword))

		return {e: sorted(combine_requirements(d)) for e, d in parsed_optional_dependencies.items()}

	@property
	def keys(self) -> List[str]:
		"""
		The keys to parse from the TOML file.
		"""

		return [
				"name",
				"version",
				"description",
				"readme",
				"requires-python",
				"license",
				"authors",
				"maintainers",
				"keywords",
				"classifiers",
				"urls",
				"scripts",
				"gui-scripts",
				"entry-points",
				"dependencies",
				"optional-dependencies",
				]

	def parse(self, config: Dict[str, TOML_TYPES]) -> Dict[str, TOML_TYPES]:
		"""
		Parse the TOML configuration.

		:param config:
		"""

		dynamic_fields = config.get("dynamic", [])

		parsed_config = {"dynamic": dynamic_fields}

		if "name" in dynamic_fields:
			raise BadConfigError("The 'project.name' field may not be dynamic.")
		elif "name" not in config:
			raise BadConfigError("The 'project.name' field must be provided.")

		if dynamic_fields:
			# TODO: Support the remaining fields as dynamic

			supported_dynamic = ("classifiers", "requires-python", "dependencies")

			if any(f not in supported_dynamic for f in dynamic_fields):
				supported = word_join(supported_dynamic, oxford=True, use_repr=True)
				raise BadConfigError(f"whey only supports {supported} as dynamic fields.")

		if "version" not in config:
			raise BadConfigError("The 'project.version' field must be provided.")

		for key in self.keys:

			if key in config and key in dynamic_fields:
				raise BadConfigError(f"{key!r} was listed in 'project.dynamic-fields' but a value was given.")
			elif key not in config:
				# Ignore absent values
				pass
			elif hasattr(self, f"parse_{key.replace('-', '_')}"):
				parsed_config[key] = getattr(self, f"parse_{key.replace('-', '_')}")(config)
			elif key in config:
				parsed_config[key] = config[key]

		return parsed_config


class WheyParser(AbstractConfigParser):
	"""
	Parser for the ``[tool.whey]`` table from ``pyproject.toml``.
	"""

	def parse_package(self, config: Dict[str, TOML_TYPES]) -> str:
		"""
		Parse the ``package`` key, giving the name of the importable package.

		This defaults to `project.name <https://www.python.org/dev/peps/pep-0621/#name>`_ if unspecified.

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""

		package = config["package"]

		self.assert_type(package, str, ["tool", "whey", "package"])

		return package

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
		Parse the ``additional-files`` key,
		giving `MANIFEST.in <https://packaging.python.org/guides/using-manifest-in/>`_-style
		entries for additional files to include in distributions.

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
						f"Invalid type for 'tool.whey.python-versions[{idx}]': expected {str!r}, {int!r} or {float!r}, got {type(version)!r}"
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
		"""

		python_implementations = config["python-implementations"]

		for idx, impl in enumerate(python_implementations):
			self.assert_indexed_type(impl, str, ["tool", "whey", "python-implementations"], idx=idx)

		return python_implementations

	def parse_base_classifiers(self, config: Dict[str, TOML_TYPES]) -> Set[str]:
		"""
		Parse the ``base-classifiers`` key, giving a list `trove classifiers <https://pypi.org/classifiers/>`_.

		This list will be extended with the appropriate classifiers for supported platforms,
		Python versions and implementations, and the project's license.
		Ignored if `classifiers <https://www.python.org/dev/peps/pep-0621/#classifiers>`_
		is not listed in `dynamic <https://www.python.org/dev/peps/pep-0621/#dynamic>`_

		:param config: The unparsed TOML config for the ``[tool.whey]`` table.
		"""

		parsed_classifiers = set()

		for idx, classifier in enumerate(config["base-classifiers"]):
			self.assert_indexed_type(classifier, str, ["tool", "whey", "python-implementations"], idx=idx)
			parsed_classifiers.add(classifier)

		return parsed_classifiers

	@property
	def keys(self) -> List[str]:
		"""
		The keys to parse from the TOML file.
		"""

		return [
				"package",
				"additional-files",
				"license-key",
				"base-classifiers",
				"platforms",
				"python-versions",
				"python-implementations",
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


def load_toml(filename: PathLike):
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
	parsed_config.setdefault("package", config["project"]["name"].replace('.', '/'))
	parsed_config.setdefault("additional-files", [])
	parsed_config.setdefault("license-key", None)
	parsed_config.setdefault("base-classifiers", [])
	parsed_config.setdefault("platforms", None)
	parsed_config.setdefault("python-versions", None)
	parsed_config.setdefault("python-implementations", None)

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
