# stdlib
import tempfile
from typing import TYPE_CHECKING, Any, Dict

# 3rd party
import handy_archives
import pytest
from coincidence.regressions import AdvancedDataRegressionFixture, check_file_regression
from domdf_python_tools.paths import PathPlus
from pyproject_examples.example_configs import LONG_REQUIREMENTS, MINIMAL_CONFIG
from pytest_regressions.file_regression import FileRegressionFixture

# this package
from tests.example_configs import COMPLETE_A, COMPLETE_B
from whey.foreman import Foreman

if TYPE_CHECKING:
	# 3rd party
	from _pytest.capture import CaptureFixture


def test_build_success(
		good_config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		file_regression: FileRegressionFixture,
		capsys: "CaptureFixture[str]",
		):
	(tmp_pathplus / "pyproject.toml").write_clean(good_config)
	(tmp_pathplus / "spam").mkdir()
	(tmp_pathplus / "spam" / "__init__.py").write_clean("print('hello world)")

	data: Dict[str, Any] = {}

	foreman = Foreman(project_dir=tmp_pathplus)

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel = foreman.build_wheel(
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		assert (tmp_pathplus / wheel).is_file()

		with handy_archives.ZipFile(tmp_pathplus / wheel) as zip_file:
			data["wheel_content"] = sorted(zip_file.namelist())

			assert zip_file.read_text("spam/__init__.py") == "print('hello world)\n"
			check_file_regression(zip_file.read_text("spam-2020.0.0.dist-info/METADATA"), file_regression)

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist = foreman.build_sdist(
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		assert (tmp_pathplus / sdist).is_file()

		with handy_archives.TarFile.open(tmp_pathplus / sdist) as tar:
			data["sdist_content"] = sorted(tar.getnames())
			assert tar.read_text("spam-2020.0.0/spam/__init__.py") == "print('hello world)\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


@pytest.mark.parametrize(
		"config",
		[
				# pytest.param(COMPLETE_PROJECT_A, id="COMPLETE_PROJECT_A"),
				pytest.param(COMPLETE_A, id="COMPLETE_A"),
				pytest.param(COMPLETE_B, id="COMPLETE_B"),
				pytest.param(LONG_REQUIREMENTS, id="LONG_REQUIREMENTS"),
				],
		)
def test_build_complete(
		config: str,
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		file_regression: FileRegressionFixture,
		capsys: "CaptureFixture[str]",
		):
	(tmp_pathplus / "pyproject.toml").write_clean(config)
	(tmp_pathplus / "whey").mkdir()
	(tmp_pathplus / "whey" / "__init__.py").write_clean("print('hello world)")
	(tmp_pathplus / "README.rst").write_clean("Spam Spam Spam Spam")
	(tmp_pathplus / "LICENSE").write_clean("This is the license")
	(tmp_pathplus / "requirements.txt").write_clean("domdf_python_tools")

	data: Dict[str, Any] = {}

	foreman = Foreman(project_dir=tmp_pathplus)

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel = foreman.build_binary(
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		assert (tmp_pathplus / wheel).is_file()

		with handy_archives.ZipFile(tmp_pathplus / wheel) as zip_file:
			data["wheel_content"] = sorted(zip_file.namelist())

			assert zip_file.read_text("whey/__init__.py") == "print('hello world)\n"
			check_file_regression(zip_file.read_text("whey-2021.0.0.dist-info/METADATA"), file_regression)

	with tempfile.TemporaryDirectory() as tmpdir:
		sdist = foreman.build_sdist(
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		assert (tmp_pathplus / sdist).is_file()

		with handy_archives.TarFile.open(tmp_pathplus / sdist) as tar:
			data["sdist_content"] = sorted(tar.getnames())

			assert tar.read_text("whey-2021.0.0/whey/__init__.py") == "print('hello world)\n"
			assert tar.read_text("whey-2021.0.0/README.rst") == "Spam Spam Spam Spam\n"
			assert tar.read_text("whey-2021.0.0/LICENSE") == "This is the license\n"
			assert tar.read_text("whey-2021.0.0/requirements.txt") == "domdf_python_tools\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def test_build_additional_files(
		tmp_pathplus: PathPlus,
		advanced_data_regression: AdvancedDataRegressionFixture,
		file_regression: FileRegressionFixture,
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

	foreman = Foreman(project_dir=tmp_pathplus)

	with tempfile.TemporaryDirectory() as tmpdir:
		wheel = foreman.build_wheel(
				build_dir=tmpdir,
				out_dir=tmp_pathplus,
				verbose=True,
				colour=False,
				)
		assert (tmp_pathplus / wheel).is_file()

		with handy_archives.ZipFile(tmp_pathplus / wheel) as zip_file:
			data["wheel_content"] = sorted(zip_file.namelist())

			assert zip_file.read_text("whey/__init__.py") == "print('hello world)\n"
			check_file_regression(zip_file.read_text("whey-2021.0.0.dist-info/METADATA"), file_regression)

	sdist = foreman.build_sdist(out_dir=tmp_pathplus, verbose=True, colour=False)
	assert (tmp_pathplus / sdist).is_file()

	with handy_archives.TarFile.open(tmp_pathplus / sdist) as tar:
		data["sdist_content"] = sorted(tar.getnames())

		assert tar.read_text("whey-2021.0.0/whey/__init__.py") == "print('hello world)\n"
		assert tar.read_text("whey-2021.0.0/whey/style.css") == "This is the style.css file\n"
		assert tar.read_text("whey-2021.0.0/README.rst") == "Spam Spam Spam Spam\n"
		assert tar.read_text("whey-2021.0.0/LICENSE") == "This is the license\n"
		assert tar.read_text("whey-2021.0.0/requirements.txt") == "domdf_python_tools\n"

	outerr = capsys.readouterr()
	data["stdout"] = outerr.out.replace(tmp_pathplus.as_posix(), "...")
	data["stderr"] = outerr.err

	advanced_data_regression.check(data)


def test_build_missing_dir(tmp_pathplus: PathPlus):
	(tmp_pathplus / "pyproject.toml").write_clean(MINIMAL_CONFIG)

	foreman = Foreman(project_dir=tmp_pathplus)

	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(FileNotFoundError, match="Package directory 'spam' not found."):
			foreman.build_wheel(
					build_dir=tmpdir,
					out_dir=tmp_pathplus,
					verbose=True,
					colour=False,
					)

	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(FileNotFoundError, match="Package directory 'spam' not found."):
			foreman.build_sdist(
					build_dir=tmpdir,
					out_dir=tmp_pathplus,
					verbose=True,
					colour=False,
					)


def test_build_empty_dir(tmp_pathplus: PathPlus):
	(tmp_pathplus / "pyproject.toml").write_clean(MINIMAL_CONFIG)
	(tmp_pathplus / "spam").mkdir()

	foreman = Foreman(project_dir=tmp_pathplus)

	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(FileNotFoundError, match="No Python source files found in"):
			foreman.build_wheel(
					build_dir=tmpdir,
					out_dir=tmp_pathplus,
					verbose=True,
					colour=False,
					)

	with tempfile.TemporaryDirectory() as tmpdir:
		with pytest.raises(FileNotFoundError, match="No Python source files found in"):
			foreman.build_sdist(
					build_dir=tmpdir,
					out_dir=tmp_pathplus,
					verbose=True,
					colour=False,
					)


# TODO: test with whey-pth to test the entry point extension mechanism
