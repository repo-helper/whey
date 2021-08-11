# stdlib
from typing import Dict, Type

# 3rd party
import click
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, AdvancedFileRegressionFixture
from domdf_python_tools.paths import PathPlus
from pyproject_examples import MINIMAL_CONFIG
from whey_conda import CondaBuilder
from whey_pth import PthWheelBuilder

# this package
from whey.builder import AbstractBuilder, SDistBuilder, WheelBuilder
from whey.foreman import Foreman
from whey.utils import parse_custom_builders, print_builder_names


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
		"builders",
		[
				pytest.param({"sdist": True}, id="sdist_true"),
				pytest.param({"wheel": True}, id="wheel_true"),
				pytest.param({"binary": True}, id="binary_true"),
				pytest.param({"sdist": True, "wheel": True}, id="sdist_and_wheel"),
				pytest.param({"binary": False, "wheel": True}, id="true_and_false"),
				]
		)
@pytest.mark.parametrize(
		"custom_builders",
		[
				pytest.param({}, id="none"),
				pytest.param({"whey_conda": CondaBuilder}, id="whey_conda"),
				pytest.param({"whey_pth": PthWheelBuilder}, id="whey_pth"),
				]
		)
def test_print_builder_names(
		tmp_pathplus: PathPlus,
		config,
		builders: Dict[str, bool],
		custom_builders: Dict[str, Type[AbstractBuilder]],
		advanced_file_regression: AdvancedFileRegressionFixture,
		capsys,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)

	foreman = Foreman(project_dir=tmp_pathplus)
	print_builder_names(foreman, custom_builders, **builders)
	advanced_file_regression.check(capsys.readouterr().out)


def test_parse_custom_builders(advanced_data_regression: AdvancedDataRegressionFixture, ):

	assert parse_custom_builders(None) == {}
	assert parse_custom_builders([]) == {}
	assert parse_custom_builders(()) == {}
	assert parse_custom_builders(iter([])) == {}
	assert parse_custom_builders(x for x in ()) == {}  # type: ignore

	assert parse_custom_builders(["whey_sdist"]) == {"whey_sdist": SDistBuilder}
	assert parse_custom_builders(["whey_wheel"]) == {"whey_wheel": WheelBuilder}
	assert parse_custom_builders(["whey_conda"]) == {"whey_conda": CondaBuilder}
	assert parse_custom_builders(["whey_pth_wheel"]) == {"whey_pth_wheel": PthWheelBuilder}

	expected = {"whey_conda": CondaBuilder, "whey_pth_wheel": PthWheelBuilder}
	assert parse_custom_builders(["whey_conda", "whey_pth_wheel"]) == expected

	with pytest.raises(
			click.BadArgumentUsage,
			match=f"Unknown builder 'foo'. \nIs it registered as an entry point under 'whey.builder'?"
			):
		parse_custom_builders(["foo"])
