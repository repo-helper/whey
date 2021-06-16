#!/usr/bin/env python3
#
#  utils.py
"""
General utilities.
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
from typing import Dict, Iterable, Optional, Type

# 3rd party
import click
from consolekit.utils import abort
from domdf_python_tools.words import Plural
from packaging.requirements import InvalidRequirement
from pyproject_parser.cli import ConfigTracebackHandler

# this package
from whey.builder import AbstractBuilder
from whey.config.whey import get_entry_points

__all__ = ["WheyTracebackHandler", "parse_custom_builders", "print_builder_names"]

# this package
from whey.foreman import Foreman

_builder = Plural("builder", "builders")


class WheyTracebackHandler(ConfigTracebackHandler):
	"""
	Custom :class:`consolekit.tracebacks.TracebackHandler` which handles :exc:`dom_toml.parser.BadConfigError`
	and :exc:`packaging.requirements.InvalidRequirement`.
	"""  # noqa: D400

	def handle_InvalidRequirement(self, e: InvalidRequirement) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}", colour=False)


def parse_custom_builders(builders: Optional[Iterable[str]]) -> Dict[str, Type[AbstractBuilder]]:
	"""
	Parse the custom builders passed using the ``--builder NAME`` option on the command line.

	:param builders:
	"""

	custom_builders: Dict[str, Type[AbstractBuilder]] = {}

	if builders is None:
		return custom_builders

	entry_points = get_entry_points()
	for builder_name in builders:
		if builder_name not in entry_points:
			raise click.BadArgumentUsage(
					f"Unknown builder {builder_name!r}. \n"
					f"Is it registered as an entry point under 'whey.builder'?"
					)
		else:
			custom_builders[builder_name] = entry_points[builder_name].load()

	return custom_builders


def print_builder_names(foreman: Foreman, custom_builders: Dict[str, Type[AbstractBuilder]], **opts: bool):
	"""
	Prints the name(s) of the builders which will be used.

	:param foreman:
	:param custom_builders:
	:param opts: Keyword arguments for builder categories.
		Corresponds to the ``--sdist``, ``--wheel`` and ``--binary`` options.
	"""

	builders = []

	for builder_name, enabled in opts.items():
		if enabled:
			builder_obj = foreman.config["builders"][builder_name]
			builders.append(f"    {builder_name}: {builder_obj.__module__}.{builder_obj.__qualname__}")

	for builder_name, builder_obj in custom_builders.items():
		builders.append(f"    {builder_name}: {builder_obj.__module__}.{builder_obj.__qualname__}")

	click.echo(f"Using the following {_builder(len(builders))}:")

	for line in builders:
		click.echo(line)

	click.echo()
