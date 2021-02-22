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
from consolekit.options import colour_option, flag_option
from consolekit.terminal_colours import ColourTrilean
from domdf_python_tools.typing import PathLike

__all__ = ["main"]


@colour_option()
@flag_option("-v", "--verbose", help="Enable verbose output.")
@click.option("-o", "--out-dir", type=click.STRING, default=None, help="The output directory.")
@click.option("--build-dir", type=click.STRING, default=None, help="The temporary build directory.")
@flag_option("-b", "--binary", help="Build a binary wheel.")
@flag_option("-s", "--source", help="Build a source distribution.")
@click.argument("project", type=click.STRING, default='.')
@click_command()
def main(
		project: PathLike = '.',
		build_dir: Optional[str] = None,
		out_dir: Optional[str] = None,
		binary: bool = False,
		source: bool = False,
		verbose: bool = False,
		colour: ColourTrilean = None,
		):
	"""
	Build a wheel for the given project.
	"""

	# 3rd party
	from domdf_python_tools.paths import PathPlus

	# this package
	from whey.builder import SDistBuilder, WheelBuilder

	if not binary and not source:
		binary = True
		source = True

	project = PathPlus(project)

	if binary:
		wheel_builder = WheelBuilder(
				project_dir=project,
				build_dir=build_dir,
				out_dir=out_dir,
				verbose=verbose,
				colour=colour,
				)
		wheel_builder.build_wheel()

	if source:
		sdist_builder = SDistBuilder(
				project_dir=project,
				build_dir=build_dir,
				out_dir=out_dir,
				verbose=verbose,
				colour=colour,
				)
		sdist_builder.build_sdist()


if __name__ == "__main__":
	sys.exit(main())
