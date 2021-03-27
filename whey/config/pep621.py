#!/usr/bin/env python3
#
#  pep621.py
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
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union

# 3rd party
from apeye import URL
from dom_toml.parser import TOML_TYPES, AbstractConfigParser, BadConfigError
from domdf_python_tools.paths import PathPlus
from domdf_python_tools.typing import PathLike
from domdf_python_tools.words import word_join
from email_validator import EmailSyntaxError, validate_email  # type: ignore
from natsort import natsorted, ns
from packaging.specifiers import InvalidSpecifier, Specifier, SpecifierSet
from packaging.version import InvalidVersion, Version
from shippinglabel import normalize
from shippinglabel.classifiers import validate_classifiers
from shippinglabel.requirements import ComparableRequirement, combine_requirements

__all__ = [
		"PEP621Parser",
		"read_readme",
		]

try:

	# 3rd party
	import readme_renderer.markdown  # type: ignore
	import readme_renderer.rst  # type: ignore

	def render_rst(content: str):
		readme_renderer.rst.render(content)

	def render_markdown(content: str):
		readme_renderer.markdown.render(content)

except ImportError:  # pragma: no cover

	def render_rst(content: str):
		pass

	def render_markdown(content: str):
		pass


name_re = re.compile("^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", flags=re.IGNORECASE)


def read_readme(readme_file: PathLike, encoding="UTF-8") -> Tuple[str, str]:
	"""
	Reads the readme file and returns the content of the file and its content type.

	:param readme_file:
	:param encoding:
	"""

	readme_file = PathPlus(readme_file)

	if readme_file.suffix.lower() == ".md":
		content = readme_file.read_text(encoding=encoding)
		render_markdown(content)
		return content, "text/markdown"
	elif readme_file.suffix.lower() == ".rst":
		content = readme_file.read_text(encoding=encoding)
		render_rst(content)
		return content, "text/x-rst"
	elif readme_file.suffix.lower() == ".txt":
		return readme_file.read_text(encoding=encoding), "text/plain"
	else:
		raise BadConfigError(f"Unrecognised filetype for '{readme_file!s}'")


class PEP621Parser(AbstractConfigParser):
	"""
	Parser for :pep:`621` metadata from ``pyproject.toml``.
	"""

	defaults = {"description": None, "readme": None, "requires-python": None}
	factories = {
			"authors": list,
			"maintainers": list,
			"keywords": list,
			"classifiers": list,
			"urls": dict,
			"scripts": dict,
			"gui-scripts": dict,
			"entry-points": dict,
			"dependencies": list,
			"optional-dependencies": dict,
			}

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
			if not readme:
				raise BadConfigError("The 'project.readme' table cannot be empty.")

			if "file" in readme and "text" in readme:
				raise BadConfigError(
						"The 'project.readme.file' and 'project.readme.text' keys "
						"are mutually exclusive."
						)

			elif set(readme.keys()) == {"file"}:
				readme_encoding = readme.get("charset", "UTF-8")
				readme_text, readme_content_type = read_readme(readme["file"], readme_encoding)
				return {"text": readme_text, "content-type": readme_content_type}

			elif "content-type" in readme and "text" not in readme:
				raise BadConfigError(
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too."
						)

			elif "charset" in readme and "text" not in readme:
				raise BadConfigError(
						"The 'project.readme.charset' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too."
						)

			elif "text" in readme:
				if "content-type" not in readme:
					raise BadConfigError(
							"The 'project.readme.content-type' key must be provided "
							"when 'project.readme.text' is given."
							)
				elif readme["content-type"] not in {"text/markdown", "text/x-rst", "text/plain"}:
					raise BadConfigError(
							f"Unrecognised value for 'project.readme.content-type': {readme['content-type']!r}"
							)

				readme_encoding = readme.get("charset", "UTF-8")
				return {
						"text": readme["text"].encode(readme_encoding).decode("UTF-8"),
						"content-type": readme["content-type"]
						}

			else:
				raise BadConfigError(f"Unknown format for 'project.readme': {readme!r}")

		raise TypeError(f"Unsupported type for 'project.readme': {type(readme)!r}")

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

			self.assert_value_type(sub_table, dict, ["project", "entry-points", group])

			for name, func in sub_table.items():
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

		err_template = (
				f"Invalid type for 'project.optional-dependencies{{idx_string}}': "
				f"expected {dict!r}, got {{actual_type!r}}"
				)

		optional_dependencies = config["optional-dependencies"]

		if not isinstance(optional_dependencies, dict):
			raise TypeError(err_template.format('', type(optional_dependencies)))

		for extra, dependencies in optional_dependencies.items():
			for idx, dep in enumerate(dependencies):
				if isinstance(dep, str):
					parsed_optional_dependencies[extra].add(ComparableRequirement(dep))
				else:
					raise TypeError(err_template.format(f'{extra}[{idx}]', type(dep)))

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

	def _parse(
			self,
			config: Dict[str, TOML_TYPES],
			set_defaults: bool = False,
			) -> Dict[str, TOML_TYPES]:

		dynamic_fields = config.get("dynamic", [])
		parsed_config = {"dynamic": dynamic_fields}

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

		if set_defaults:
			for key, value in self.defaults.items():
				parsed_config.setdefault(key, value)

			for key, factory in self.factories.items():
				value = factory()
				parsed_config.setdefault(key, value)

		return parsed_config

	def parse(
			self,
			config: Dict[str, TOML_TYPES],
			set_defaults: bool = False,
			) -> Dict[str, TOML_TYPES]:
		"""
		Parse the TOML configuration.

		:param config:
		:param set_defaults: If :py:obj:`True`, the values in :attr:`.AbstractConfigParser.defaults`
			and :attr:`.AbstractConfigParser.factories` will be set as defaults for the returned mapping.
		"""

		dynamic_fields = config.get("dynamic", [])

		if "name" in dynamic_fields:
			raise BadConfigError("The 'project.name' field may not be dynamic.")
		elif "name" not in config:
			raise BadConfigError("The 'project.name' field must be provided.")

		if dynamic_fields:
			# TODO: Support the remaining fields as dynamic
			# TODO: dynamic version numbers by parsing AST for __version__ in __init__.py

			supported_dynamic = ("classifiers", "requires-python", "dependencies")

			if any(f not in supported_dynamic for f in dynamic_fields):
				supported = word_join(supported_dynamic, oxford=True, use_repr=True)
				raise BadConfigError(f"whey only supports {supported} as dynamic fields.")

		if "version" not in config:
			raise BadConfigError("The 'project.version' field must be provided.")

		return self._parse(config, set_defaults)
