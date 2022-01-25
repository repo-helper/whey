#!/usr/bin/env python
#
#  _editable.py
"""
Internal plumbing for editable installs.
"""
#
#  Copyright © 2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  `map` method adapted from https://github.com/pfmoore/editables
#  Copyright © 2020 Paul Moore
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
from pathlib import Path
from typing import Dict, List

# 3rd party
import editables  # type: ignore[import]  # nodep
from domdf_python_tools.typing import PathLike

__all__ = ["EditableProject"]


class EditableProject(editables.EditableProject):  # noqa: D101
	project_name: str
	project_dir: Path
	redirections: Dict[str, str]
	path_entries: List[Path]

	def map(self, name: str, target: PathLike) -> None:  # noqa: A003,D102  # pylint: disable=redefined-builtin
		if '.' in name:
			raise editables.EditableException(f"Cannot map {name} as it is not a top-level package")

		abs_target = self.make_absolute(target)

		if abs_target.is_dir():
			abs_target = abs_target / "__init__.py"

		if abs_target.is_file():
			self.redirections[name] = abs_target.as_posix()
		else:
			raise editables.EditableException(f"{target} is not a valid Python package or module")

	def map_or_add_to_path(self, name: str, pkgdir: Path) -> None:
		"""
		``.map`` a conventional package, or ``.add_to_path`` a :pep:`420` namespace package.

		:param name: The package name.
		:param pkgdir: The package directory.
		"""

		if (pkgdir / "__init__.py").is_file():
			self.map(name, pkgdir)
		else:
			# namespace package
			self.add_to_path(pkgdir.parent)
