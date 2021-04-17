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
from typing import Dict, cast

# 3rd party
import pyproject_parser.parsers
from dom_toml.parser import TOML_TYPES, BadConfigError
from domdf_python_tools.words import word_join
from pyproject_parser.type_hints import ProjectDict

__all__ = ["PEP621Parser"]


class PEP621Parser(pyproject_parser.parsers.PEP621Parser, inherit_defaults=True):
	"""
	Parser for :pep:`621` metadata from ``pyproject.toml``.
	"""

	defaults = {
			"description": None,
			"readme": None,
			"requires-python": None,
			"license": None,
			}

	def _parse(
			self,
			config: Dict[str, TOML_TYPES],
			set_defaults: bool = False,
			) -> ProjectDict:

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

		return cast(ProjectDict, parsed_config)

	def parse(  # type: ignore[override]
		self,
		config: Dict[str, TOML_TYPES],
		set_defaults: bool = False,
		) -> ProjectDict:
		"""
		Parse the TOML configuration.

		:param config:
		:param set_defaults: If :py:obj:`True`, the values in
			:attr:`dom_toml.parser.AbstractConfigParser.defaults` and
			:attr:`dom_toml.parser.AbstractConfigParser.factories`
			will be set as defaults for the returned mapping.
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
