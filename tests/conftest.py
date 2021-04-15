# stdlib
from typing import Callable, Type, TypeVar, Union

# 3rd party
from packaging.markers import Marker
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from pyproject_parser.classes import License, Readme
from pytest_regressions.data_regression import RegressionYamlDumper

_C = TypeVar("_C", bound=Callable)

pytest_plugins = ("coincidence", )


def _representer_for(*data_type: Type):

	def deco(representer_fn: _C) -> _C:
		for dtype in data_type:
			RegressionYamlDumper.add_custom_yaml_representer(dtype, representer_fn)

		return representer_fn

	return deco


@_representer_for(Version, Requirement, Marker, SpecifierSet)
def represent_packaging_types(
		dumper: RegressionYamlDumper,
		data: Union[Version, Requirement, Marker, SpecifierSet],
		):
	return dumper.represent_str(str(data))


@_representer_for(Readme, License)
def represent_readme_or_license(
		dumper: RegressionYamlDumper,
		data: Union[Readme, License],
		):
	return dumper.represent_dict(data.to_dict())
