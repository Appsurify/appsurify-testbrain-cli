import abc
import logging
import pathlib
import typing as t

from testbrain.contrib.terminal import Process

logger = logging.getLogger(__name__)


class BaseVCSProcess(Process):
    def __init__(self, work_dir: t.Optional[pathlib.Path] = None):
        super().__init__(work_dir)


class AbstractVCS(abc.ABC):
    _repo_dir: pathlib.Path
    _repo_name: t.Optional[str] = None

    def __init__(
        self,
        repo_dir: t.Optional[t.Union[pathlib.Path, str]] = None,
        repo_name: t.Optional[str] = None,
    ):
        if repo_dir is None:
            repo_dir = pathlib.Path(".").resolve()

        self._repo_dir = pathlib.Path(repo_dir).resolve()
        self._repo_name = repo_name

    @property
    def repo_dir(self) -> pathlib.Path:
        return self._repo_dir

    @property
    def repo_name(self) -> str:
        if self._repo_name is None:
            self._repo_name = self._get_repo_name()
        return self._repo_name

    @property
    @abc.abstractmethod
    def process(self) -> "BaseVCSProcess":
        raise NotImplementedError()

    @abc.abstractmethod
    def _get_repo_name(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_current_branch(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_branch(self, branch_name: str) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def validate_commit(self, branch: str, commit: str) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def fetch(self, branch: t.Optional[str] = None) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def checkout(
        self,
        branch: str,
        commit: str,
        detach: t.Optional[bool] = False,
        remote: t.Optional[bool] = False,
    ) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def commits(
        self,
        commit: str = "HEAD",
        number: int = 1,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> t.List[t.Dict]:
        raise NotImplementedError()

    @abc.abstractmethod
    def file_tree(self, branch: t.Optional[str] = None) -> t.Optional[t.List[str]]:
        raise NotImplementedError()
