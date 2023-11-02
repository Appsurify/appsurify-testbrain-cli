import abc
import logging
import pathlib
import typing as t

from ..models import Commit
from ..types import T_SHA, PathLike, T_Branch, T_File

if t.TYPE_CHECKING:
    from testbrain.terminal import Process


logger = logging.getLogger(__name__)


class BaseVCS(abc.ABC):
    _repo_dir: PathLike
    _repo_name: t.Optional[str] = None
    _current_branch: t.Optional[T_Branch] = None

    def __init__(
        self,
        repo_dir: t.Optional[PathLike] = None,
        repo_name: t.Optional[str] = None,
    ):
        if repo_dir is None:
            repo_dir = pathlib.Path(".").resolve()

        self._repo_dir = pathlib.Path(repo_dir).resolve()
        self._repo_name = repo_name

    @property
    @abc.abstractmethod
    def process(self) -> "Process":
        ...

    @property
    def repo_dir(self) -> PathLike:
        return self._repo_dir

    @property
    def repo_name(self) -> str:
        if self._repo_name is None:
            self._repo_name = self._get_repo_name()
        return self._repo_name

    @property
    def current_branch(self) -> T_Branch:
        if self._current_branch is None:
            self._current_branch = self._get_current_branch()
        return self._current_branch

    @abc.abstractmethod
    def _get_repo_name(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def _get_current_branch(self) -> T_Branch:
        raise NotImplementedError()

    @abc.abstractmethod
    def branches(self) -> t.List[T_Branch]:
        raise NotImplementedError()

    @abc.abstractmethod
    def commits(
        self,
        branch: T_Branch,
        commit: T_SHA,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> t.List[Commit]:
        raise NotImplementedError()

    @abc.abstractmethod
    def file_tree(self, branch: T_Branch) -> t.Optional[t.List[T_File]]:
        raise NotImplementedError()
