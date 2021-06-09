#!/usr/bin/env python
#
#  builder.py
"""
The actual wheel builder.
"""
#
#  Copyright © 2020-2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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
import configparser
import os
import pathlib
import posixpath
import re
import shutil
import tarfile
import warnings
from abc import ABC, abstractmethod
from email.headerregistry import Address
from email.message import EmailMessage
from functools import partial
from io import StringIO
from typing import Any, Dict, Iterator, Mapping, Optional
from zipfile import ZipFile

# 3rd party
import click
import dom_toml
from consolekit.terminal_colours import Fore, resolve_color_default
from domdf_python_tools.paths import PathPlus, sort_paths, traverse_to_file
from domdf_python_tools.stringlist import StringList
from domdf_python_tools.typing import PathLike
from domdf_python_tools.words import word_join
from first import first
from shippinglabel.checksum import get_record_entry
from shippinglabel.requirements import ComparableRequirement, combine_requirements

__all__ = ["AbstractBuilder", "SDistBuilder", "WheelBuilder"]

archive_name_sub_re = re.compile(
		r"[^\w\d.]+",
		re.UNICODE,
		)


class AbstractBuilder(ABC):
	"""
	Abstract base class for builders of Python distributions using metadata read from ``pyproject.toml``.

	:param project_dir: The project to build the distribution for.
	:param build_dir: The (temporary) build directory.
	:default build_dir: :file:`{<project_dir>}/build/`
	:param out_dir: The output directory.
	:default out_dir: :file:`{<project_dir>}/dist/`
	:param verbose: Whether to enable verbose output.
	:param colour: Whether to use coloured output.

	.. autosummary-widths:: 1/2
		:html: 3/10

	.. autoclasssumm:: AbstractBuilder
		:autosummary-sections: Attributes

	.. latex:clearpage::

	.. autosummary-widths:: 7/16
		:html: 4/10

	.. autoclasssumm:: AbstractBuilder
		:autosummary-sections: Methods
	"""

	def __init__(
			self,
			project_dir: PathPlus,
			config: Mapping[str, Any],
			build_dir: Optional[PathLike] = None,
			out_dir: Optional[PathLike] = None,
			*,
			verbose: bool = False,
			colour: bool = None,
			):

		# Walk up the tree until a "pyproject.toml" file is found.
		#: The pyproject.toml directory
		self.project_dir: PathPlus = traverse_to_file(PathPlus(project_dir), "pyproject.toml")

		#: Configuration parsed from ``pyproject.toml``.
		self.config: Dict[str, Any] = dict(config)

		#: The archive name, without the tag
		self.archive_name = archive_name_sub_re.sub(
				'_',
				self.config["name"],
				) + f"-{self.config['version']}"

		#: The (temporary) build directory.
		self.build_dir = PathPlus(build_dir or self.default_build_dir)
		self.clear_build_dir()

		#: The output directory.
		self.out_dir = PathPlus(out_dir or self.default_out_dir)
		self.out_dir.maybe_make(parents=True)

		#: Whether to enable verbose output.
		self.verbose = verbose

		#: Whether to use coloured output.
		self.colour = resolve_color_default(colour)

		self._echo = partial(click.echo, color=self.colour)

	@property
	def default_build_dir(self) -> PathPlus:  # pragma: no cover
		"""
		Provides a default for the ``build_dir`` argument.
		"""

		return self.project_dir / "build"

	@property
	def default_out_dir(self) -> PathPlus:  # pragma: no cover
		"""
		Provides a default for the ``out_dir`` argument.
		"""

		return self.project_dir / "dist"

	def clear_build_dir(self) -> None:
		"""
		Clear the build directory of any residue from previous builds.
		"""

		if self.build_dir.is_dir():
			shutil.rmtree(self.build_dir)

		self.build_dir.maybe_make(parents=True)

	def iter_source_files(self) -> Iterator[PathPlus]:
		"""
		Iterate over the files in the source directory.
		"""

		pkgdir = self.project_dir / self.config["source-dir"] / self.config["package"]

		if not pkgdir.is_dir():
			raise FileNotFoundError(f"Package directory '{self.config['package']}' not found.")

		found_file = False

		for py_pattern in {"**/*.py", "**/*.pyi", "**/*.pyx", "**/py.typed"}:
			for py_file in pkgdir.rglob(py_pattern):
				if "__pycache__" not in py_file.parts:
					found_file = True
					yield py_file

		if not found_file:
			raise FileNotFoundError(f"No Python source files found in {pkgdir}")

	def copy_source(self) -> None:
		"""
		Copy source files into the build directory.
		"""

		for py_file in self.iter_source_files():
			target = self.build_dir / py_file.relative_to(self.project_dir / self.config["source-dir"])
			target.parent.maybe_make(parents=True)
			target.write_clean(py_file.read_text())
			self.report_copied(py_file, target)

	def _echo_if_v(self, *args, **kwargs):
		if self.verbose:
			self._echo(*args, **kwargs)

	def report_copied(self, source: pathlib.Path, target: pathlib.Path) -> None:
		"""
		Report that a file has been copied into the build directory.

		The format is::

			Copying {source} -> {target.relative_to(self.build_dir)}

		.. latex:vspace:: -5px

		:param source: The source file
		:param target: The file in the build directory.
		"""

		self._echo_if_v(
				f"Copying {source.resolve().as_posix()} -> {target.relative_to(self.build_dir).as_posix()}"
				)

	def report_removed(self, removed_file: pathlib.Path) -> None:
		"""
		Reports the removal of a file from the build directory.

		The format is::

			Removing {removed_file.relative_to(self.build_dir)}

		.. latex:vspace:: -5px

		:param removed_file:
		"""

		self._echo_if_v(f"Removing {removed_file.relative_to(self.build_dir).as_posix()}")

	def report_written(self, written_file: pathlib.Path) -> None:
		"""
		Report that a file has been written to the build directory.

		The format is::

			Writing {written_file.relative_to(self.build_dir)}

		.. latex:vspace:: -5px

		:param written_file:
		"""

		self._echo_if_v(f"Writing {written_file.relative_to(self.build_dir).as_posix()}")

	def copy_additional_files(self) -> None:
		"""
		Copy additional files to the build directory, as specified in the ``additional-files`` key.
		"""

		self.parse_additional_files(*self.config["additional-files"])

	def parse_additional_files(self, *entries: str) -> None:  # pylint: disable=useless-return
		r"""
		Copy additional files to the build directory, by parsing `MANIFEST.in`_-style entries.

		.. _MANIFEST.in: https://packaging.python.org/guides/using-manifest-in/

		:param \*entries:
		"""

		def copy_file(filename):
			target = self.build_dir / filename.relative_to(self.project_dir)
			target.parent.maybe_make(parents=True)
			shutil.copy2(src=filename, dst=target)
			self.report_copied(filename, target)

		for entry in entries:
			parts = entry.split(' ')

			if parts[0] == "include":
				for include_pat in parts[1:]:
					for include_file in sorted(self.project_dir.glob(include_pat)):
						if include_file.is_file():
							copy_file(filename=include_file)

			elif parts[0] == "exclude":
				for exclude_pat in parts[1:]:
					for exclude_file in sorted(self.build_dir.glob(exclude_pat)):
						if exclude_file.is_file():
							exclude_file.unlink()
							self.report_removed(exclude_file)

			elif parts[0] == "recursive-include":
				for include_file in sort_paths(*(self.project_dir / parts[1]).rglob(parts[2])):
					if "__pycache__" in include_file.parts:
						continue

					if include_file.is_file():
						copy_file(filename=include_file)

			elif parts[0] == "recursive-exclude":
				for exclude_file in sort_paths(*(self.build_dir / parts[1]).rglob(parts[2])):
					if exclude_file.is_file():
						exclude_file.unlink()
						self.report_removed(exclude_file)

			else:  # pragma: no cover
				warnings.warn(f"Unsupported command in 'additional-files': {entry}")

		#
		# elif parts[0] == "global-include":
		# 	for include_pat in parts[1:]:
		# 		for include_file in self.project_dir.rglob(include_pat):
		# 			if include_file.is_file():
		# 				copy_file(filename=include_file)
		#
		# elif parts[0] == "global-exclude":
		# 	for exclude_pat in parts[1:]:
		# 		for exclude_file in self.project_dir.rglob(exclude_pat):
		# 			if exclude_file.is_file():
		# 				exclude_file.unlink()
		# 				self.report_removed(exclude_file)

		#
		# elif parts[0] == "graft":
		# 	for graft_dir in self.project_dir.rglob(parts[1]):
		# 		for graft_file in graft_dir.rglob("*.*"):
		# 			if graft_file.is_file():
		# 				copy_file(graft_file)
		#
		# elif parts[0] == "prune":
		# 	for prune_dir in self.project_dir.rglob(parts[1]):
		# 		for prune_file in prune_dir.rglob("*.*"):
		# 			if prune_file.is_file():
		# 				prune_file.unlink()
		# 				self.report_removed(exclude_file)

		return

	def write_license(self, dest_dir: PathPlus, dest_filename: str = "LICENSE"):
		"""
		Write the ``LICENSE`` file.

		:param dest_dir: The directory to write the file into.
		:param dest_filename: The name of the file to write in ``dest_dir``.
		"""

		if self.config.get("license", None) is not None:
			target = dest_dir / dest_filename
			target.parent.maybe_make(parents=True)
			target.write_clean(self.config["license"].text)
			self.report_written(target)

	def write_metadata(self, metadata_file: PathPlus):
		"""
		Write `Core Metadata`_ to the given file.

		.. _Core Metadata: https://packaging.python.org/specifications/core-metadata

		:param metadata_file:
		"""

		metadata = EmailMessage()

		# TODO: metadata 2.2
		# Need to translate pep621 dynamic into core metadata field names
		metadata["Metadata-Version"] = "2.1"
		metadata["Name"] = self.config["name"]
		metadata["Version"] = str(self.config["version"])

		if self.config["description"] is not None:
			metadata["Summary"] = self.config["description"]

		author = []
		author_email = []
		maintainer = []
		maintainer_email = []

		for entry in self.config["authors"]:
			if entry["name"] and entry["email"]:
				address = Address(entry["name"], addr_spec=entry["email"])
				author_email.append(str(address))
			elif entry["email"]:
				author_email.append(entry["email"])
			elif entry["name"]:
				author.append(entry["name"])

		for entry in self.config["maintainers"]:
			if entry["name"] and entry["email"]:
				address = Address(entry["name"], addr_spec=entry["email"])
				author_email.append(str(address))
			elif entry["email"]:
				maintainer_email.append(entry["email"])
			elif entry["name"]:
				maintainer.append(entry["name"])

		# TODO: I'm not quite sure how PEP 621 expects a name for one author and the email for another to be handled.

		if author_email:
			metadata["Author-email"] = ", ".join(author_email)
		elif author:
			metadata["Author"] = word_join(author)

		if maintainer_email:
			metadata["Author-email"] = ", ".join(maintainer_email)
		elif maintainer:
			metadata["Author"] = word_join(maintainer)

		if self.config["license-key"] is not None:
			metadata["License"] = self.config["license-key"]

		if self.config["keywords"]:
			metadata["Keywords"] = ','.join(self.config["keywords"])

		seen_hp = False

		for category, url in self.config["urls"].items():
			if category.lower() in {"homepage", "home page"} and not seen_hp:
				metadata["Home-page"] = url
				seen_hp = True
			else:
				metadata["Project-URL"] = f"{category}, {url}"

		for platform in (self.config.get("platforms", None) or ()):
			metadata["Platform"] = platform

		for classifier in self.config["classifiers"]:
			metadata["Classifier"] = classifier

		if self.config["requires-python"]:
			metadata["Requires-Python"] = str(self.config["requires-python"])

		for requirement in self.config["dependencies"]:
			metadata["Requires-Dist"] = str(requirement)

		for extra, requirements in self.config["optional-dependencies"].items():
			metadata["Provides-Extra"] = extra
			for requirement in requirements:
				requirement = ComparableRequirement(str(requirement))

				if requirement.marker:
					requirement.marker = f"({requirement.marker!s}) and extra == {extra!r}"
				else:
					requirement.marker = f"extra == {extra!r}"

				metadata["Requires-Dist"] = str(requirement)

		# TODO:
		#  https://packaging.python.org/specifications/core-metadata/#requires-external-multiple-use
		#  https://packaging.python.org/specifications/core-metadata/#provides-dist-multiple-use
		#  https://packaging.python.org/specifications/core-metadata/#obsoletes-dist-multiple-use

		if self.config["readme"] is None:
			description = ''
		else:
			metadata["Description-Content-Type"] = self.config["readme"].content_type
			description = self.config["readme"].text

		metadata_file.write_lines([
				# TODO: https://github.com/python/typeshed/issues/5094
				metadata.as_string(maxheaderlen=2048, policy=metadata.policy.clone(utf8=True)),  # type: ignore
				description,
				])

		self.report_written(metadata_file)

	def call_additional_hooks(self):
		"""
		Subclasses may call this method to give *their* subclasses an opportunity to run custom code.

		For example, the wheel builder calls this as the final step before adding files to the archive,
		giving an opportunity for subclasses of :class:`~.WheelBuilder` to include additional steps
		without having to override the entire :meth:`~.WheelBuilder.build_wheel` method.
		"""

	@abstractmethod
	def build(self):
		"""
		Build the distribution.

		:returns: The filename of the created archive.
		"""

		raise NotImplementedError


class SDistBuilder(AbstractBuilder):
	"""
	Builds source distributions using metadata read from ``pyproject.toml``.

	:param project_dir: The project to build the distribution for.
	:param build_dir: The (temporary) build directory.
	:default build_dir: :file:`{<project_dir>}/build/sdist`
	:param out_dir: The output directory.
	:default out_dir: :file:`{<project_dir>}/dist`
	:param verbose: Enable verbose output.
	"""

	@property
	def default_build_dir(self) -> PathPlus:  # pragma: no cover
		"""
		Provides a default for the ``build_dir`` argument.
		"""

		return self.project_dir / "build" / "sdist"

	def create_sdist_archive(self) -> str:
		"""
		Create the sdist archive.

		:return: The filename of the created archive.
		"""

		self.out_dir.maybe_make(parents=True)

		sdist_filename = self.out_dir / f"{self.archive_name}.tar.gz"
		with tarfile.open(sdist_filename, mode="w:gz", format=tarfile.PAX_FORMAT) as sdist_archive:
			for file in self.build_dir.rglob('*'):
				if file.is_file():
					sdist_archive.add(
							str(file),
							arcname=posixpath.join(self.archive_name, file.relative_to(self.build_dir).as_posix()),
							)

		self._echo(Fore.GREEN(f"Source distribution created at {sdist_filename.resolve().as_posix()}"))
		return os.path.basename(sdist_filename)

	def write_pyproject_toml(self):
		"""
		Write the ``pyproject.toml`` file.
		"""

		# Copy pyproject.toml
		pp_toml = dom_toml.load(self.project_dir / "pyproject.toml")

		# Ensure whey is the build backend and a requirement
		pp_toml.setdefault("build-system", {})
		current_requires = map(ComparableRequirement, pp_toml["build-system"].get("requires", ()))
		new_requirements = combine_requirements(ComparableRequirement("whey"), *current_requires)
		pp_toml["build-system"]["requires"] = list(map(str, sorted(new_requirements)))
		pp_toml["build-system"]["build-backend"] = "whey"

		dynamic = set(pp_toml["project"].get("dynamic", ()))

		# Make the "dependencies" static
		if "dependencies" in dynamic:
			dynamic.remove("dependencies")

			pp_toml["project"]["dependencies"] = list(map(str, sorted(self.config["dependencies"])))

		# Make the "classifiers" static
		if "classifiers" in dynamic:
			dynamic.remove("classifiers")

			pp_toml["project"]["classifiers"] = list(map(str, sorted(self.config["classifiers"])))

		# Make "requires-python" static
		if "requires-python" in dynamic:
			dynamic.remove("requires-python")

			pp_toml["project"]["requires-python"] = str(self.config["requires-python"])

		# Set the new value for "dynamic"
		pp_toml["project"]["dynamic"] = dynamic

		dom_toml.dump(pp_toml, self.build_dir / "pyproject.toml", encoder=dom_toml.TomlEncoder)
		self.report_copied(self.project_dir / "pyproject.toml", self.build_dir / "pyproject.toml")

	def build_sdist(self) -> str:
		"""
		Build the source distribution.

		:return: The filename of the created archive.
		"""

		if self.build_dir.is_dir():
			shutil.rmtree(self.build_dir)
		self.build_dir.maybe_make(parents=True)

		self.copy_source()
		self.copy_additional_files()
		self.write_license(self.build_dir)

		self.write_pyproject_toml()

		for filename in ["requirements.txt"]:
			source = self.project_dir / filename
			if source.is_file():
				dest = self.build_dir / filename
				dest.write_clean(source.read_text())
				self.report_copied(source, dest)

		self.write_readme()
		self.write_metadata(self.build_dir / "PKG-INFO")
		self.call_additional_hooks()

		return self.create_sdist_archive()

	def write_readme(self):
		"""
		Write the ``README.*`` file.
		"""

		if self.config["readme"] is None:
			return

		if self.config["readme"].content_type == "text/x-rst":
			target = self.build_dir / "README.rst"
		elif self.config["readme"].content_type == "text/markdown":
			target = self.build_dir / "README.md"
		else:
			target = self.build_dir / "README"

		target.parent.maybe_make(parents=True)
		target.write_clean(self.config["readme"].text)
		self.report_written(target)

	build = build_sdist


class WheelBuilder(AbstractBuilder):
	"""
	Builds wheel binary distributions using metadata read from ``pyproject.toml``.

	:param project_dir: The project to build the distribution for.
	:param build_dir: The (temporary) build directory.
	:default build_dir: :file:`{<project_dir>}/build/wheel`
	:param out_dir: The output directory.
	:default out_dir: :file:`{<project_dir>}/dist`
	:param verbose: Enable verbose output.

	.. autosummary-widths:: 11/32
		:html: 4/10

	.. latex:vspace:: -10px
	"""

	@property
	def default_build_dir(self) -> PathPlus:  # pragma: no cover
		"""
		Provides a default for the ``build_dir`` argument.
		"""

		return self.project_dir / "build" / "wheel"

	@property
	def dist_info(self) -> PathPlus:
		"""
		The ``*.dist-info`` directory in the build directory.
		"""

		dist_info = self.build_dir / f"{self.archive_name}.dist-info"
		dist_info.maybe_make(parents=True)
		return dist_info

	@property
	def tag(self) -> str:
		"""
		The tag for the wheel.
		"""

		return "py3-none-any"

	def write_entry_points(self) -> None:
		"""
		Write the list of entry points to the wheel, as specified in
		``[project.scripts]``, ``[project.gui-scripts]`` and ``[project.entry-points]``
		"""  # noqa: D400

		buf = StringList()
		if self.config["scripts"]:
			buf.append("[console_scripts]")

			for name, func in self.config["scripts"].items():
				buf.append(f"{name} = {func}")

		if self.config["gui-scripts"]:
			buf.append("[gui_scripts]")

			for name, func in self.config["gui-scripts"].items():
				buf.append(f"{name} = {func}")

		for group, entry_points in self.config["entry-points"].items():

			buf.append(f"[{group}]")

			for name, func in entry_points.items():
				buf.append(f"{name} = {func}")

		cfg_parser = configparser.ConfigParser()
		cfg_parser.optionxform = str  # type: ignore  # preserve case
		cfg_parser.read_string(str(buf))
		cfg_io = StringIO()
		cfg_parser.write(cfg_io)

		entry_points_file = self.dist_info / "entry_points.txt"
		entry_points_file.write_clean(cfg_io.getvalue())
		self.report_written(entry_points_file)

	def write_wheel(self) -> None:
		"""
		Write the metadata to the ``WHEEL`` file.
		"""

		# this package
		from whey import __version__

		wheel = EmailMessage()
		wheel["Wheel-Version"] = "1.0"
		wheel["Generator"] = f"whey ({__version__})"
		wheel["Root-Is-Purelib"] = "true"
		wheel["Tag"] = self.tag

		wheel_file = self.dist_info / "WHEEL"
		wheel_file.write_clean(str(wheel))
		self.report_written(wheel_file)

	def write_top_level(self, dist_info: PathPlus) -> None:
		"""
		Write the ``top_level.txt`` file to the ``*.dist-info`` directory.

		:param dist_info: The absolute path to the ``*.dist-info`` directory.
		"""

		top_level = first(posixpath.split(self.config["package"]), default=self.config["package"])
		(dist_info / "top_level.txt").write_clean(top_level)
		self.report_written(dist_info / "top_level.txt")

	def create_wheel_archive(self) -> str:
		"""
		Create the wheel archive.

		:return: The filename of the created archive.
		"""

		wheel_filename = self.out_dir / f"{self.archive_name}-{self.tag}.whl"
		self.out_dir.maybe_make(parents=True)

		with ZipFile(wheel_filename, mode='w') as wheel_archive:
			with (self.dist_info / "RECORD").open('w') as fp:
				for file in self.build_dir.rglob('*'):
					if "RECORD" in file.name and self.dist_info.name in file.parts:
						continue
					if not file.is_file():
						continue

					fp.write(get_record_entry(file, relative_to=self.build_dir))
					fp.write('\n')
					wheel_archive.write(file, arcname=file.relative_to(self.build_dir))

				for file in self.dist_info.rglob("RECORD*"):
					if file.is_file():
						fp.write(f"{file.relative_to(self.build_dir).as_posix()},,\n")

			for file in self.dist_info.rglob("RECORD*"):
				if file.is_file():
					wheel_archive.write(file, arcname=file.relative_to(self.build_dir))
					self.report_written(file)

		self._echo(Fore.GREEN(f"Wheel created at {wheel_filename.resolve().as_posix()}"))

		return wheel_filename.name

	def build_wheel(self) -> str:
		"""
		Build the binary wheel distribution.

		:return: The filename of the created archive.
		"""

		if self.build_dir.is_dir():
			shutil.rmtree(self.build_dir)

		self.build_dir.maybe_make(parents=True)

		self.copy_source()
		self.copy_additional_files()
		self.write_license(self.dist_info)
		self.write_entry_points()
		self.write_metadata(self.dist_info / "METADATA")
		self.write_wheel()
		self.write_top_level(self.dist_info)
		self.call_additional_hooks()

		return self.create_wheel_archive()

	build = build_wheel
