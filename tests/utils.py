# stdlib
import tarfile
from typing import IO, TYPE_CHECKING, Type, TypeVar, Union

# 3rd party
from coincidence.regressions import AdvancedFileRegressionFixture

_TF = TypeVar("_TF", bound="TarFile")


class TarFile(tarfile.TarFile):

	def extractfile(self, member: Union[str, tarfile.TarInfo]) -> IO[bytes]:
		fd = super().extractfile(member)

		if fd is None:
			raise FileNotFoundError(member)
		else:
			return fd

	def read_text(self, member: Union[str, tarfile.TarInfo]) -> str:
		return self.read_binary(member).decode("UTF-8")

	def read_binary(self, member: Union[str, tarfile.TarInfo]) -> bytes:
		fd = self.extractfile(member)

		return fd.read()

	if TYPE_CHECKING:

		def __enter__(self: _TF) -> _TF:
			return super().__enter__()  # type: ignore

		@classmethod  # noqa: A001  # pylint: disable=redefined-builtin
		def open(
				cls: Type[_TF],
				*args,
				**kwargs,
				) -> _TF:
			return super().open(  # type: ignore
					*args,
					**kwargs,
					)


class TarFileRegressionFixture(AdvancedFileRegressionFixture):

	def check_archive(self, tar_file: TarFile, filename: str, **kwargs):
		self.check(tar_file.read_text(filename), **kwargs)
