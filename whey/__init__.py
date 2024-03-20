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

# stdlib
import os

__author__: str = "Dominic Davis-Foster"
__copyright__: str = "2021 Dominic Davis-Foster"
__license__: str = "MIT License"
__version__: str = "0.0.25"
__email__: str = "dominic@davis-foster.co.uk"

__all__ = ("build_sdist", "build_wheel")


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None) -> str:  # noqa: MAN001
	"""
	:pep:`517` hook to build a wheel binary distribution.

	.. seealso:: https://www.python.org/dev/peps/pep-0517/#build-wheel

	:param wheel_directory:
	:param config_settings:
	:param metadata_directory:

	:returns: The filename of the created archive.
	"""

	# 3rd party
	from consolekit.tracebacks import handle_tracebacks
	from domdf_python_tools.paths import PathPlus, TemporaryPathPlus

	# this package
	from whey.foreman import Foreman
	from whey.utils import WheyBackendTBHandler

	show_traceback = bool(int(os.getenv("WHEY_TRACEBACK", 0)))
	verbose = bool(int(os.getenv("WHEY_VERBOSE", 1)))

	with TemporaryPathPlus() as tmpdir, handle_tracebacks(show_traceback, WheyBackendTBHandler):
		foreman = Foreman(project_dir=PathPlus.cwd())
		return foreman.build_wheel(build_dir=tmpdir, out_dir=wheel_directory, verbose=verbose)


def build_sdist(sdist_directory, config_settings=None) -> str:  # noqa: MAN001
	"""
	:pep:`517` hook to build a source distribution.

	.. seealso:: https://www.python.org/dev/peps/pep-0517/#build-sdist

	:param sdist_directory:
	:param config_settings:

	:returns: The filename of the created archive.
	"""

	# 3rd party
	from consolekit.tracebacks import handle_tracebacks
	from domdf_python_tools.paths import PathPlus, TemporaryPathPlus

	# this package
	from whey.foreman import Foreman
	from whey.utils import WheyBackendTBHandler

	show_traceback = bool(int(os.getenv("WHEY_TRACEBACK", 0)))
	verbose = bool(int(os.getenv("WHEY_VERBOSE", 1)))

	with TemporaryPathPlus() as tmpdir, handle_tracebacks(show_traceback, WheyBackendTBHandler):
		foreman = Foreman(project_dir=PathPlus.cwd())
		return foreman.build_sdist(build_dir=tmpdir, out_dir=sdist_directory, verbose=verbose)


def get_requires_for_build_sdist(config_settings=None):  # pragma: no cover  # noqa: MAN001,MAN002
	return []


def get_requires_for_build_editable(config_settings=None):  # pragma: no cover  # noqa: MAN001,MAN002
	return ["editables>=0.2"]


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):  # noqa: MAN001,MAN002
	"""
	:pep:`517` hook to build an editable wheel.

	.. seealso:: :pep:`660`

	:param wheel_directory:
	:param config_settings:
	:param metadata_directory:
	"""

	# stdlib
	from typing import Type, cast

	# 3rd party
	from consolekit.tracebacks import handle_tracebacks
	from domdf_python_tools.paths import PathPlus, TemporaryPathPlus

	# this package
	from whey.builder import WheelBuilder
	from whey.foreman import Foreman
	from whey.utils import WheyBackendTBHandler

	show_traceback = bool(int(os.getenv("WHEY_TRACEBACK", 0)))
	verbose = bool(int(os.getenv("WHEY_VERBOSE", 1)))

	with TemporaryPathPlus() as tmpdir, handle_tracebacks(show_traceback, WheyBackendTBHandler):
		foreman = Foreman(project_dir=PathPlus.cwd())
		builder_cls: Type[WheelBuilder] = cast(Type[WheelBuilder], foreman.get_builder("wheel"))
		builder = builder_cls(
				foreman.project_dir,
				foreman.config,
				build_dir=tmpdir,
				out_dir=wheel_directory,
				verbose=verbose,
				)
		return builder.build_editable()
