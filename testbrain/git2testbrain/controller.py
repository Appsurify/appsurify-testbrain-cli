import pathlib

from testbrain.git2testbrain.repository import GitRepository
from testbrain.git2testbrain.client import Git2TestbrainAPIClient
from testbrain.git2testbrain.types import *


class Git2TestbrainController(object):
    client = None
    repository = None

    def __init__(
        self,
        server: str,
        token: str,
        project: str,
        repo_dir: Optional[PathLike] = None,
        repo_name: Optional[str] = None,
    ):
        self.repository = GitRepository(repo_dir=repo_dir, repo_name=repo_name)
        self.client = Git2TestbrainAPIClient(server=server, token=token)
        self.project = project
        # self.project_id = self.get_project_id()

    def get_project_id(self) -> int:
        result = self.client.get_project_id(name=self.project)
        return result

    def get_repository_changes(
        self,
        branch: Union[T_Branch, None],
        commit: T_SHA,
        number: int,
        blame: Optional[bool] = False,
    ):
        ...

    def deliver_repository_changes(self):
        ...
