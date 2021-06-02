#!/usr/bin/env python3
#
#  foreman.py
"""
The foreman is responsible for loading the configuration calling the builders.
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
from typing import Optional, Type

# 3rd party
from domdf_python_tools.paths import PathPlus, traverse_to_file
from domdf_python_tools.typing import PathLike

# this package
from whey.builder import AbstractBuilder
from whey.config import load_toml

__all__ = ["Foreman"]


class Foreman:
	"""
	Responsible for loading the configuration calling the builders.
	"""

	def __init__(self, project_dir: PathLike):

		# Walk up the tree until a ``pyproject.toml`` file is found.
		#: The pyproject.toml directory
		self.project_dir: PathPlus = traverse_to_file(PathPlus(project_dir), "pyproject.toml")

		#: Configuration parsed from ``pyproject.toml``.
		self.config = load_toml(self.project_dir / "pyproject.toml")

	def get_builder(self, distribution_type: str) -> Type[AbstractBuilder]:
		"""
		Returns the builder for the given distribution type.

		:param distribution_type: The distribution type, such as ``'source'`` or ``'wheel'``.
		"""

		return self.config["builders"][distribution_type]

	def build_sdist(
			self,
			build_dir: Optional[PathLike] = None,
			out_dir: Optional[PathLike] = None,
			*args,
			verbose: bool = False,
			colour: bool = None,
			**kwargs,
			):
		"""
		Build a sdist distribution using the ``sdist`` builder configured in ``pyproject.toml``.

		:returns: The filename of the created archive.
		"""

		builder = self.get_builder("sdist")(  # type: ignore
			self.project_dir,
			self.config,
			build_dir,
			out_dir,
			*args,
			verbose=verbose,
			colour=colour,
			**kwargs,
			)
		return builder.build()

	def build_binary(
			self,
			build_dir: Optional[PathLike] = None,
			out_dir: Optional[PathLike] = None,
			*args,
			verbose: bool = False,
			colour: bool = None,
			**kwargs,
			):
		"""
		Build a binary distribution using the ``binary`` builder configured in ``pyproject.toml``.

		:returns: The filename of the created archive.
		"""

		builder = self.get_builder("binary")(  # type: ignore
			self.project_dir,
			self.config,
			build_dir,
			out_dir,
			*args,
			verbose=verbose,
			colour=colour,
			**kwargs,
			)
		return builder.build()

	def build_wheel(
			self,
			build_dir: Optional[PathLike] = None,
			out_dir: Optional[PathLike] = None,
			*args,
			verbose: bool = False,
			colour: bool = None,
			**kwargs,
			):
		"""
		Build a wheel distribution using the ``wheel`` builder configured in ``pyproject.toml``.

		:returns: The filename of the created archive.
		"""

		builder = self.get_builder("wheel")(  # type: ignore
			self.project_dir,
			self.config,
			build_dir,
			out_dir,
			*args,
			verbose=verbose,
			colour=colour,
			**kwargs,
			)
		return builder.build()
