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
import os
import pathlib
import posixpath
import re
import shutil
import tarfile
import warnings
from abc import ABC, abstractmethod
from datetime import datetime
from email.headerregistry import Address
from functools import partial
from typing import Any, Dict, Iterator, Mapping, Optional

# 3rd party
import click
import dom_toml
import handy_archives
from consolekit.terminal_colours import ColourTrilean, Fore, resolve_color_default
from dist_meta import entry_points, metadata, wheel
from dist_meta.metadata_mapping import MetadataMapping
from domdf_python_tools.paths import PathPlus, sort_paths, traverse_to_file
from domdf_python_tools.typing import PathLike
from domdf_python_tools.words import word_join
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

	.. autoclasssumm:: AbstractBuilder
		:autosummary-sections: Attributes

	.. latex:clearpage::

	.. autosummary-widths:: 7/16

	.. autoclasssumm:: AbstractBuilder
		:autosummary-sections: Methods
	"""

	def __init__(
			self,
			project_dir: PathPlus,
			config: Mapping[str, Any],
			build_dir: Optional[PathLike] = None,
			out_dir: Optional[PathLike] = None,
			*args,
			verbose: bool = False,
			colour: ColourTrilean = None,
			**kwargs,
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

	@property
	def code_directory(self) -> str:
		"""
		The directory containing the code in the build directory.
		"""

		return self.config["source-dir"]

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
			message = f"Package directory {self.config['package']!r} not found"

			if self.config["source-dir"]:
				raise FileNotFoundError(f"{message} in {self.config['source-dir']!r}.")
			else:
				raise FileNotFoundError(f"{message}.")

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
			target = self.build_dir / py_file.relative_to(self.project_dir / self.code_directory)
			target.parent.maybe_make(parents=True)
			target.write_clean(py_file.read_text())
			shutil.copystat(py_file, target)
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

		def copy_file(filename: PathPlus):
			target = self.build_dir / filename.relative_to(self.project_dir / self.code_directory)
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

	def parse_authors(self) -> Dict[str, str]:
		"""
		Parse the :tconf:`project.authors` and :tconf:`~project.maintainers` fields into :core-meta:`Author`,
		:core-meta:`Maintainer-Email` etc.

		:return: A mapping of field names to values.

			Possible field names are ``Author``, ``Author-Email``, ``Maintainer``, and ``Maintainer-Email``.
		"""  # noqa: D400

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

		output = {}

		if author_email:
			output["Author-email"] = ", ".join(author_email)
		elif author:
			output["Author"] = word_join(author)

		if maintainer_email:
			output["Maintainer-email"] = ", ".join(maintainer_email)
		elif maintainer:
			output["Maintainer"] = word_join(maintainer)

		return output

	def get_metadata_map(self) -> MetadataMapping:
		"""
		Generate the content of the ``METADATA`` / ``PKG-INFO`` file.
		"""

		metadata_mapping = MetadataMapping()

		# TODO: metadata 2.2
		# Need to translate pep621 dynamic into core metadata field names
		metadata_mapping["Metadata-Version"] = "2.1"
		metadata_mapping["Name"] = self.config["name"]
		metadata_mapping["Version"] = str(self.config["version"])

		def add_not_none(key: str, field: str):
			if self.config[key] is not None:
				metadata_mapping[field] = self.config[key]

		def add_multiple(key: str, field: str):
			for value in self.config[key]:
				metadata_mapping[field] = str(value)

		metadata_mapping.update(self.parse_authors())

		add_not_none("description", "Summary")
		add_not_none("license-key", "License")

		add_multiple("classifiers", "Classifier")
		add_multiple("dependencies", "Requires-Dist")

		if self.config["keywords"]:
			metadata_mapping["Keywords"] = ','.join(self.config["keywords"])

		seen_hp = False

		for category, url in self.config["urls"].items():
			if category.lower() in {"homepage", "home page"} and not seen_hp:
				metadata_mapping["Home-page"] = url
				seen_hp = True
			else:
				metadata_mapping["Project-URL"] = f"{category}, {url}"

		for platform in (self.config.get("platforms", None) or ()):
			metadata_mapping["Platform"] = platform

		if self.config["requires-python"]:
			metadata_mapping["Requires-Python"] = str(self.config["requires-python"])

		for extra, requirements in self.config["optional-dependencies"].items():
			metadata_mapping["Provides-Extra"] = extra
			for requirement in requirements:
				requirement = ComparableRequirement(str(requirement))

				if requirement.marker:
					requirement.marker = f"({requirement.marker!s}) and extra == {extra!r}"
				else:
					requirement.marker = f"extra == {extra!r}"

				metadata_mapping["Requires-Dist"] = str(requirement)

		# TODO:
		#  https://packaging.python.org/specifications/core-metadata/#requires-external-multiple-use
		#  https://packaging.python.org/specifications/core-metadata/#provides-dist-multiple-use
		#  https://packaging.python.org/specifications/core-metadata/#obsoletes-dist-multiple-use

		if self.config["readme"] is not None:
			metadata_mapping["Description"] = self.config["readme"].text
			metadata_mapping["Description-Content-Type"] = self.config["readme"].content_type

		return metadata_mapping

	def write_metadata(self, metadata_file: PathPlus, metadata_mapping: MetadataMapping):
		"""
		Write `Core Metadata`_ to the given file.

		.. _Core Metadata: https://packaging.python.org/specifications/core-metadata

		:param metadata_file:
		"""

		metadata_file.write_text(metadata.dumps(metadata_mapping))
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

	@property
	def code_directory(self) -> str:
		"""
		The directory containing the code in the build and project directories.
		"""

		return ''

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
					arcname = posixpath.join(self.archive_name, file.relative_to(self.build_dir).as_posix())
					sdist_archive.add(str(file), arcname=arcname)

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
		self.write_metadata(self.build_dir / "PKG-INFO", self.get_metadata_map())
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

	@property
	def generator(self) -> str:
		"""
		The value for the ``Generator`` field in ``*.dist-info/WHEEL``.
		"""

		# this package
		from whey import __version__

		return f"whey ({__version__})"

	def write_entry_points(self) -> None:
		"""
		Write the list of entry points to the wheel, as specified in
		``[project.scripts]``, ``[project.gui-scripts]`` and ``[project.entry-points]``
		"""  # noqa: D400

		ep_dict = {}

		if self.config["scripts"]:
			ep_dict["console_scripts"] = self.config["scripts"]

		if self.config["gui-scripts"]:
			ep_dict["gui_scripts"] = self.config["gui-scripts"]

		ep_dict.update(self.config["entry-points"])

		entry_points_file = self.dist_info / "entry_points.txt"
		entry_points.dump(ep_dict, entry_points_file)
		self.report_written(entry_points_file)

	def write_wheel(self) -> None:
		"""
		Write the metadata to the ``WHEEL`` file.
		"""

		wheel_file = self.dist_info / "WHEEL"

		wheel_file.write_clean(
				wheel.dumps({
						"Wheel-Version": "1.0",
						"Generator": self.generator,
						"Root-Is-Purelib": True,
						"Tag": [self.tag],
						})
				)

		self.report_written(wheel_file)

	@staticmethod
	def get_source_epoch() -> Optional[datetime]:
		"""
		Returns the parsed value of the :envvar:`SOURCE_DATE_EPOCH` environment variable, or :py:obj:`None` if unset.

		See https://reproducible-builds.org/specs/source-date-epoch/ for the specification.

		:raises ValueError: if the value is in an invalid format.
		"""

		# If SOURCE_DATE_EPOCH is set (e.g. by Debian), it's used for timestamps inside the wheel.
		epoch: Optional[str] = os.environ.get("SOURCE_DATE_EPOCH")
		if epoch is None:
			return None
		elif epoch.isdigit():
			return datetime.utcfromtimestamp(int(epoch))
		else:
			raise ValueError(f"'SOURCE_DATE_EPOCH' must be an integer with no fractional component, not {epoch!r}")

	def create_wheel_archive(self) -> str:
		"""
		Create the wheel archive.

		:return: The filename of the created archive.
		"""

		wheel_filename = self.out_dir / f"{self.archive_name}-{self.tag}.whl"
		self.out_dir.maybe_make(parents=True)

		mtime = self.get_source_epoch()

		non_record_filenames = []
		record_filenames = []

		for file in self.build_dir.rglob('*'):
			if not file.is_file():
				continue
			if "RECORD" in file.name and self.dist_info.name in file.parts:
				record_filenames.append(file)
				continue

			non_record_filenames.append(file)

		record_filenames = sort_paths(*record_filenames, self.dist_info / "RECORD")

		with handy_archives.ZipFile(wheel_filename, mode='w') as wheel_archive:
			with (self.dist_info / "RECORD").open('w') as fp:
				for file in sort_paths(*non_record_filenames):

					fp.write(f"{get_record_entry(file, relative_to=self.build_dir)}\n")

					wheel_archive.write_file(
							file,
							arcname=file.relative_to(self.build_dir),
							mtime=mtime,
							)

				for file in record_filenames:
					fp.write(f"{file.relative_to(self.build_dir).as_posix()},,\n")

			for file in record_filenames:
				wheel_archive.write_file(
						file,
						arcname=file.relative_to(self.build_dir),
						mtime=mtime,
						)
				self.report_written(file)

		self._echo(Fore.GREEN(f"Wheel created at {wheel_filename.resolve().as_posix()}"))

		return wheel_filename.name

	def create_editables_files(self) -> Iterator[ComparableRequirement]:
		"""
		Generate files with `editables`_ for use in a :pep:`660` wheel.

		.. _editables: https://pypi.org/project/editables/

		.. extras-require:: editable
			:scope: method
			:pyproject:

		:returns: An iterator of additional runtime requirements which should be added to the wheel's ``METADATA`` file.
		"""

		# this package
		from whey._editable import EditableProject

		pkgdir = self.project_dir / self.config["source-dir"] / self.config["package"]

		if not pkgdir.is_dir():
			message = f"Package directory {self.config['package']!r} not found"

			if self.config["source-dir"]:
				raise FileNotFoundError(f"{message} in {self.config['source-dir']!r}.")
			else:
				raise FileNotFoundError(f"{message}.")

		my_project = EditableProject(
				self.config["name"].replace('-', '_'),
				pkgdir.parent,
				)

		my_project.map_or_add_to_path(self.config["package"], pkgdir)

		for name, content in my_project.files():
			target = self.build_dir / name
			target.parent.maybe_make(parents=True)
			target.write_clean(content)
			self.report_written(target)

		yield from map(ComparableRequirement, my_project.dependencies())

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
		self.write_metadata(self.dist_info / "METADATA", self.get_metadata_map())
		self.write_wheel()
		self.call_additional_hooks()

		return self.create_wheel_archive()

	build = build_wheel

	def build_editable(self) -> str:
		"""
		Build an editable wheel.

		An "editable" wheel uses the wheel format not for distribution but as ephemeral communication
		between the build system and the front end.
		This avoids having the build backend install anything directly.
		This wheel must not be exposed to end users, nor cached, nor distributed.

		You should use a different ``build_dir`` and ``out_dir`` to those used for standard wheel builds.

		The default implementation of this method does not call
		:meth:`~.AbstractBuilder.copy_source` or :meth:`~.AbstractBuilder.copy_additional_files`.

		.. extras-require:: editable
			:scope: method
			:pyproject:

		:return: The filename of the created archive.
		"""

		if self.build_dir.is_dir():
			shutil.rmtree(self.build_dir)

		self.build_dir.maybe_make(parents=True)

		extra_deps = self.create_editables_files()
		self.write_license(self.dist_info)
		self.write_entry_points()

		metadata = self.get_metadata_map()

		for dep in extra_deps:
			if not any(dep.name in req for req in metadata.get_all("Requires-Dist", ())):
				# Additional runtime requirement for editable wheels.
				metadata["Requires-Dist"] = str(dep)

		# Prevents uploading to PyPI, which you shouldn't do with an editable wheel.
		metadata["Classifier"] = "Private :: Do Not Upload"

		self.write_metadata(self.dist_info / "METADATA", metadata)
		self.write_wheel()
		self.call_additional_hooks()

		return self.create_wheel_archive()
