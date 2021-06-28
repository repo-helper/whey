# stdlib
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import List

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus, compare_dirs
from pyproject_examples.example_configs import (
		AUTHORS,
		CLASSIFIERS,
		DEPENDENCIES,
		DYNAMIC_REQUIREMENTS,
		ENTRY_POINTS,
		KEYWORDS,
		LONG_REQUIREMENTS,
		MAINTAINERS,
		MINIMAL_CONFIG,
		OPTIONAL_DEPENDENCIES,
		UNICODE,
		URLS
		)

# this package
from tests.example_configs import COMPLETE_A, COMPLETE_B
from tests.utils import TarFile
from whey.builder import SDistBuilder, WheelBuilder
from whey.config import load_toml


@pytest.mark.parametrize(
		"config",
		[
				pytest.param(MINIMAL_CONFIG, id="minimal"),
				pytest.param(f'{MINIMAL_CONFIG}\ndescription = "Lovely Spam! Wonderful Spam!"', id="description"),
				pytest.param(f'{MINIMAL_CONFIG}\nrequires-python = ">=3.8"', id="requires-python"),
				pytest.param(
						f'{MINIMAL_CONFIG}\nrequires-python = ">=2.7,!=3.0.*,!=3.2.*"',
						id="requires-python_complex"
						),
				pytest.param(KEYWORDS, id="keywords"),
				pytest.param(AUTHORS, id="authors"),
				pytest.param(MAINTAINERS, id="maintainers"),
				pytest.param(CLASSIFIERS, id="classifiers"),
				pytest.param(DEPENDENCIES, id="dependencies"),
				pytest.param(OPTIONAL_DEPENDENCIES, id="optional-dependencies"),
				pytest.param(URLS, id="urls"),
				pytest.param(ENTRY_POINTS, id="entry_points"),
				pytest.param(UNICODE, id="unicode"),
				]
		)
def test_build_success(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "spam").mkdir()
	(tmp_pathplus / "spam" / "__init__.py").write_clean("print('hello world')")
	now = datetime.now()
	os.utime(tmp_pathplus / "spam" / "__init__.py", (now.timestamp(), now.timestamp()))

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		wheel = wheel_builder.build_wheel()
		assert (tmp_pathplus / wheel).is_file()
		zip_file = zipfile.ZipFile(tmp_pathplus / wheel)
		data["wheel_content"] = sorted(zip_file.namelist())

		with zip_file.open("spam/__init__.py", mode='r') as fp:
			assert fp.read().decode("UTF-8") == "print('hello world')\n"

		with zip_file.open("spam-2020.0.0.dist-info/METADATA", mode='r') as fp:
			advanced_file_regression.check(fp.read().decode("UTF-8"))

		# The seconds can vary by 1 second between the mtime and the time in the zip, but this is inconsistent
		assert zip_file.getinfo("spam/__init__.py").date_time[:5] == now.timetuple()[:5]

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		with TarFile.open(tmp_pathplus / sdist) as tar:
			data["sdist_content"] = sorted(tar.getnames())
			assert tar.read_text("spam-2020.0.0/spam/__init__.py") == "print('hello world')\n"

			advanced_file_regression.check(tar.read_text("spam-2020.0.0/PKG-INFO"))
			advanced_file_regression.check(tar.read_text("spam-2020.0.0/pyproject.toml"), extension=".toml")

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def check_built_wheel(filename: PathPlus, advanced_file_regression: AdvancedFileRegressionFixture):
	assert filename.is_file()
	zip_file = zipfile.ZipFile(filename)

	with zip_file.open("whey/__init__.py", mode='r') as fp:
		assert fp.read().decode("UTF-8") == "print('hello world')\n"
	with zip_file.open("whey-2021.0.0.dist-info/METADATA", mode='r') as fp:
		advanced_file_regression.check(fp.read().decode("UTF-8"))

	contents = sorted(zip_file.namelist())

	with zip_file.open("whey-2021.0.0.dist-info/RECORD", mode='r') as fp:
		for line in fp.readlines():
			entry_filename, digest, size, *_ = line.decode("UTF-8").strip().split(',')
			assert entry_filename in contents, entry_filename
			contents.remove(entry_filename)

			if "RECORD" not in entry_filename:
				assert zip_file.getinfo(entry_filename).file_size == int(size)
				# TODO: check digest

	return sorted(zip_file.namelist())


@pytest.mark.parametrize(
		"config",
		[
				# pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				pytest.param(LONG_REQUIREMENTS, id="LONG_REQUIREMENTS"),
				]
		)
def test_build_complete(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world')")
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		wheel = wheel_builder.build_wheel()
		data["wheel_content"] = check_built_wheel(tmp_pathplus / wheel, advanced_file_regression)

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		with TarFile.open(tmp_pathplus / sdist) as tar:
			data["sdist_content"] = sorted(tar.getnames())

			assert tar.read_text("whey-2021.0.0/whey/__init__.py") == "print('hello world')\n"
			assert tar.read_text("whey-2021.0.0/README.rst") == "Spam Spam Spam Spam\n"
			assert tar.read_text("whey-2021.0.0/LICENSE") == "This is the license\n"
			assert tar.read_text("whey-2021.0.0/requirements.txt") == "domdf_python_tools\n"

			advanced_file_regression.check(tar.read_text("whey-2021.0.0/PKG-INFO"))
			advanced_file_regression.check(tar.read_text("whey-2021.0.0/pyproject.toml"), extension=".toml")

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def test_build_additional_files(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		capsys,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			COMPLETE_B,
			'',
			"additional-files = [",
			'  "include whey/style.css",',
			'  "exclude whey/style.css",',
			'  "include whey/style.css",',
			'  "recursive-include whey/static *",',
			'  "recursive-exclude whey/static *.txt",',
			']',
			])
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world')")
	(tmp_pathplus / "whey" / "style.css").write_clean("This is the style.css file")
	(tmp_pathplus / "whey" / "static").mkdir()
	(tmp_pathplus / "whey" / "static" / "foo.py").touch()
	(tmp_pathplus / "whey" / "static" / "foo.c").touch()
	(tmp_pathplus / "whey" / "static" / "foo.txt").touch()
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		wheel = wheel_builder.build_wheel()
		assert (tmp_pathplus / wheel).is_file()
		zip_file = zipfile.ZipFile(tmp_pathplus / wheel)
		data["wheel_content"] = sorted(zip_file.namelist())

		with zip_file.open("whey/__init__.py", mode='r') as fp:
			assert fp.read().decode("UTF-8") == "print('hello world')\n"

		with zip_file.open("whey-2021.0.0.dist-info/METADATA", mode='r') as fp:
			advanced_file_regression.check(fp.read().decode("UTF-8"))

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				)
		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		with TarFile.open(tmp_pathplus / sdist) as tar:
			data["sdist_content"] = sorted(tar.getnames())

			assert tar.read_text("whey-2021.0.0/whey/__init__.py") == "print('hello world')\n"
			assert tar.read_text("whey-2021.0.0/whey/style.css") == "This is the style.css file\n"
			assert tar.read_text("whey-2021.0.0/README.rst") == "Spam Spam Spam Spam\n"
			assert tar.read_text("whey-2021.0.0/LICENSE") == "This is the license\n"
			assert tar.read_text("whey-2021.0.0/requirements.txt") == "domdf_python_tools\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def test_build_markdown_readme(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		capsys,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(COMPLETE_B.replace(".rst", ".md"))
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world')")
	(tmp_pathplus / "README.md").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		wheel = wheel_builder.build_wheel()
		data["wheel_content"] = check_built_wheel(tmp_pathplus / wheel, advanced_file_regression)

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				)
		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		with TarFile.open(tmp_pathplus / sdist) as tar:
			data["sdist_content"] = sorted(tar.getnames())

			assert tar.read_text("whey-2021.0.0/whey/__init__.py") == "print('hello world')\n"
			assert tar.read_text("whey-2021.0.0/README.md") == "Spam Spam Spam Spam\n"
			assert tar.read_text("whey-2021.0.0/LICENSE") == "This is the license\n"
			assert tar.read_text("whey-2021.0.0/requirements.txt") == "domdf_python_tools\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def test_build_missing_dir(tmp_pathplus: PathPlus):
	(tmp_pathplus / "pyproject.toml").write_clean(MINIMAL_CONFIG)

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		with pytest.raises(FileNotFoundError, match="Package directory 'spam' not found."):
			wheel_builder.build_wheel()

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		with pytest.raises(FileNotFoundError, match="Package directory 'spam' not found."):
			sdist_builder.build_sdist()


def test_build_empty_dir(tmp_pathplus: PathPlus):
	(tmp_pathplus / "pyproject.toml").write_clean(MINIMAL_CONFIG)
	(tmp_pathplus / "spam").mkdir()

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		with pytest.raises(FileNotFoundError, match="No Python source files found in"):
			wheel_builder.build_wheel()

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		with pytest.raises(FileNotFoundError, match="No Python source files found in"):
			sdist_builder.build_sdist()


@pytest.mark.parametrize(
		"config",
		[
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				pytest.param(DYNAMIC_REQUIREMENTS, id="DYNAMIC_REQUIREMENTS"),
				pytest.param(LONG_REQUIREMENTS, id="LONG_REQUIREMENTS"),
				]
		)
def test_build_wheel_from_sdist(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world')")
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_lines([
			"httpx", "gidgethub[httpx]>4.0.0", "django>2.1; os_name != 'nt'", "django>2.0; os_name == 'nt'"
			])

	# Build the sdist
	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

	# unpack sdist into another tmpdir and use that as project_dir
	(tmp_pathplus / "sdist_unpacked").mkdir()

	with TarFile.open(tmp_pathplus / sdist) as sdist_tar:
		sdist_tar.extractall(path=tmp_pathplus / "sdist_unpacked")

	capsys.readouterr()
	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus / "sdist_unpacked/whey-2021.0.0/",
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		wheel = wheel_builder.build_wheel()
		data["wheel_content"] = check_built_wheel(tmp_pathplus / wheel, advanced_file_regression)

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


@pytest.mark.parametrize(
		"config", [
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_build_wheel_reproducible(
		config: str,
		tmp_pathplus: PathPlus,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world')")
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	# Build the wheel twice

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus / "wheel1",
				verbose=True,
				colour=False,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				)

		wheel = wheel_builder.build_wheel()
		assert (tmp_pathplus / "wheel1" / wheel).is_file()

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus / "wheel2",
				verbose=True,
				colour=False,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				)
		wheel = wheel_builder.build_wheel()
		assert (tmp_pathplus / "wheel2" / wheel).is_file()

	# extract both

	shutil.unpack_archive(
			str(tmp_pathplus / "wheel1" / wheel),
			extract_dir=tmp_pathplus / "wheel1" / "unpack",
			format="zip",
			)
	shutil.unpack_archive(
			str(tmp_pathplus / "wheel1" / wheel),
			extract_dir=tmp_pathplus / "wheel2" / "unpack",
			format="zip",
			)
	# (tmp_pathplus / "wheel2" / "unpack" / "foo.txt").touch()

	assert compare_dirs(
			tmp_pathplus / "wheel1" / "unpack",
			tmp_pathplus / "wheel2" / "unpack",
			)


@pytest.mark.parametrize(
		"config",
		[
				pytest.param(
						["[project]", 'name = "spam_spam"', 'version = "2020.0.0"'],
						id="underscore_name",
						),
				pytest.param(
						["[project]", 'name = "spam-spam"', 'version = "2020.0.0"'],
						id="hyphen_name_underscore_package_implicit",
						),
				pytest.param([
						"[project]",
						'name = "spam-spam"',
						'version = "2020.0.0"',
						"[tool.whey]",
						"package = 'spam_spam'"
						],
								id="hyphen_name_underscore_package_explicit"),
				]
		)
def test_build_underscore_name(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		capsys,
		config: List[str]
		):
	(tmp_pathplus / "pyproject.toml").write_lines(config)
	(tmp_pathplus / "spam_spam").mkdir()
	(tmp_pathplus / "spam_spam" / "__init__.py").write_clean("print('hello world')")

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				)

		wheel = wheel_builder.build_wheel()
		assert (tmp_pathplus / wheel).is_file()
		zip_file = zipfile.ZipFile(tmp_pathplus / wheel)
		data["wheel_content"] = sorted(zip_file.namelist())

		with zip_file.open("spam_spam/__init__.py", mode='r') as fp:
			assert fp.read().decode("UTF-8") == "print('hello world')\n"

		with zip_file.open("spam_spam-2020.0.0.dist-info/METADATA", mode='r') as fp:
			advanced_file_regression.check(fp.read().decode("UTF-8"))

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				)

		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		with TarFile.open(tmp_pathplus / sdist) as tar:
			data["sdist_content"] = sorted(tar.getnames())

			assert tar.read_text("spam_spam-2020.0.0/spam_spam/__init__.py") == "print('hello world')\n"

			advanced_file_regression.check(tar.read_text("spam_spam-2020.0.0/PKG-INFO"))

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def test_build_stubs_name(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		advanced_file_regression: AdvancedFileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam_spam-stubs"',
			'version = "2020.0.0"',
			])
	(tmp_pathplus / "spam_spam-stubs").mkdir()
	(tmp_pathplus / "spam_spam-stubs" / "__init__.pyi").write_clean("print('hello world')")

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				)

		wheel = wheel_builder.build_wheel()
		assert (tmp_pathplus / wheel).is_file()
		zip_file = zipfile.ZipFile(tmp_pathplus / wheel)
		data["wheel_content"] = sorted(zip_file.namelist())

		with zip_file.open("spam_spam-stubs/__init__.pyi", mode='r') as fp:
			assert fp.read().decode("UTF-8") == "print('hello world')\n"

		with zip_file.open("spam_spam_stubs-2020.0.0.dist-info/METADATA", mode='r') as fp:
			advanced_file_regression.check(fp.read().decode("UTF-8"))

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				)

		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		with TarFile.open(tmp_pathplus / sdist) as tar:
			data["sdist_content"] = sorted(tar.getnames())

			assert tar.read_text(
					"spam_spam_stubs-2020.0.0/spam_spam-stubs/__init__.pyi"
					) == "print('hello world')\n"

			advanced_file_regression.check(tar.read_text("spam_spam_stubs-2020.0.0/PKG-INFO"))

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


# TODO: test some bad configurations
