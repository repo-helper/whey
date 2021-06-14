#!/usr/bin/env python3
#
#  __init__.py
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

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.0.15"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = ["build_sdist", "build_wheel"]


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
	"""
	:pep:`517` hook to build a wheel binary distribution.

	.. seealso:: https://www.python.org/dev/peps/pep-0517/#build-wheel

	:param wheel_directory:
	:param config_settings:
	:param metadata_directory:
	"""

	# 3rd party
	from domdf_python_tools.paths import PathPlus, TemporaryPathPlus

	# this package
	from whey.foreman import Foreman

	with TemporaryPathPlus() as tmpdir:
		foreman = Foreman(project_dir=PathPlus.cwd())
		return foreman.build_wheel(build_dir=tmpdir, out_dir=wheel_directory, verbose=True)


def build_sdist(sdist_directory, config_settings=None):
	"""
	:pep:`517` hook to build a source distribution.

	.. seealso:: https://www.python.org/dev/peps/pep-0517/#build-sdist

	:param sdist_directory:
	:param config_settings:
	"""

	# 3rd party
	from domdf_python_tools.paths import PathPlus, TemporaryPathPlus

	# this package
	from whey.foreman import Foreman

	with TemporaryPathPlus() as tmpdir:
		foreman = Foreman(project_dir=PathPlus.cwd())
		return foreman.build_sdist(build_dir=tmpdir, out_dir=sdist_directory, verbose=True)


def get_requires_for_build_sdist(config_settings=None):  # pragma: no cover
	return []
