# stdlib
import tarfile
import tempfile
import zipfile
from typing import Any, Dict

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from consolekit.testing import CliRunner, Result
from domdf_python_tools.paths import PathPlus, in_directory

# this package
from tests.example_configs import (
		AUTHORS,
		CLASSIFIERS,
		COMPLETE_A,
		COMPLETE_B,
		DEPENDENCIES,
		ENTRY_POINTS,
		KEYWORDS,
		MAINTAINERS,
		MINIMAL_CONFIG,
		OPTIONAL_DEPENDENCIES,
		URLS
		)
from whey.__main__ import main


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
				]
		)
def test_cli_build_success(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "spam").mkdir()
	(tmp_pathplus / "spam" / "__init__.py").write_clean("print('hello world)")

	data: Dict[str, Any] = {}

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(main, args=["--verbose", "--no-colour", "--out-dir", str(tmp_pathplus)])

	assert result.exit_code == 0

	wheel = "spam-2020.0.0-py3-none-any.whl"
	assert (tmp_pathplus / wheel).is_file()
	zip_file = zipfile.ZipFile(tmp_pathplus / wheel)

	data["wheel_content"] = sorted(zip_file.namelist())

	with zip_file.open("spam/__init__.py", mode='r') as fp:
		assert fp.read().decode("UTF-8") == "print('hello world)\n"

	sdist = "spam-2020.0.0.tar.gz"
	assert (tmp_pathplus / sdist).is_file()

	tar = tarfile.open(tmp_pathplus / sdist)
	data["sdist_content"] = sorted(tar.getnames())

	with tar.extractfile("spam/__init__.py") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "print('hello world)\n"

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


@pytest.mark.parametrize(
		"config",
		[
				# pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_build_complete(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world)")
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	data: Dict[str, Any] = {}

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(main, args=["--verbose", "--no-colour", "--out-dir", str(tmp_pathplus)])

	assert result.exit_code == 0

	wheel = "whey-2021.0.0-py3-none-any.whl"
	assert (tmp_pathplus / wheel).is_file()
	zip_file = zipfile.ZipFile(tmp_pathplus / wheel)

	data["wheel_content"] = sorted(zip_file.namelist())

	with zip_file.open("whey/__init__.py", mode='r') as fp:
		assert fp.read().decode("UTF-8") == "print('hello world)\n"

	sdist = "whey-2021.0.0.tar.gz"
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

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


def test_build_additional_files(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
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

	data: Dict[str, Any] = {}

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(main, args=["--verbose", "--no-colour", "--out-dir", str(tmp_pathplus)])

	assert result.exit_code == 0

	wheel = "whey-2021.0.0-py3-none-any.whl"

	assert (tmp_pathplus / wheel).is_file()
	zip_file = zipfile.ZipFile(tmp_pathplus / wheel)
	data["wheel_content"] = sorted(zip_file.namelist())

	with zip_file.open("whey/__init__.py", mode='r') as fp:
		assert fp.read().decode("UTF-8") == "print('hello world)\n"

	sdist = "whey-2021.0.0.tar.gz"

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

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)
