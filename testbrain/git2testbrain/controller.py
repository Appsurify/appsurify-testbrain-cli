from testbrain.git2testbrain.repository import GitRepository
from testbrain.git2testbrain.client import Git2TestbrainAPIClient
from testbrain.git2testbrain.types import *


class Git2TestBrainController(object):
    client = None
    repository = None

    def __init__(
        self, server: str, token: str, project: str, repo_dir: str, repo_name: str
    ):
        self.project = project
        self.server = server
        self.token = token

        self.client = Git2TestbrainAPIClient(server=server, token=token)
        self.repository = GitRepository(repo_dir=repo_dir, repo_name=repo_name)

    def capture_changes(
        self,
        branch: Union[T_Branch, None],
        commit: T_SHA,
        number: int,
        blame: Optional[bool] = False,
    ):
        ...

    def deliver_changes(self):
        ...
