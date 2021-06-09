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
from typing import Optional

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
from consolekit.terminal_colours import ColourTrilean
from consolekit.tracebacks import handle_tracebacks, traceback_option
from domdf_python_tools.typing import PathLike

__all__ = ["main"]


@colour_option()
@traceback_option()
@flag_option("-v", "--verbose", help="Enable verbose output.")
@auto_default_option("-o", "--out-dir", type=click.STRING, help="The output directory.")
@auto_default_option("--build-dir", type=click.STRING, help="The temporary build directory.")
@flag_option("-b", "--binary", help="Build a binary distribution.")
@flag_option("-w", "--wheel", help="Build a wheel.")
@flag_option("-s", "--sdist", help="Build a sdist distribution.")
@auto_default_argument(
		"project",
		type=click.STRING,
		cls=DescribedArgument,
		description="The path to the project to build.",
		)
@click_command()
def main(
		project: PathLike = '.',
		build_dir: Optional[str] = None,
		out_dir: Optional[str] = None,
		sdist: bool = False,
		wheel: bool = False,
		binary: bool = False,
		verbose: bool = False,
		colour: ColourTrilean = None,
		show_traceback: bool = False,
		):
	"""
	Build a wheel for the given project.
	"""

	# 3rd party
	from domdf_python_tools.paths import PathPlus
	from pyproject_parser.cli import ConfigTracebackHandler

	# this package
	from whey.foreman import Foreman

	if not binary and not sdist and not wheel:
		wheel = True
		sdist = True

	project = PathPlus(project).resolve()

	with handle_tracebacks(show_traceback, ConfigTracebackHandler):
		foreman = Foreman(project_dir=project)

		if verbose:
			click.echo("Using the following builders:")

			for builder_name, builder_obj in foreman.config["builders"].items():
				click.echo(f"    {builder_name}: {builder_obj.__module__}.{builder_obj.__qualname__}")

			click.echo()

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


if __name__ == "__main__":
	sys.exit(main())
