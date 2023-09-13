#!/usr/bin/env python
#
#  additional_files.py
"""
Parser for the ``additional-files`` option.
"""
#
#  Copyright © 2020-2023 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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
import abc
from typing import Any, Dict, Iterable, Iterator, List, Optional
from warnings import warn

# 3rd party
import attr
from dom_toml.parser import BadConfigError
from domdf_python_tools.paths import PathPlus, sort_paths

__all__ = ["AdditionalFilesEntry", "Exclude", "Include", "RecursiveExclude", "RecursiveInclude", "from_entry"]


class AdditionalFilesEntry(abc.ABC):
	"""
	An abstract command in ``additional-files``.
	"""

	@classmethod
	@abc.abstractmethod
	def parse(cls, parameters: str) -> "AdditionalFilesEntry":
		"""
		Parse the command's parameters.

		:param parameters:
		"""

		raise NotImplementedError

	@abc.abstractmethod
	def iter_files(self, directory: PathPlus) -> Iterator[PathPlus]:
		"""
		Returns an iterator over files to be included or excluded by this command.

		:param directory: The project or build directory.
		"""

		raise NotImplementedError

	@abc.abstractmethod
	def to_dict(self) -> Dict[str, Any]:
		"""
		Returns a dictionary representation of the command entry.
		"""

		raise NotImplementedError


def _to_list(_: Iterable[str]) -> List[str]:
	return list(_)


@attr.define
class Include(AdditionalFilesEntry):
	"""
	Include a single file, or multiple files with a pattern.
	"""

	#: Glob patterns (with complete paths from the project root)
	patterns: List[str] = attr.field(converter=_to_list)

	@classmethod
	def parse(cls, parameters: str) -> "Include":
		"""
		Parse the command's parameters.

		:param parameters:
		"""

		if not parameters:
			raise BadConfigError(f"additional-files: 'include' must have at least one path or pattern specified.")

		return cls(parameters.split(' '))

	def iter_files(self, directory: PathPlus) -> Iterator[PathPlus]:
		"""
		Returns an iterator over files to be included by this command.

		:param directory: The project directory.
		"""

		for include_pat in self.patterns:
			for include_file in sorted(directory.glob(include_pat)):
				if include_file.is_file():
					yield include_file

	def to_dict(self) -> Dict[str, Any]:
		"""
		Returns a dictionary representation of the command entry.
		"""

		return {
				"command": "include",
				**attr.asdict(self),
				}


@attr.define
class Exclude(AdditionalFilesEntry):
	"""
	Exclude a single file, or multiple files with a pattern.
	"""

	#: Glob patterns (with complete paths from the project root)
	patterns: List[str] = attr.field(converter=_to_list)

	@classmethod
	def parse(cls, parameters: str) -> "Exclude":
		"""
		Parse the command's parameters.

		:param parameters:
		"""

		if not parameters:
			raise BadConfigError(f"additional-files: 'exclude' must have at least one path or pattern specified.")

		return cls(parameters.split(' '))

	def iter_files(self, directory: PathPlus) -> Iterator[PathPlus]:
		"""
		Returns an iterator over files to be excluded by this command.

		:param directory: The build directory.
		"""

		for exclude_pat in self.patterns:
			for exclude_file in sorted(directory.glob(exclude_pat)):
				if exclude_file.is_file():
					yield exclude_file

	def to_dict(self) -> Dict[str, Any]:
		"""
		Returns a dictionary representation of the command entry.
		"""

		return {
				"command": "exclude",
				**attr.asdict(self),
				}


@attr.define
class RecursiveInclude(AdditionalFilesEntry):
	"""
	Recursively include files in a directory based on patterns.
	"""

	#: The directory to start from.
	path: str

	#: Glob patterns.
	patterns: List[str] = attr.field(converter=_to_list)

	@classmethod
	def parse(cls, parameters: str) -> "RecursiveInclude":
		"""
		Parse the command's parameters.

		:param parameters:
		"""

		parts = parameters.split(' ')
		if len(parts) < 2:
			raise BadConfigError(
					f"additional-files: 'recursive-include' must have one path and at least one pattern specified."
					)

		return cls(parts[0], parts[1:])

	def iter_files(self, directory: PathPlus) -> Iterator[PathPlus]:
		"""
		Returns an iterator over files to be included by this command.

		:param directory: The project directory.
		"""

		for include_pat in self.patterns:
			for include_file in sort_paths(*(directory / self.path).rglob(include_pat)):
				if "__pycache__" in include_file.parts:
					continue

				if include_file.is_file():
					yield include_file

	def to_dict(self) -> Dict[str, Any]:
		"""
		Returns a dictionary representation of the command entry.
		"""

		return {
				"command": "recursive-include",
				**attr.asdict(self),
				}


@attr.define
class RecursiveExclude(AdditionalFilesEntry):
	"""
	Recursively exclude files in a directory based on patterns.
	"""

	#: The directory to start from.
	path: str

	#: Glob patterns.
	patterns: List[str] = attr.field(converter=_to_list)

	@classmethod
	def parse(cls, parameters: str) -> "RecursiveExclude":
		"""
		Parse the command's parameters.

		:param parameters:
		"""

		parts = parameters.split(' ')
		if len(parts) < 2:
			raise BadConfigError(
					f"additional-files: 'recursive-exclude' must have one path and at least one pattern specified."
					)

		return cls(parts[0], parts[1:])

	def iter_files(self, directory: PathPlus) -> Iterator[PathPlus]:
		"""
		Returns an iterator over files to be excluded by this command.

		:param directory: The build directory.
		"""
		for exclude_pat in self.patterns:
			for exclude_file in sort_paths(*(directory / self.path).rglob(exclude_pat)):
				if exclude_file.is_file():
					yield exclude_file

	def to_dict(self) -> Dict[str, Any]:
		"""
		Returns a dictionary representation of the command entry.
		"""

		return {
				"command": "recursive-exclude",
				**attr.asdict(self),
				}


def from_entry(line: str) -> Optional[AdditionalFilesEntry]:
	"""
	Parse a `MANIFEST.in`_-style entry.

	.. _MANIFEST.in: https://packaging.python.org/guides/using-manifest-in/

	:param line:

	:returns: An :class:`~.AdditionalFilesEntry` for known commands,
		or :py:obj:`None` if an unknown command is found in the entry.
	"""

	command, *parameters = line.split(' ')
	parameter_string = ' '.join(parameters)

	if command == "include":
		return Include.parse(parameter_string)
	elif command == "exclude":
		return Exclude.parse(parameter_string)
	elif command == "recursive-include":
		return RecursiveInclude.parse(parameter_string)
	elif command == "recursive-exclude":
		return RecursiveExclude.parse(parameter_string)
	else:  # pragma: no cover
		warn(f"Unsupported command in 'additional-files': {line}")
		return None
