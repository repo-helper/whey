#!/usr/bin/env python3
#
#  __main__.py
"""
A simple Python wheel builder for simple projects.
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
import sys

# 3rd party
import click
from consolekit import click_command
from consolekit.options import (
		DescribedArgument,
		auto_default_argument,
		auto_default_option,
		colour_option,
		flag_option
		)
from consolekit.tracebacks import handle_tracebacks, traceback_option

if False:  # TYPE_CHECKING:
	# stdlib
	from typing import Iterable, Optional

	# 3rd party
	from consolekit.terminal_colours import ColourTrilean
	from domdf_python_tools.typing import PathLike

__all__ = ["main"]


@colour_option()
@traceback_option()
@flag_option("-S", "--show-builders", help="Show the builders which will be used, and exit.")
@flag_option("-v", "--verbose", help="Enable verbose output.")
@auto_default_option(
		"-o",
		"--out-dir",
		type=click.STRING,
		help="The output directory.",
		metavar="DIRECTORY",
		)
@auto_default_option(
		"--build-dir",
		type=click.STRING,
		help="The temporary build directory.",
		metavar="DIRECTORY",
		)
@auto_default_option(
		"-B",
		"--builder",
		type=click.STRING,
		help="The builder to build with.",
		multiple=True,
		metavar="BUILDER",
		)
@flag_option("-b", "--binary", help="Build a binary distribution.")
@flag_option("-w", "--wheel", help="Build a wheel.")
@flag_option("-s", "--sdist", help="Build a source distribution.")
@auto_default_argument(
		"project",
		type=click.STRING,
		cls=DescribedArgument,
		description="The path to the project to build.",
		)
@click_command()
def main(
		project: "PathLike" = '.',
		build_dir: "Optional[str]" = None,
		out_dir: "Optional[str]" = None,
		sdist: bool = False,
		wheel: bool = False,
		binary: bool = False,
		builder: "Optional[Iterable[str]]" = None,
		verbose: bool = False,
		colour: "ColourTrilean" = None,
		show_traceback: bool = False,
		show_builders: bool = False,
		):
	"""
	Build a wheel for the given project.
	"""

	# 3rd party
	from domdf_python_tools.paths import PathPlus

	# this package
	from whey.foreman import Foreman
	from whey.utils import WheyTracebackHandler, parse_custom_builders, print_builder_names

	if not any((binary, sdist, wheel, builder)):
		wheel = True
		sdist = True

	project = PathPlus(project).resolve()

	with handle_tracebacks(show_traceback, WheyTracebackHandler):
		foreman = Foreman(project_dir=project)

		custom_builders = parse_custom_builders(builder)

		if verbose or show_builders:
			print_builder_names(foreman, custom_builders, sdist=sdist, wheel=wheel, binary=binary)

		if show_builders:
			sys.exit(0)

		click.echo(f"Building {foreman.project_dir.as_posix()}")

		if wheel:
			foreman.build_wheel(
					build_dir=build_dir,
					out_dir=out_dir,
					verbose=verbose,
					colour=colour,
					)

		if sdist:
			foreman.build_sdist(
					build_dir=build_dir,
					out_dir=out_dir,
					verbose=verbose,
					colour=colour,
					)

		if binary:
			foreman.build_binary(
					build_dir=build_dir,
					out_dir=out_dir,
					verbose=verbose,
					colour=colour,
					)

		for custom_builder in custom_builders.values():
			custom_builder(
					foreman.project_dir,
					foreman.config,
					build_dir=build_dir,
					out_dir=out_dir,
					verbose=verbose,
					colour=colour,
					).build()


if __name__ == "__main__":
	sys.exit(main())
