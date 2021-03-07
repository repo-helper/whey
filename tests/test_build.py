# stdlib
import shutil
import tarfile
import tempfile
import zipfile

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, check_file_regression
from domdf_python_tools.paths import PathPlus, compare_dirs
from pytest_regressions.file_regression import FileRegressionFixture

# this package
from tests.example_configs import (
		AUTHORS,
		CLASSIFIERS,
		DEPENDENCIES,
		ENTRY_POINTS,
		KEYWORDS,
		MAINTAINERS,
		MINIMAL_CONFIG,
		OPTIONAL_DEPENDENCIES,
		UNICODE,
		URLS
		)
from whey import SDistBuilder, WheelBuilder

COMPLETE_PROJECT_A = """\
[project]
name = "spam"
version = "2020.0.0"
description = "Lovely Spam! Wonderful Spam!"
requires-python = ">=3.8"
keywords = ["egg", "bacon", "sausage", "tomatoes", "Lobster Thermidor"]
authors = [
  {email = "hi@pradyunsg.me"},
  {name = "Tzu-Ping Chung"}
]
maintainers = [
  {name = "Brett Cannon", email = "brett@python.org"}
]
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python"
]

dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]

[project.optional-dependencies]
test = [
  "pytest < 5.0.0",
  "pytest-cov[all]"
]

[project.urls]
homepage = "example.com"
documentation = "readthedocs.org"
repository = "github.com"
changelog = "github.com/me/spam/blob/master/CHANGELOG.md"

[project.scripts]
spam-cli = "spam:main_cli"

[project.gui-scripts]
spam-gui = "spam:main_gui"

[project.entry-points."spam.magical"]
tomatoes = "spam:main_tomatoes"
"""

COMPLETE_A = """\
[build-system]
requires = [ "whey",]
build-backend = "whey"

[project]
name = "whey"
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
keywords = [ "pep517", "pep621", "build", "sdist", "wheel", "packaging", "distribution",]
dynamic = [ "classifiers", "requires-python",]
readme = "README.rst"
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]

[project.license]
file = "LICENSE"

[[project.authors]]
email = "dominic@davis-foster.co.uk"
name = "Dominic Davis-Foster"

[project.urls]
Homepage = "https://whey.readthedocs.io/en/latest"
Documentation = "https://whey.readthedocs.io/en/latest"
"Issue Tracker" = "https://github.com/repo-helper/whey/issues"
"Source Code" = "https://github.com/repo-helper/whey"

[tool.whey]
base-classifiers = [ "Development Status :: 4 - Beta",]
python-versions = [ "3.6", "3.7", "3.8", "3.9", "3.10",]
python-implementations = [ "CPython", "PyPy",]
platforms = [ "Windows", "macOS", "Linux",]
license-key = "MIT"
"""

COMPLETE_B = """\
[build-system]
requires = [ "whey",]
build-backend = "whey"

[project]
name = "Whey"
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
readme = "README.rst"
keywords = [ "pep517", "pep621", "build", "sdist", "wheel", "packaging", "distribution",]
dynamic = [ "classifiers", "requires-python",]
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]

[project.license]
file = "LICENSE"

[[project.authors]]
email = "dominic@davis-foster.co.uk"
name = "Dominic Davis-Foster"

[project.urls]
Homepage = "https://whey.readthedocs.io/en/latest"
Documentation = "https://whey.readthedocs.io/en/latest"
"Issue Tracker" = "https://github.com/repo-helper/whey/issues"
"Source Code" = "https://github.com/repo-helper/whey"

[tool.whey]
base-classifiers = [ "Development Status :: 4 - Beta",]
python-versions = [ "3.6", "3.7", "3.8", "3.9", "3.10",]
python-implementations = [ "CPython", "PyPy",]
platforms = [ "Windows", "macOS", "Linux",]
license-key = "MIT"
package = "whey"
"""

LONG_REQUIREMENTS = """\
[build-system]
requires = [ "whey",]
build-backend = "whey"

[project]
name = "Whey"
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
readme = "README.rst"
dynamic = [ "classifiers", "requires-python",]
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'",
  "typed-ast>=1.4.2; python_version < '3.8' and platform_python_implementation == 'CPython'"
]

[project.license]
file = "LICENSE"

[[project.authors]]
email = "dominic@davis-foster.co.uk"
name = "Dominic Davis-Foster"

[tool.whey]
base-classifiers = [ "Development Status :: 4 - Beta",]
license-key = "MIT"
package = "whey"
"""


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
		file_regression: FileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "spam").mkdir()
	(tmp_pathplus / "spam" / "__init__.py").write_clean("print('hello world)")

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
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
			assert fp.read().decode("UTF-8") == "print('hello world)\n"

		with zip_file.open("spam-2020.0.0.dist-info/METADATA", mode='r') as fp:
			check_file_regression(fp.read().decode("UTF-8"), file_regression)

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		tar = tarfile.open(tmp_pathplus / sdist)
		data["sdist_content"] = sorted(tar.getnames())

		with tar.extractfile("spam/__init__.py") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "print('hello world)\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


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
		file_regression: FileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world)")
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
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
			assert fp.read().decode("UTF-8") == "print('hello world)\n"

		with zip_file.open("whey-2021.0.0.dist-info/METADATA", mode='r') as fp:
			check_file_regression(fp.read().decode("UTF-8"), file_regression)

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		tar = tarfile.open(tmp_pathplus / sdist)
		data["sdist_content"] = sorted(tar.getnames())

		with tar.extractfile("whey/__init__.py") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "print('hello world)\n"
		with tar.extractfile("README.rst") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "Spam Spam Spam Spam\n"
		with tar.extractfile("LICENSE") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "This is the license\n"
		with tar.extractfile("requirements.txt") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "domdf_python_tools\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def test_build_additional_files(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		file_regression: FileRegressionFixture,
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
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world)")
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
			assert fp.read().decode("UTF-8") == "print('hello world)\n"

		with zip_file.open("whey-2021.0.0.dist-info/METADATA", mode='r') as fp:
			check_file_regression(fp.read().decode("UTF-8"), file_regression)

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		tar = tarfile.open(tmp_pathplus / sdist)
		data["sdist_content"] = sorted(tar.getnames())

		with tar.extractfile("whey/__init__.py") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "print('hello world)\n"
		with tar.extractfile("whey/style.css") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "This is the style.css file\n"
		with tar.extractfile("README.rst") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "Spam Spam Spam Spam\n"
		with tar.extractfile("LICENSE") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "This is the license\n"
		with tar.extractfile("requirements.txt") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "domdf_python_tools\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def test_build_missing_dir(tmp_pathplus: PathPlus):
	(tmp_pathplus / "pyproject.toml").write_clean(MINIMAL_CONFIG)

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
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
				pytest.param(LONG_REQUIREMENTS, id="LONG_REQUIREMENTS"),
				]
		)
def test_build_wheel_from_sdist(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		file_regression: FileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world)")
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	# Build the sdist

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

	# unpack sdist into another tmpdir and use that as project_dir

	(tmp_pathplus / "sdist_unpacked").mkdir()

	with tarfile.open(tmp_pathplus / sdist) as sdist_tar:
		sdist_tar.extractall(path=tmp_pathplus / "sdist_unpacked")

	capsys.readouterr()
	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus / "sdist_unpacked",
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
			assert fp.read().decode("UTF-8") == "print('hello world)\n"

		with zip_file.open("whey-2021.0.0.dist-info/METADATA", mode='r') as fp:
			check_file_regression(fp.read().decode("UTF-8"), file_regression)

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
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world)")
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


def test_build_underscore_name(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		file_regression: FileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam_spam"',
			'version = "2020.0.0"',
			])
	(tmp_pathplus / "spam_spam").mkdir()
	(tmp_pathplus / "spam_spam" / "__init__.py").write_clean("print('hello world)")

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		wheel = wheel_builder.build_wheel()
		assert (tmp_pathplus / wheel).is_file()
		zip_file = zipfile.ZipFile(tmp_pathplus / wheel)
		data["wheel_content"] = sorted(zip_file.namelist())

		with zip_file.open("spam_spam/__init__.py", mode='r') as fp:
			assert fp.read().decode("UTF-8") == "print('hello world)\n"

		with zip_file.open("spam_spam-2020.0.0.dist-info/METADATA", mode='r') as fp:
			check_file_regression(fp.read().decode("UTF-8"), file_regression)

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		tar = tarfile.open(tmp_pathplus / sdist)
		data["sdist_content"] = sorted(tar.getnames())

		with tar.extractfile("spam_spam/__init__.py") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "print('hello world)\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def test_build_stubs_name(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		file_regression: FileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam_spam-stubs"',
			'version = "2020.0.0"',
			])
	(tmp_pathplus / "spam_spam-stubs").mkdir()
	(tmp_pathplus / "spam_spam-stubs" / "__init__.pyi").write_clean("print('hello world)")

	data = {}

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		wheel = wheel_builder.build_wheel()
		assert (tmp_pathplus / wheel).is_file()
		zip_file = zipfile.ZipFile(tmp_pathplus / wheel)
		data["wheel_content"] = sorted(zip_file.namelist())

		with zip_file.open("spam_spam-stubs/__init__.pyi", mode='r') as fp:
			assert fp.read().decode("UTF-8") == "print('hello world)\n"

		with zip_file.open("spam_spam_stubs-2020.0.0.dist-info/METADATA", mode='r') as fp:
			check_file_regression(fp.read().decode("UTF-8"), file_regression)

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist_builder = SDistBuilder(
				project_dir=tmp_pathplus,
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		sdist = sdist_builder.build_sdist()
		assert (tmp_pathplus / sdist).is_file()

		tar = tarfile.open(tmp_pathplus / sdist)
		data["sdist_content"] = sorted(tar.getnames())

		with tar.extractfile("spam_spam-stubs/__init__.pyi") as fp:  # type: ignore
			assert fp.read().decode("UTF-8") == "print('hello world)\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


# TODO: test some bad configurations
