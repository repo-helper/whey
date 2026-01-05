# stdlib
from typing import TYPE_CHECKING, Any, Dict

# 3rd party
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture
from coincidence.selectors import min_version, only_version
from domdf_python_tools.paths import PathPlus, TemporaryPathPlus, sort_paths

# this package
from tests.example_configs import COMPLETE_A
from whey.builder import WheelBuilder
from whey.config import load_toml

if TYPE_CHECKING:
	# 3rd party
	from _pytest.capture import CaptureFixture


@pytest.mark.parametrize(
		"editables_version", [
				pytest.param("0.2", marks=only_version("3.6")),
				pytest.param("0.3", marks=min_version("3.7")),
				]
		)
def test_create_editables_files(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		capsys: "CaptureFixture[str]",
		editables_version: str,
		):
	(tmp_pathplus / "pyproject.toml").write_clean(COMPLETE_A)
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world)")
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	data: Dict[str, Any] = {}

	with TemporaryPathPlus() as tmpdir:
		wheel_builder = WheelBuilder(
				project_dir=tmp_pathplus,
				config=load_toml(tmp_pathplus / "pyproject.toml"),
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)

		assert list(wheel_builder.create_editables_files()) == ["editables>=0.2"]

		outerr = capsys.readouterr()
		data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
		data["stderr"] = outerr.err

		data["listdir"] = [p.relative_to(tmpdir).as_posix() for p in sort_paths(*tmpdir.iterdir())]
		data["pth"] = (tmpdir / "whey.pth").read_text()

		data["code"] = (tmpdir / "_editable_impl_whey.py").read_text().replace(tmp_pathplus.as_posix(), "...")

	advanced_data_regression.check(data)
