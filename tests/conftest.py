# stdlib
from typing import Callable, Type, TypeVar, Union

# 3rd party
import pytest
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
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
from pytest_regressions.data_regression import RegressionYamlDumper

# this package
from whey.additional_files import AdditionalFilesEntry

_C = TypeVar("_C", bound=Callable)

pytest_plugins = ("coincidence", )


def _representer_for(*data_type: Type) -> Callable[[_C], _C]:

	def deco(representer_fn: _C) -> _C:
		for dtype in data_type:
			RegressionYamlDumper.add_custom_yaml_representer(dtype, representer_fn)

		return representer_fn

	return deco


@_representer_for(str, Version, Requirement, Marker, SpecifierSet)
def represent_packaging_types(  # noqa: MAN002
		dumper: RegressionYamlDumper,
		data: Union[Version, Requirement, Marker, SpecifierSet],
		):
	return dumper.represent_str(str(data))


@_representer_for(Readme, License)
def represent_readme_or_license(  # noqa: MAN002
		dumper: RegressionYamlDumper,
		data: Union[Readme, License],
		):
	return dumper.represent_dict(data.to_dict())


@_representer_for(AdditionalFilesEntry)
def represent_additional_files_entry(  # noqa: MAN002
		dumper: RegressionYamlDumper,
		data: AdditionalFilesEntry,
		):
	return dumper.represent_dict(data.to_dict())


@pytest.fixture(
		params=[
				pytest.param(MINIMAL_CONFIG, id="minimal"),
				pytest.param(f'{MINIMAL_CONFIG}\ndescription = "Lovely Spam! Wonderful Spam!"', id="description"),
				pytest.param(f'{MINIMAL_CONFIG}\nrequires-python = ">=3.8"', id="requires-python"),
				pytest.param(
						f'{MINIMAL_CONFIG}\nrequires-python = ">=2.7,!=3.0.*,!=3.2.*"',
						id="requires-python_complex",
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
def good_config(request) -> str:
	return request.param
