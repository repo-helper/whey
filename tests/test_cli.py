# stdlib
import re
import tarfile
import zipfile
from typing import Any, Dict, List, Type

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from consolekit.testing import CliRunner, Result
from dom_toml.parser import BadConfigError
from domdf_python_tools.paths import PathPlus, in_directory
from pyproject_examples import bad_pep621_config
from pyproject_examples.example_configs import (
		AUTHORS,
		CLASSIFIERS,
		DEPENDENCIES,
		ENTRY_POINTS,
		KEYWORDS,
		MAINTAINERS,
		MINIMAL_CONFIG,
		OPTIONAL_DEPENDENCIES,
		URLS
		)
from pyproject_examples.utils import file_not_found_regex

# this package
from tests.example_configs import COMPLETE_A, COMPLETE_B
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

	with tar.extractfile("spam-2020.0.0/spam/__init__.py") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "print('hello world)\n"

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


def check_built_wheel(filename: PathPlus):
	assert (filename).is_file()
	zip_file = zipfile.ZipFile(filename)

	with zip_file.open("whey/__init__.py", mode='r') as fp:
		assert fp.read().decode("UTF-8") == "print('hello world)\n"

	return sorted(zip_file.namelist())


def check_built_sdist(filename: PathPlus):
	assert (filename).is_file()

	tar = tarfile.open(filename)

	with tar.extractfile("whey-2021.0.0/whey/__init__.py") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "print('hello world)\n"
	with tar.extractfile("whey-2021.0.0/README.rst") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "Spam Spam Spam Spam\n"
	with tar.extractfile("whey-2021.0.0/LICENSE") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "This is the license\n"
	with tar.extractfile("whey-2021.0.0/requirements.txt") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "domdf_python_tools\n"

	return sorted(tar.getnames())


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
	data["wheel_content"] = check_built_wheel(tmp_pathplus / wheel)

	sdist = "whey-2021.0.0.tar.gz"
	data["sdist_content"] = check_built_sdist(tmp_pathplus / sdist)

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


@pytest.mark.parametrize(
		"config", [
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_build_sdist_complete(
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
		result: Result = runner.invoke(
				main, args=["--sdist", "--verbose", "--no-colour", "--out-dir", str(tmp_pathplus)]
				)

	assert result.exit_code == 0

	sdist = "whey-2021.0.0.tar.gz"
	data["sdist_content"] = check_built_sdist(tmp_pathplus / sdist)

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


@pytest.mark.parametrize(
		"config", [
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_build_wheel_complete(
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
		result: Result = runner.invoke(
				main, args=["--wheel", "--verbose", "--no-colour", "--out-dir", str(tmp_pathplus)]
				)

	assert result.exit_code == 0

	wheel = "whey-2021.0.0-py3-none-any.whl"
	data["wheel_content"] = check_built_wheel(tmp_pathplus / wheel)

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


@pytest.mark.parametrize(
		"config", [
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_build_wheel_via_builder_complete(
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
		result: Result = runner.invoke(
				main, args=["--builder", "whey_wheel", "--verbose", "--no-colour", "--out-dir", str(tmp_pathplus)]
				)

	assert result.exit_code == 0

	wheel = "whey-2021.0.0-py3-none-any.whl"
	data["wheel_content"] = check_built_wheel(tmp_pathplus / wheel)

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


@pytest.mark.parametrize(
		"config", [
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_build_binary_complete(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		capsys,
		):

	# TODO: e.g. conda, RPM, DEB

	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world)")
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	data: Dict[str, Any] = {}

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(
				main, args=["--binary", "--verbose", "--no-colour", "--out-dir", str(tmp_pathplus)]
				)

	assert result.exit_code == 0

	wheel = "whey-2021.0.0-py3-none-any.whl"
	data["wheel_content"] = check_built_wheel(tmp_pathplus / wheel)

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
	with zip_file.open("whey/style.css", mode='r') as fp:
		assert fp.read().decode("UTF-8") == "This is the style.css file\n"

	sdist = "whey-2021.0.0.tar.gz"

	assert (tmp_pathplus / sdist).is_file()

	tar = tarfile.open(tmp_pathplus / sdist)
	data["sdist_content"] = sorted(tar.getnames())

	with tar.extractfile("whey-2021.0.0/whey/__init__.py") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "print('hello world)\n"
	with tar.extractfile("whey-2021.0.0/whey/style.css") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "This is the style.css file\n"
	with tar.extractfile("whey-2021.0.0/README.rst") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "Spam Spam Spam Spam\n"
	with tar.extractfile("whey-2021.0.0/LICENSE") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "This is the license\n"
	with tar.extractfile("whey-2021.0.0/requirements.txt") as fp:  # type: ignore
		assert fp.read().decode("UTF-8") == "domdf_python_tools\n"

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


@pytest.mark.parametrize(
		"config, match",
		[
				pytest.param(
						'[project]\nname = "spam"',
						"BadConfigError: The 'project.version' field must be provided.\nAborted!",
						id="no_version"
						),
				pytest.param(
						'[project]\n\nversion = "2020.0.0"',
						"BadConfigError: The 'project.name' field must be provided.\nAborted!",
						id="no_name"
						),
				pytest.param(
						'[project]\ndynamic = ["name"]',
						"BadConfigError: The 'project.name' field may not be dynamic.\nAborted!",
						id="dynamic_name"
						),
				pytest.param(
						'[project]\nname = "???????12345=============☃"\nversion = "2020.0.0"',
						"BadConfigError: The value for 'project.name' is invalid.\nAborted!",
						id="bad_name"
						),
				pytest.param(
						'[project]\nname = "spam"\nversion = "???????12345=============☃"',
						re.escape("BadConfigError: Invalid version: '???????12345=============☃'\nAborted!"),
						id="bad_version"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nrequires-python = "???????12345=============☃"',
						re.escape("BadConfigError: Invalid specifier: '???????12345=============☃'\nAborted!"),
						id="bad_requires_python"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nauthors = [{{name = "Bob, Alice"}}]',
						r"BadConfigError: The 'project.authors\[0\].name' key cannot contain commas.\nAborted!",
						id="author_comma"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nmaintainers = [{{name = "Bob, Alice"}}]',
						r"BadConfigError: The 'project.maintainers\[0\].name' key cannot contain commas.\nAborted!",
						id="maintainer_comma"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nkeywords = [1, 2, 3, 4, 5]',
						r"TypeError: Invalid type for 'project.keywords\[0\]': expected <class 'str'>, got <class 'int'>\nAborted!",
						id="keywords_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nclassifiers = [1, 2, 3, 4, 5]',
						r"TypeError: Invalid type for 'project.classifiers\[0\]': expected <class 'str'>, got <class 'int'>\nAborted!",
						id="classifiers_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\ndependencies = [1, 2, 3, 4, 5]',
						r"TypeError: Invalid type for 'project.dependencies\[0\]': expected <class 'str'>, got <class 'int'>\nAborted!",
						id="dependencies_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nreadme = "README.rst"',
						f"File Not Found: {file_not_found_regex('README.rst')}\nAborted!",
						id="missing_readme_file",
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
						f"File Not Found: {file_not_found_regex('LICENSE.txt')}\nAborted!",
						id="missing_license_file",
						),
				]
		)
def test_bad_config(
		config: str,
		match: str,
		tmp_pathplus: PathPlus,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(
				main,
				args=["--sdist", "--verbose", "--no-colour", "--out-dir", str(tmp_pathplus)],
				)
	assert result.exit_code == 1

	assert re.match(match, result.stdout.rstrip())


@pytest.mark.parametrize(
		"config, exception, match",
		[
				pytest.param(
						'[project]\nname = "spam"',
						BadConfigError,
						"The 'project.version' field must be provided.",
						id="no_version"
						),
				*bad_pep621_config,
				]
		)
def test_bad_config_show_traceback(
		config: str,
		exception: Type[Exception],
		match: str,
		tmp_pathplus: PathPlus,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with in_directory(tmp_pathplus):
		runner = CliRunner()

		with pytest.raises(exception, match=match):
			runner.invoke(
					main,
					args=["--sdist", "--verbose", "--no-colour", "--out-dir", str(tmp_pathplus), "-T"],
					)


@pytest.mark.parametrize(
		"config",
		[
				pytest.param(MINIMAL_CONFIG, id="default"),
				pytest.param(f'{MINIMAL_CONFIG}\n[tool.whey.builders]\nsdist = "whey_sdist"', id="sdist"),
				pytest.param(f'{MINIMAL_CONFIG}\n[tool.whey.builders]\nwheel = "whey_wheel"', id="wheel"),
				pytest.param(f'{MINIMAL_CONFIG}\n[tool.whey.builders]\nwheel = "whey_pth_wheel"', id="whey_pth"),
				pytest.param(f'{MINIMAL_CONFIG}\n[tool.whey.builders]\nbinary = "whey_wheel"', id="binary_wheel"),
				pytest.param(f'{MINIMAL_CONFIG}\n[tool.whey.builders]\nbinary = "whey_conda"', id="binary_conda"),
				pytest.param(
						f'{MINIMAL_CONFIG}\n[tool.whey.builders]\nsdist = "whey_sdist"\nwheel = "whey_wheel"',
						id="sdist_and_wheel",
						),
				]
		)
@pytest.mark.parametrize(
		"args",
		[
				pytest.param([], id="none"),
				pytest.param(["--sdist"], id="sdist"),
				pytest.param(["--wheel"], id="wheel"),
				pytest.param(["--binary"], id="binary"),
				pytest.param(["--binary", "--sdist"], id="binary_and_sdist"),
				pytest.param(["--builder", "whey_conda"], id="whey_conda"),
				pytest.param(["--builder", "whey_conda", "--sdist"], id="whey_conda_and_sdist"),
				pytest.param(["--builder", "whey_pth_wheel", "--builder", "whey_conda"], id="whey_conda_and_whey_pth"),
				]
		)
def test_show_builders(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		args: List[str]
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(
				main,
				args=[*args, "--show-builders", "--no-colour"],
				)

	result.check_stdout(advanced_file_regression)
	assert result.exit_code == 0


def test_show_builders_error(
		tmp_pathplus: PathPlus,
		advanced_file_regression: AdvancedFileRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(MINIMAL_CONFIG)

	with in_directory(tmp_pathplus):
		runner = CliRunner()
		result: Result = runner.invoke(
				main,
				args=["--builder", "foo", "--show-builders", "--no-colour"],
				)

	result.check_stdout(advanced_file_regression)
	assert result.exit_code == 2
