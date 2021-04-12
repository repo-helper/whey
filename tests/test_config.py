# stdlib
import re
from textwrap import dedent
from typing import Type

# 3rd party
import dom_toml
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from dom_toml.parser import BadConfigError
from domdf_python_tools.compat import PYPY37
from domdf_python_tools.paths import PathPlus, in_directory

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
from whey.builder import AbstractBuilder
from whey.config import PEP621Parser, load_toml

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
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]

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
keywords = [ "pep517", "pep621", "build", "sdist", "wheel", "packaging", "distribution",]
dynamic = [ "classifiers", "requires-python",]
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]

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
additional-files = [
  "include whey/style.css",
]
"""


def check_config(config, data_regression: AdvancedDataRegressionFixture):
	assert "builders" in config
	builders = config.pop("builders")
	assert all(isinstance(name, str) for name in builders)
	assert all(issubclass(name, AbstractBuilder) for name in builders.values())

	if "requires-python" in config and config["requires-python"] is not None:
		config["requires-python"] = str(config["requires-python"])
	if "version" in config and config["version"] is not None:
		config["version"] = str(config["version"])

	data_regression.check(config)


@pytest.mark.parametrize(
		"toml_config",
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
				pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_parse_valid_config(
		toml_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)
	config = load_toml(tmp_pathplus / "pyproject.toml")

	if "dependencies" in config:
		config["dependencies"] = list(map(str, config["dependencies"]))
	if "optional-dependencies" in config:
		config["optional-dependencies"] = {
				k: list(map(str, v))
				for k, v in config["optional-dependencies"].items()
				}

	check_config(config, advanced_data_regression)


@pytest.mark.parametrize(
		"toml_config",
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
				pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_pep621_class_valid_config(
		toml_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)

	with in_directory(tmp_pathplus):
		config = PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])

	if "dependencies" in config:
		config["dependencies"] = list(map(str, config["dependencies"]))
	if "optional-dependencies" in config:
		config["optional-dependencies"] = {
				k: list(map(str, v))
				for k, v in config["optional-dependencies"].items()
				}

	if "requires-python" in config and config["requires-python"] is not None:
		config["requires-python"] = str(config["requires-python"])
	if "version" in config and config["version"] is not None:
		config["version"] = str(config["version"])

	advanced_data_regression.check(config)


@pytest.mark.parametrize("filename", ["README.rst", "README.md", "INTRODUCTION.md", "readme.txt"])
def test_parse_valid_config_readme(
		filename: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			f'readme = {filename!r}',
			])
	(tmp_pathplus / filename).write_text("This is the readme.")

	config = load_toml(tmp_pathplus / "pyproject.toml")

	check_config(config, advanced_data_regression)


@pytest.mark.parametrize(
		"readme",
		[
				pytest.param('readme = {file = "README.rst"}', id="rst_file"),
				pytest.param('readme = {file = "README.md"}', id="md_file"),
				pytest.param('readme = {file = "README.txt"}', id="txt_file"),
				pytest.param(
						'readme = {text = "This is the inline README README.", content-type = "text/x-rst"}',
						id="text_content_type_rst"
						),
				pytest.param(
						'readme = {text = "This is the inline markdown README.", content-type = "text/markdown"}',
						id="text_content_type_md"
						),
				pytest.param(
						'readme = {text = "This is the inline README.", content-type = "text/plain"}',
						id="text_content_type_plain"
						),
				]
		)
def test_parse_valid_config_readme_dict(
		readme,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			readme,
			])
	(tmp_pathplus / "README.rst").write_text("This is the reStructuredText README.")
	(tmp_pathplus / "README.md").write_text("This is the markdown README.")
	(tmp_pathplus / "README.txt").write_text("This is the plaintext README.")
	(tmp_pathplus / "README").write_text("This is the README.")

	config = load_toml(tmp_pathplus / "pyproject.toml")
	check_config(config, advanced_data_regression)


@pytest.mark.parametrize(
		"readme, expected",
		[
				pytest.param("readme = {}", "The 'project.readme' table cannot be empty.", id="empty"),
				pytest.param(
						"readme = {fil = 'README.md'}",
						"Unknown format for 'project.readme': {'fil': 'README.md'}",
						id="unknown_key",
						),
				pytest.param(
						'readme = {text = "This is the inline README."}',
						"The 'project.readme.content-type' key must be provided when 'project.readme.text' is given.",
						id="text_only"
						),
				pytest.param(
						'readme = {content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						id="content_type_only"
						),
				pytest.param(
						'readme = {charset = "cp1252"}',
						"The 'project.readme.charset' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						id="charset_only"
						),
				pytest.param(
						'readme = {charset = "cp1252", content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						id="content_type_charset"
						),
				pytest.param(
						'readme = {text = "This is the inline README", content-type = "application/x-abiword"}',
						"Unrecognised value for 'project.readme.content-type': 'application/x-abiword'",
						id="bad_content_type"
						),
				pytest.param(
						'readme = {file = "README"}', "Unrecognised filetype for 'README'", id="no_extension"
						),
				pytest.param(
						'readme = {file = "README.doc"}',
						"Unrecognised filetype for 'README.doc'",
						id="bad_extension"
						),
				pytest.param(
						'readme = {file = "README.doc", text = "This is the README"}',
						"The 'project.readme.file' and 'project.readme.text' keys are mutually exclusive.",
						id="file_and_readme"
						),
				]
		)
def test_bad_config_readme_dict(
		readme: str,
		expected: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			readme,
			])

	with pytest.raises(BadConfigError, match=expected):
		load_toml(tmp_pathplus / "pyproject.toml")


@pytest.mark.parametrize(
		"readme, expected",
		[
				pytest.param("readme = {}", "The 'project.readme' table cannot be empty.", id="empty"),
				pytest.param(
						"readme = {fil = 'README.md'}",
						"Unknown format for 'project.readme': {'fil': 'README.md'}",
						id="unknown_key",
						),
				pytest.param(
						'readme = {text = "This is the inline README."}',
						"The 'project.readme.content-type' key must be provided when 'project.readme.text' is given.",
						id="text_only"
						),
				pytest.param(
						'readme = {content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						id="content_type_only"
						),
				pytest.param(
						'readme = {charset = "cp1252"}',
						"The 'project.readme.charset' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						id="charset_only"
						),
				pytest.param(
						'readme = {charset = "cp1252", content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						id="content_type_charset"
						),
				pytest.param(
						'readme = {text = "This is the inline README", content-type = "application/x-abiword"}',
						"Unrecognised value for 'project.readme.content-type': 'application/x-abiword'",
						id="bad_content_type"
						),
				pytest.param(
						'readme = {file = "README"}', "Unrecognised filetype for 'README'", id="no_extension"
						),
				pytest.param(
						'readme = {file = "README.doc"}',
						"Unrecognised filetype for 'README.doc'",
						id="bad_extension"
						),
				pytest.param(
						'readme = {file = "README.doc", text = "This is the README"}',
						"The 'project.readme.file' and 'project.readme.text' keys are mutually exclusive.",
						id="file_and_readme"
						),
				]
		)
def test_pep621parser_class_bad_config(
		readme: str,
		expected: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			readme,
			])

	with in_directory(tmp_pathplus), pytest.raises(BadConfigError, match=expected):
		PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])


def test_parse_builders(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	toml_config = dedent(
			"""
[project]
name = "whey"
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
keywords = [ "pep517", "pep621", "build", "sdist", "wheel", "packaging", "distribution",]
dynamic = [ "classifiers", "requires-python",]

[tool.whey]
base-classifiers = [ "Development Status :: 4 - Beta",]
python-versions = [ "3.6", "3.7", "3.8", "3.9", "3.10",]
python-implementations = [ "CPython", "PyPy",]
platforms = [ "Windows", "macOS", "Linux",]
license-key = "MIT"

[tool.whey.builders]
sdist = "whey_sdist"
wheel = "whey_wheel"

"""
			)
	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)
	config = load_toml(tmp_pathplus / "pyproject.toml")

	check_config(config, advanced_data_regression)


def test_parse_dynamic_requirements(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	toml_config = dedent(
			"""
[project]
name = "whey"
version = "2021.0.0"
description = "A simple Python wheel builder for simple projects."
keywords = [ "pep517", "pep621", "build", "sdist", "wheel", "packaging", "distribution",]
dynamic = [ "classifiers", "requires-python", "dependencies",]

[tool.whey]
base-classifiers = [ "Development Status :: 4 - Beta",]
python-versions = [ "3.6", "3.7", "3.8", "3.9", "3.10",]
python-implementations = [ "CPython", "PyPy",]
platforms = [ "Windows", "macOS", "Linux",]
license-key = "MIT"
"""
			)
	(tmp_pathplus / "pyproject.toml").write_clean(toml_config)
	(tmp_pathplus / "requirements.txt").write_lines([
			"apeye>=0.7.0",
			"click>=7.1.2",
			"consolekit>=1.0.1",
			"domdf-python-tools>=2.5.2",
			"email-validator>=1.1.2",
			"first>=2.0.2",
			"natsort>=7.1.1",
			"packaging>=20.9",
			"readme-renderer[md]>=28.0",
			"shippinglabel>=0.10.0",
			"toml>=0.10.2",
			])

	config = load_toml(tmp_pathplus / "pyproject.toml")

	if "dependencies" in config:
		config["dependencies"] = list(map(str, config["dependencies"]))

	check_config(config, advanced_data_regression)


@pytest.mark.parametrize("filename", ["LICENSE.rst", "LICENSE.md", "LICENSE.txt", "LICENSE"])
def test_parse_valid_config_license(
		filename: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			f'[project]',
			f'name = "spam"',
			f'version = "2020.0.0"',
			f'license = {{file = "{filename}"}}',
			])
	(tmp_pathplus / filename).write_text("This is the license.")

	config = load_toml(tmp_pathplus / "pyproject.toml")
	check_config(config, advanced_data_regression)


def test_parse_valid_config_license_text(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			f'[project]',
			f'name = "spam"',
			f'version = "2020.0.0"',
			f'license = {{text = "This is the MIT License"}}',
			])

	config = load_toml(tmp_pathplus / "pyproject.toml")
	check_config(config, advanced_data_regression)


@pytest.mark.parametrize(
		"license_key, expected",
		[
				pytest.param(
						"license = {}",
						"The 'project.license' table should contain one of 'text' or 'file'.",
						id="empty"
						),
				pytest.param(
						'license = {text = "MIT", file = "LICENSE.txt"}',
						"The 'project.license.file' and 'project.license.text' keys are mutually exclusive.",
						id="double_license"
						),
				]
		)
def test_bad_config_license(
		license_key: str,
		expected: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			f'[project]',
			f'name = "spam"',
			f'version = "2020.0.0"',
			license_key,
			])

	with pytest.raises(BadConfigError, match=expected):
		load_toml(tmp_pathplus / "pyproject.toml")


@pytest.mark.parametrize(
		"config, expects, match",
		[
				pytest.param('', KeyError, "'project' table not found in '.*'", id="no_config"),
				pytest.param(
						'[project]\nname = "spam"',
						BadConfigError,
						"The 'project.version' field must be provided.",
						id="no_version"
						),
				pytest.param(
						'[project]\n\nversion = "2020.0.0"',
						BadConfigError,
						"The 'project.name' field must be provided.",
						id="no_name"
						),
				pytest.param(
						'[project]\ndynamic = ["name"]',
						BadConfigError,
						"The 'project.name' field may not be dynamic.",
						id="dynamic_name"
						),
				pytest.param(
						'[project]\nname = "???????12345=============☃"\nversion = "2020.0.0"',
						BadConfigError,
						"The value for 'project.name' is invalid.",
						id="bad_name"
						),
				pytest.param(
						'[project]\nname = "spam"\nversion = "???????12345=============☃"',
						BadConfigError,
						re.escape("Invalid version: '???????12345=============☃'"),
						id="bad_version"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nrequires-python = "???????12345=============☃"',
						BadConfigError,
						re.escape("Invalid specifier: '???????12345=============☃'"),
						id="bad_requires_python"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nauthors = [{{name = "Bob, Alice"}}]',
						BadConfigError,
						r"The 'project.authors\[0\].name' key cannot contain commas.",
						id="author_comma"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nmaintainers = [{{name = "Bob, Alice"}}]',
						BadConfigError,
						r"The 'project.maintainers\[0\].name' key cannot contain commas.",
						id="maintainer_comma"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nkeywords = [1, 2, 3, 4, 5]',
						TypeError,
						r"Invalid type for 'project.keywords\[0\]': expected <class 'str'>, got <class 'int'>",
						id="keywords_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nclassifiers = [1, 2, 3, 4, 5]',
						TypeError,
						r"Invalid type for 'project.classifiers\[0\]': expected <class 'str'>, got <class 'int'>",
						id="classifiers_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\ndependencies = [1, 2, 3, 4, 5]',
						TypeError,
						r"Invalid type for 'project.dependencies\[0\]': expected <class 'str'>, got <class 'int'>",
						id="dependencies_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nreadme = "README.rst"',
						FileNotFoundError,
						"No such file or directory: 'README.rst'",
						id="missing_readme_file",
						marks=pytest.mark.skipif(PYPY37, reason="Message differs on PyPy 3.7")
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
						FileNotFoundError,
						"No such file or directory: 'LICENSE.txt'",
						id="missing_license_file",
						marks=pytest.mark.skipif(PYPY37, reason="Message differs on PyPy 3.7")
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nreadme = "README.rst"',
						FileNotFoundError,
						r"No such file or directory: .*PathPlus\('README.rst'\)",
						id="missing_readme_file",
						marks=pytest.mark.skipif(not PYPY37, reason="Message differs on PyPy 3.7")
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
						FileNotFoundError,
						r"No such file or directory: .*PathPlus\('LICENSE.txt'\)",
						id="missing_license_file",
						marks=pytest.mark.skipif(not PYPY37, reason="Message differs on PyPy 3.7")
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\ndynamic = ["dependencies"]',
						BadConfigError,
						"'project.dependencies' was listed as a dynamic field but no 'requirements.txt' file was found.",
						id="missing_dynamic_requirements"
						),
				]
		)
def test_parse_config_errors(config: str, expects: Type[Exception], match: str, tmp_pathplus: PathPlus):
	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with pytest.raises(expects, match=match):
		load_toml(tmp_pathplus / "pyproject.toml")


@pytest.mark.parametrize(
		"config, expects, match",
		[
				pytest.param(
						'[project]\nname = "spam"',
						BadConfigError,
						"The 'project.version' field must be provided.",
						id="no_version"
						),
				pytest.param(
						'[project]\n\nversion = "2020.0.0"',
						BadConfigError,
						"The 'project.name' field must be provided.",
						id="no_name"
						),
				pytest.param(
						'[project]\ndynamic = ["name"]',
						BadConfigError,
						"The 'project.name' field may not be dynamic.",
						id="dynamic_name"
						),
				pytest.param(
						'[project]\nname = "???????12345=============☃"\nversion = "2020.0.0"',
						BadConfigError,
						"The value for 'project.name' is invalid.",
						id="bad_name"
						),
				pytest.param(
						'[project]\nname = "spam"\nversion = "???????12345=============☃"',
						BadConfigError,
						re.escape("Invalid version: '???????12345=============☃'"),
						id="bad_version"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nrequires-python = "???????12345=============☃"',
						BadConfigError,
						re.escape("Invalid specifier: '???????12345=============☃'"),
						id="bad_requires_python"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nauthors = [{{name = "Bob, Alice"}}]',
						BadConfigError,
						r"The 'project.authors\[0\].name' key cannot contain commas.",
						id="author_comma"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nmaintainers = [{{name = "Bob, Alice"}}]',
						BadConfigError,
						r"The 'project.maintainers\[0\].name' key cannot contain commas.",
						id="maintainer_comma"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nkeywords = [1, 2, 3, 4, 5]',
						TypeError,
						r"Invalid type for 'project.keywords\[0\]': expected <class 'str'>, got <class 'int'>",
						id="keywords_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nclassifiers = [1, 2, 3, 4, 5]',
						TypeError,
						r"Invalid type for 'project.classifiers\[0\]': expected <class 'str'>, got <class 'int'>",
						id="classifiers_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\ndependencies = [1, 2, 3, 4, 5]',
						TypeError,
						r"Invalid type for 'project.dependencies\[0\]': expected <class 'str'>, got <class 'int'>",
						id="dependencies_wrong_type"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nreadme = "README.rst"',
						FileNotFoundError,
						"No such file or directory: 'README.rst'",
						id="missing_readme_file",
						marks=pytest.mark.skipif(PYPY37, reason="Message differs on PyPy 3.7")
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
						FileNotFoundError,
						"No such file or directory: 'LICENSE.txt'",
						id="missing_license_file",
						marks=pytest.mark.skipif(PYPY37, reason="Message differs on PyPy 3.7")
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nreadme = "README.rst"',
						FileNotFoundError,
						r"No such file or directory: .*PathPlus\('README.rst'\)",
						id="missing_readme_file",
						marks=pytest.mark.skipif(not PYPY37, reason="Message differs on PyPy 3.7")
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
						FileNotFoundError,
						r"No such file or directory: .*PathPlus\('LICENSE.txt'\)",
						id="missing_license_file",
						marks=pytest.mark.skipif(not PYPY37, reason="Message differs on PyPy 3.7")
						),
				]
		)
def test_pep621parser_class_errors(config: str, expects: Type[Exception], match: str, tmp_pathplus: PathPlus):
	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with in_directory(tmp_pathplus), pytest.raises(expects, match=match):
		PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"])


@pytest.mark.parametrize("filename", ["README", "README.rtf"])
def test_parse_config_readme_errors(filename: str, tmp_pathplus: PathPlus):
	config = dedent(f"""
[project]
name = "spam"
version = "2020.0.0"
readme = "{filename}"
""")
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / filename).write_text("This is the readme.")

	with pytest.raises(ValueError, match=f"Unrecognised filetype for '{filename}'"):
		load_toml(tmp_pathplus / "pyproject.toml")
