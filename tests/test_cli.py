# stdlib
import re
import textwrap
from typing import TYPE_CHECKING, Any, Dict, List, Type

# 3rd party
import handy_archives
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
from re_assert import Matches  # type: ignore[import]

# this package
from tests.example_configs import COMPLETE_A, COMPLETE_B
from whey.__main__ import main

if TYPE_CHECKING:
	# 3rd party
	from _pytest.capture import CaptureFixture


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
		capsys: "CaptureFixture[str]",
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

	with handy_archives.ZipFile(tmp_pathplus / wheel) as zip_file:
		data["wheel_content"] = sorted(zip_file.namelist())
		assert zip_file.read_text("spam/__init__.py") == "print('hello world)\n"

	sdist = "spam-2020.0.0.tar.gz"
	assert (tmp_pathplus / sdist).is_file()

	with handy_archives.TarFile.open(tmp_pathplus / sdist) as tar:
		data["sdist_content"] = sorted(tar.getnames())
		assert tar.read_text("spam-2020.0.0/spam/__init__.py") == "print('hello world)\n"

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


def check_built_wheel(filename: PathPlus):
	assert (filename).is_file()

	with handy_archives.ZipFile(filename) as zip_file:
		assert zip_file.read_text("whey/__init__.py") == "print('hello world)\n"

		return sorted(zip_file.namelist())


def check_built_sdist(filename: PathPlus):
	assert (filename).is_file()

	with handy_archives.TarFile.open(filename) as tar:
		assert tar.read_text("whey-2021.0.0/whey/__init__.py") == "print('hello world)\n"
		assert tar.read_text("whey-2021.0.0/README.rst") == "Spam Spam Spam Spam\n"
		assert tar.read_text("whey-2021.0.0/LICENSE") == "This is the license\n"
		assert tar.read_text("whey-2021.0.0/requirements.txt") == "domdf_python_tools\n"

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
		capsys: "CaptureFixture[str]",
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
		capsys: "CaptureFixture[str]",
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
		capsys: "CaptureFixture[str]",
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
		capsys: "CaptureFixture[str]",
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
		capsys: "CaptureFixture[str]",
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
		capsys: "CaptureFixture[str]",
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
	with handy_archives.ZipFile(tmp_pathplus / wheel) as zip_file:
		data["wheel_content"] = sorted(zip_file.namelist())

		assert zip_file.read_text("whey/__init__.py") == "print('hello world)\n"
		assert zip_file.read_text("whey/style.css") == "This is the style.css file\n"

	sdist = "whey-2021.0.0.tar.gz"
	assert (tmp_pathplus / sdist).is_file()

	with handy_archives.TarFile.open(tmp_pathplus / sdist) as tar:
		data["sdist_content"] = sorted(tar.getnames())

		assert tar.read_text("whey-2021.0.0/whey/__init__.py") == "print('hello world)\n"
		assert tar.read_text("whey-2021.0.0/whey/style.css") == "This is the style.css file\n"
		assert tar.read_text("whey-2021.0.0/README.rst") == "Spam Spam Spam Spam\n"
		assert tar.read_text("whey-2021.0.0/LICENSE") == "This is the license\n"
		assert tar.read_text("whey-2021.0.0/requirements.txt") == "domdf_python_tools\n"

	data["stdout"] = result.stdout.rstrip().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)


@pytest.mark.parametrize(
		"config, match",
		[
				pytest.param(
						'[project]\nname = "spam"',
						textwrap.dedent("""\
						BadConfigError: The 'project.version' field must be provided.
						    Use '--traceback' to view the full traceback.
						Aborted!"""),
						id="no_version"
						),
				pytest.param(
						'[project]\n\nversion = "2020.0.0"',
						textwrap.dedent("""\
						BadConfigError: The 'project.name' field must be provided.
						    Use '--traceback' to view the full traceback.
						Aborted!"""),
						id="no_name"
						),
				pytest.param(
						'[project]\ndynamic = ["name"]',
						textwrap.dedent("""\
						BadConfigError: The 'project.name' field may not be dynamic.
						    Use '--traceback' to view the full traceback.
						Aborted!"""),
						id="dynamic_name"
						),
				pytest.param(
						'[project]\nname = "???????12345=============☃"\nversion = "2020.0.0"',
						re.escape(textwrap.dedent("""\
						BadConfigError: The value '???????12345=============☃' for 'project.name' is invalid.
						    Documentation: https://whey.readthedocs.io/en/latest/configuration.html#tconf-project.name
						    Use '--traceback' to view the full traceback.
						Aborted!""")),
						id="bad_name"
						),
				pytest.param(
						'[project]\nname = "spam"\nversion = "???????12345=============☃"',
						re.escape(textwrap.dedent("""\
						InvalidVersion: '???????12345=============☃'
						    Note: versions must follow PEP 440
						    Documentation: https://peps.python.org/pep-0440/
						    Use '--traceback' to view the full traceback.
						Aborted!""")),
						id="bad_version"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nrequires-python = "???????12345=============☃"',
						re.escape(textwrap.dedent("""\
						InvalidSpecifier: '???????12345=============☃'
						    Note: specifiers must follow PEP 508
						    Documentation: https://peps.python.org/pep-0508/
						    Use '--traceback' to view the full traceback.
						Aborted!""")),
						id="bad_requires_python"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nauthors = [{{name = "Bob, Alice"}}]',
						r"BadConfigError: The 'project.authors\[0\].name' key cannot contain commas.\n    Documentation: https://whey.readthedocs.io/en/latest/configuration.html#tconf-project.authors\n    Use '--traceback' to view the full traceback.\nAborted!",
						id="author_comma"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nmaintainers = [{{name = "Bob, Alice"}}]',
						r"BadConfigError: The 'project.maintainers\[0\].name' key cannot contain commas.\n    Documentation: https://whey.readthedocs.io/en/latest/configuration.html#tconf-project.maintainers\n    Use '--traceback' to view the full traceback.\nAborted!",
						id="maintainer_comma"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nkeywords = [1, 2, 3, 4, 5]',
						r"TypeError: Invalid type for 'project.keywords\[0\]': expected <class 'str'>, got <class 'int'>\n    Documentation: https://whey.readthedocs.io/en/latest/configuration.html#tconf-project.keywords\n    Use '--traceback' to view the full traceback.\nAborted!",
						id="keywords_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nclassifiers = [1, 2, 3, 4, 5]',
						r"TypeError: Invalid type for 'project.classifiers\[0\]': expected <class 'str'>, got <class 'int'>\n    Documentation: https://whey.readthedocs.io/en/latest/configuration.html#tconf-project.classifiers\n    Use '--traceback' to view the full traceback.\nAborted!",
						id="classifiers_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\ndependencies = [1, 2, 3, 4, 5]',
						r"TypeError: Invalid type for 'project.dependencies\[0\]': expected <class 'str'>, got <class 'int'>\n    Documentation: https://whey.readthedocs.io/en/latest/configuration.html#tconf-project.dependencies\n    Use '--traceback' to view the full traceback.\nAborted!",
						id="dependencies_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nreadme = "README.rst"',
						"No such file or directory: 'README.rst'\nAborted!",
						id="missing_readme_file",
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
						"No such file or directory: 'LICENSE.txt'\nAborted!",
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

	_Matches(match).assert_matches(result.stdout.rstrip())
	# assert re.match(match, result.stdout.rstrip())


# Based on https://pypi.org/project/re-assert/
# Copyright (c) 2019 Anthony Sottile
# MIT Licensed
class _Matches(Matches):

	def _fail_message(self, fail: str) -> str:
		# binary search to find the longest substring match
		pos, bound = 0, len(fail)
		while pos < bound:
			pivot = pos + (bound - pos + 1) // 2
			match = self._pattern.match(fail[:pivot], partial=True)
			if match:
				pos = pivot
			else:
				bound = pivot - 1

		retv = [f' regex: {self._pattern.pattern}', " failed to match at:", '']
		for line in fail.splitlines(True):
			line_noeol = line.rstrip('\r\n')
			retv.append(f'> {line_noeol}')
			if 0 <= pos <= len(line_noeol):
				indent = ''.join(c if c.isspace() else ' ' for c in line[:pos])
				retv.append(f'  {indent}^')
				pos = -1
			else:
				pos -= len(line)
		if pos >= 0:
			retv.append('>')
			retv.append("  ^")
		return '\n'.join(retv)


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
				pytest.param(
						["--builder", "whey_pth_wheel", "--builder", "whey_conda"],
						id="whey_conda_and_whey_pth",
						),
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
