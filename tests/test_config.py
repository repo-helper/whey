# stdlib
from textwrap import dedent
from typing import Any, Dict, List, Optional, Type, Union, cast

# 3rd party
import dom_toml
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from dom_toml.parser import BadConfigError
from domdf_python_tools.paths import PathPlus, in_directory
from packaging.markers import Marker
from packaging.requirements import InvalidRequirement
from packaging.version import Version
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
		UNICODE,
		URLS
		)
from pyproject_parser.classes import License, Readme
from pyproject_parser.type_hints import Author, Dynamic
from shippinglabel.requirements import ComparableRequirement
from typing_extensions import TypedDict

# this package
from whey.builder import AbstractBuilder
from whey.config import PEP621Parser, backfill_classifiers, load_toml

COMPLETE_PROJECT_A = """\
[project]
name = "spam"
version = "2020.0.0"
description = "Lovely Spam! Wonderful Spam!"
requires-python = ">=3.8"
keywords = ["egg", "bacon", "sausage", "tomatoes", "Lobster Thermidor"]
authors = [
  {email = "hi@pradyunsg.me"},
  {name = "Tzu-ping Chung"}
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


def check_config(
		config: Dict[str, Any],
		data_regression: AdvancedDataRegressionFixture,
		):
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


ProjectDictPureClasses = TypedDict(
		"ProjectDictPureClasses",
		{
				"name": str,
				"version": Union[Version, str, None],
				"description": Optional[str],
				"readme": Optional[Readme],
				"requires-python": Union[Marker, str, None],
				"license": Optional[License],
				"authors": List[Author],
				"maintainers": List[Author],
				"keywords": List[str],
				"classifiers": List[str],
				"urls": Dict[str, str],
				"scripts": Dict[str, str],
				"gui-scripts": Dict[str, str],
				"entry-points": Dict[str, Dict[str, str]],
				"dependencies": Union[List[ComparableRequirement], List[str]],
				"optional-dependencies": Union[Dict[str, List[ComparableRequirement]], Dict[str, List[str]]],
				"dynamic": List[Dynamic],
				}
		)


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
		config = cast(
				ProjectDictPureClasses,
				PEP621Parser().parse(dom_toml.load(tmp_pathplus / "pyproject.toml")["project"]),
				)

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
		readme: str,
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


_bad_readmes = pytest.mark.parametrize(
		"readme, expected, exception",
		[
				pytest.param(
						"readme = {}", "The 'project.readme' table cannot be empty.", BadConfigError, id="empty"
						),
				pytest.param(
						"readme = {fil = 'README.md'}",
						"Unknown format for 'project.readme': {'fil': 'README.md'}",
						BadConfigError,
						id="unknown_key",
						),
				pytest.param(
						'readme = {text = "This is the inline README."}',
						"The 'project.readme.content-type' key must be provided when 'project.readme.text' is given.",
						BadConfigError,
						id="text_only"
						),
				pytest.param(
						'readme = {content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						BadConfigError,
						id="content_type_only"
						),
				pytest.param(
						'readme = {charset = "cp1252"}',
						"The 'project.readme.charset' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						BadConfigError,
						id="charset_only"
						),
				pytest.param(
						'readme = {charset = "cp1252", content-type = "text/x-rst"}',
						"The 'project.readme.content-type' key cannot be provided on its own; "
						"Please provide the 'project.readme.text' key too.",
						BadConfigError,
						id="content_type_charset"
						),
				pytest.param(
						'readme = {text = "This is the inline README", content-type = "application/x-abiword"}',
						"Unrecognised value for 'project.readme.content-type': 'application/x-abiword'",
						BadConfigError,
						id="bad_content_type"
						),
				pytest.param(
						'readme = {file = "README"}',
						"Unsupported extension for 'README'",
						ValueError,
						id="no_extension"
						),
				pytest.param(
						'readme = {file = "README.doc"}',
						"Unsupported extension for 'README.doc'",
						ValueError,
						id="bad_extension"
						),
				pytest.param(
						'readme = {file = "README.doc", text = "This is the README"}',
						"The 'project.readme.file' and 'project.readme.text' keys are mutually exclusive.",
						BadConfigError,
						id="file_and_readme"
						),
				]
		)


@_bad_readmes
def test_bad_config_readme_dict(
		readme: str,
		expected: str,
		exception: Type[Exception],
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			readme,
			])

	with pytest.raises(exception, match=expected):
		load_toml(tmp_pathplus / "pyproject.toml")


@_bad_readmes
def test_pep621parser_class_bad_config(
		readme: str,
		expected: str,
		exception: Type[Exception],
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		):

	(tmp_pathplus / "pyproject.toml").write_lines([
			"[project]",
			'name = "spam"',
			'version = "2020.0.0"',
			readme,
			])

	with in_directory(tmp_pathplus), pytest.raises(exception, match=expected):
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


def test_parse_dynamic_requirements_invalid(tmp_pathplus: PathPlus, ):
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
			"# a comment",
			"click>=7.1.2",
			"consolekit>=1.0.1",
			"not a requirement",
			])

	with pytest.raises(InvalidRequirement, match="not a requirement"):
		load_toml(tmp_pathplus / "pyproject.toml")


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
				*bad_pep621_config,
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
				*bad_pep621_config,
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

	with pytest.raises(ValueError, match=f"Unsupported extension for '{filename}'"):
		load_toml(tmp_pathplus / "pyproject.toml")


_backfill_base_dict: Dict[str, Any] = {
		"base-classifiers": [],
		"source-dir": '.',
		"license-key": None,
		"platforms": None,
		"python-versions": None,
		"python-implementations": None,
		}


@pytest.mark.parametrize(
		"config",
		[
				pytest.param(_backfill_base_dict, id="defaults"),
				pytest.param({**_backfill_base_dict, "platforms": ["Windows"]}, id="Windows"),
				pytest.param({**_backfill_base_dict, "platforms": ["macOS"]}, id="macOS"),
				pytest.param({**_backfill_base_dict, "platforms": ["Linux"]}, id="Linux"),
				pytest.param({**_backfill_base_dict, "platforms": ["BSD"]}, id="BSD"),
				pytest.param(
						{**_backfill_base_dict, "platforms": ["Windows", "Linux"]},
						id="Multiple Platforms_1",
						),
				pytest.param(
						{**_backfill_base_dict, "platforms": ["macOS", "Linux"]},
						id="Multiple Platforms_2",
						),
				pytest.param(
						{**_backfill_base_dict, "platforms": ["Windows", "macOS", "Linux"]},
						id="All Platforms",
						),
				pytest.param({**_backfill_base_dict, "python-versions": ["3.6"]}, id="py36"),
				pytest.param({**_backfill_base_dict, "python-versions": ["3.7"]}, id="py37"),
				pytest.param({**_backfill_base_dict, "python-versions": ["3.8"]}, id="py38"),
				pytest.param({**_backfill_base_dict, "python-versions": ["3.9"]}, id="py39"),
				pytest.param(
						{**_backfill_base_dict, "python-versions": ["3.6", "3.8", "3.9"]},
						id="multiple_py_versions",
						),
				pytest.param(
						{**_backfill_base_dict, "python-implementations": ["CPython"]},
						id="CPython",
						),
				pytest.param(
						{**_backfill_base_dict, "python-implementations": ["PyPy"]},
						id="PyPy",
						),
				pytest.param(
						{**_backfill_base_dict, "python-implementations": ["CPython", "PyPy"]},
						id="Multiple Implementations",
						),
				pytest.param(
						{**_backfill_base_dict, "python-implementations": ["GraalPython"]},
						id="GraalPython",
						),
				pytest.param({**_backfill_base_dict, "license-key": "MIT"}, id="MIT License"),
				pytest.param({**_backfill_base_dict, "license-key": "GPLv2"}, id="GPLv2"),
				pytest.param(
						{**_backfill_base_dict, "license-key": "LGPL-3.0-or-later"},
						id="LGPL-3.0-or-later",
						),
				]
		)
def test_backfill_classifiers(config: Dict[str, str], advanced_data_regression: AdvancedDataRegressionFixture):
	advanced_data_regression.check(backfill_classifiers(config))


@pytest.mark.parametrize(
		"config, match",
		[
				pytest.param(
						f"{MINIMAL_CONFIG}\ndynamic = ['version']",
						"Unsupported dynamic field 'version'.\nnote: whey only supports .* as dynamic fields.",
						id="version"
						),
				pytest.param(
						f"{MINIMAL_CONFIG}\ndynamic = ['optional-dependencies']",
						"Unsupported dynamic field 'optional-dependencies'.\nnote: whey only supports .* as dynamic fields.",
						id="optional-dependencies"
						),
				pytest.param(
						f"{MINIMAL_CONFIG}\ndynamic = ['authors']",
						"Unsupported dynamic field 'authors'.\nnote: whey only supports .* as dynamic fields.",
						id="authors"
						),
				pytest.param(
						f"{MINIMAL_CONFIG}\ndynamic = ['keywords']",
						"Unsupported dynamic field 'keywords'.\nnote: whey only supports .* as dynamic fields.",
						id="keywords"
						),
				pytest.param(
						f"{MINIMAL_CONFIG}\ndependencies = ['foo']\ndynamic = ['dependencies']",
						"'dependencies' was listed in 'project.dynamic' but a value was given.",
						id="dynamic_but_given"
						),
				]
		)
def test_bad_config_dynamic(
		config: str,
		match: str,
		tmp_pathplus: PathPlus,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(config)

	with pytest.raises(BadConfigError, match=match):
		load_toml(tmp_pathplus / "pyproject.toml")


@pytest.mark.parametrize(
		"config, exception, match",
		[
				pytest.param(
						"package = 1234",
						TypeError,
						"Invalid type for 'tool.whey.package': expected <class 'str'>, got <class 'int'>",
						id="package-int"
						),
				pytest.param(
						"package = ['spam', 'eggs']",
						TypeError,
						"Invalid type for 'tool.whey.package': expected <class 'str'>, got <class 'list'>",
						id="package-list"
						),
				pytest.param(
						"source-dir = 1234",
						TypeError,
						"Invalid type for 'tool.whey.source-dir': expected <class 'str'>, got <class 'int'>",
						id="source-dir-int"
						),
				pytest.param(
						"source-dir = ['spam', 'eggs']",
						TypeError,
						"Invalid type for 'tool.whey.source-dir': expected <class 'str'>, got <class 'list'>",
						id="source-dir-list"
						),
				pytest.param(
						"license-key = 1234",
						TypeError,
						"Invalid type for 'tool.whey.license-key': expected <class 'str'>, got <class 'int'>",
						id="license-key-int"
						),
				pytest.param(
						"license-key = ['MIT', 'Apache2']",
						TypeError,
						"Invalid type for 'tool.whey.license-key': expected <class 'str'>, got <class 'list'>",
						id="license-key-list"
						),
				pytest.param(
						"license-key = {file = 'LICENSE'}",
						TypeError,
						"Invalid type for 'tool.whey.license-key': expected <class 'str'>, got <class 'dict'>",
						id="license-key-dict"
						),
				# pytest.param(
				# 		"additional-files = 'include foo.bar'",
				# 		TypeError,
				# 		"Invalid type for 'tool.whey.additional-files': expected <class 'str'>, got <class 'dict'>",
				# 		id="additional-files-dict"
				# 		),
				pytest.param(
						"python-versions = ['2.7']",
						BadConfigError,
						r"Invalid value for 'tool.whey.python-versions\[0\]': whey only supports Python 3-only projects.",
						id="python-versions-2.7-string"
						),
				pytest.param(
						"python-versions = [2.7]",
						BadConfigError,
						r"Invalid value for 'tool.whey.python-versions\[0\]': whey only supports Python 3-only projects.",
						id="python-versions-2.7-float"
						),
				pytest.param(
						"python-versions = ['1.6']",
						BadConfigError,
						r"Invalid value for 'tool.whey.python-versions\[0\]': whey only supports Python 3-only projects.",
						id="python-versions-1.6-string"
						),
				]
		)
def test_bad_config_whey_table(
		config: str,
		exception: Type[Exception],
		match: str,
		tmp_pathplus: PathPlus,
		):

	(tmp_pathplus / "pyproject.toml").write_clean(f"{MINIMAL_CONFIG}\n[tool.whey]\n{config}")

	with pytest.raises(exception, match=match):
		load_toml(tmp_pathplus / "pyproject.toml")
