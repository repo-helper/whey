# stdlib
import re
from textwrap import dedent
from typing import Iterable, Type

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from domdf_python_tools.paths import PathPlus

# this package
from whey.config import AbstractConfigParser, BadConfigError, construct_path, load_toml

MINIMAL_CONFIG = '[project]\nname = "spam"\nversion = "2020.0.0"'

KEYWORDS = f"""\
{MINIMAL_CONFIG}
keywords = ["egg", "bacon", "sausage", "tomatoes", "Lobster Thermidor"]
"""

AUTHORS = f"""\
{MINIMAL_CONFIG}
authors = [
  {{email = "hi@pradyunsg.me"}},
  {{name = "Tzu-Ping Chung"}}
]
"""

MAINTAINERS = f"""\
{MINIMAL_CONFIG}
maintainers = [
  {{name = "Brett Cannon", email = "brett@python.org"}}
]
"""

CLASSIFIERS = f"""\
{MINIMAL_CONFIG}
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python"
]
"""

DEPENDENCIES = f"""\
{MINIMAL_CONFIG}
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]
"""

OPTIONAL_DEPENDENCIES = f"""\
{MINIMAL_CONFIG}

[project.optional-dependencies]
test = [
  "pytest < 5.0.0",
  "pytest-cov[all]"
]
"""

URLS = f"""\
{MINIMAL_CONFIG}

[project.urls]
homepage = "example.com"
documentation = "readthedocs.org"
repository = "github.com"
changelog = "github.com/me/spam/blob/master/CHANGELOG.md"
"""

ENTRY_POINTS = f"""\
{MINIMAL_CONFIG}

[project.scripts]
spam-cli = "spam:main_cli"

[project.gui-scripts]
spam-gui = "spam:main_gui"

[project.entry-points."spam.magical"]
tomatoes = "spam:main_tomatoes"
"""

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
platform = [ "Windows", "macOS", "Linux",]
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
				pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				]
		)
def test_parse_valid_config(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	config = load_toml(tmp_pathplus / "pyproject.toml")

	config["version"] = str(config["version"])

	if "requires-python" in config:
		config["requires-python"] = str(config["requires-python"])
	if "dependencies" in config:
		config["dependencies"] = list(map(str, config["dependencies"]))
	if "optional-dependencies" in config:
		config["optional-dependencies"] = {
				k: list(map(str, v))
				for k, v in config["optional-dependencies"].items()
				}

	advanced_data_regression.check(config)


@pytest.mark.parametrize("filename", ["README.rst", "README.md", "INTRODUCTION.md", "readme.txt"])
def test_parse_valid_config_readme(
		filename: str, tmp_pathplus: PathPlus, advanced_data_regression: AdvancedDataRegressionFixture
		):
	config = dedent(f"""
[project]
name = "spam"
version = "2020.0.0"
readme = "{filename}"
""")
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / filename).write_text("This is the readme.")

	config = load_toml(tmp_pathplus / "pyproject.toml")

	config["version"] = str(config["version"])

	advanced_data_regression.check(config)


def test_parse_dynamic_requirements(
		tmp_pathplus: PathPlus, advanced_data_regression: AdvancedDataRegressionFixture
		):
	config = dedent(
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
platform = [ "Windows", "macOS", "Linux",]
license-key = "MIT"

"""
			)
	(tmp_pathplus / "pyproject.toml").write_clean(config)
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

	config["version"] = str(config["version"])
	if "requires-python" in config:
		config["requires-python"] = str(config["requires-python"])
	if "dependencies" in config:
		config["dependencies"] = list(map(str, config["dependencies"]))

	advanced_data_regression.check(config)


@pytest.mark.parametrize("filename", ["LICENSE.rst", "LICENSE.md", "LICENSE.txt", "LICENSE"])
def test_parse_valid_config_license(
		filename: str, tmp_pathplus: PathPlus, advanced_data_regression: AdvancedDataRegressionFixture
		):
	config = dedent(f"""
[project]
name = "spam"
version = "2020.0.0"
license = {{file = "{filename}"}}
""")
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / filename).write_text("This is the license.")

	config = load_toml(tmp_pathplus / "pyproject.toml")

	config["version"] = str(config["version"])

	advanced_data_regression.check(config)


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
						f'{MINIMAL_CONFIG}\nlicense = {{text = "MIT", file = "LICENSE.txt"}}',
						BadConfigError,
						"The 'project.license.file' and 'project.license.text' keys are mutually exclusive.",
						id="double_license"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nlicense = {{}}',
						BadConfigError,
						"The 'project.license' table should contain one of 'text' or 'file'.",
						id="empty_license"
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
						id="missing_readme_file"
						),
				pytest.param(
						f'{MINIMAL_CONFIG}\nlicense = {{file = "LICENSE.txt"}}',
						FileNotFoundError,
						"No such file or directory: 'LICENSE.txt'",
						id="missing_license_file"
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


@pytest.mark.parametrize(
		"path, expected",
		[
				(["foo"], "foo"),
				(iter(["foo"]), "foo"),
				(("foo", ), "foo"),
				(["foo", "bar"], "foo.bar"),
				(iter(["foo", "bar"]), "foo.bar"),
				(("foo", "bar"), "foo.bar"),
				(["foo", "hello world"], 'foo."hello world"'),
				(iter(["foo", "hello world"]), 'foo."hello world"'),
				(("foo", "hello world"), 'foo."hello world"'),
				]
		)
def test_construct_path(path: Iterable[str], expected: str):
	assert construct_path(path) == expected


@pytest.mark.parametrize("what", ["type", "key type", "value type"])
@pytest.mark.parametrize("expected_type", [str, int, dict])
def test_assert_type(what: str, expected_type: Type):
	with pytest.raises(
			TypeError,
			match=f"Invalid {what} for 'foo.\"hello world\"': expected {expected_type!r}, got <class 'list'>"
			):
		AbstractConfigParser.assert_type([], expected_type, ["foo", "hello world"], what=what)
