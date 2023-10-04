import pathlib
from typing import Optional
from testbrain.repository.git.types import *
from testbrain.repository.git.cmd import GitCmd
from testbrain.repository.git.utils import *


class Git(object):
    def __init__(
        self, repo_dir: Optional[PathLike] = None,
        repo_name: Optional[str] = None
    ):
        repo_dir = repo_dir or pathlib.Path(".")
        self.repo_dir = pathlib.Path(repo_dir).resolve()
        self.cmd = GitCmd(repo_dir=self.repo_dir)
        self.repo_name = repo_name or self._recognize_repo_name()

    def _recognize_repo_name(self) -> str:
        remote_url = self.cmd.execute_remote_url()
        remote_url = remote_url.replace(".git", "")
        if not remote_url:
            remote_url = str(self.repo_dir)
        repo_name = remote_url.split("/")[-1]
        return repo_name

    def _get_current_branch(self) -> T_Branch:
        branch_str = self.cmd.execute_branches(show_current=True)
        return branch_str

    def _get_commits(
        self, branch: T_Branch, start: T_SHA,
        number: int, blame: Optional[bool] = False
    ) -> List[Commit]:
        log_result = self.cmd.execute_log(
            branch=branch, start=start, number=number, blame=blame
        )
        commits = parse_commits_from_text(log_result)
        return commits

    def send_hook(
        self,
        branch: Union[T_Branch, None],
        start: T_SHA,
        number: int,
        blame: Optional[bool] = False,
    ) -> Any:
        if start == "latest":
            start = "HEAD"

        if branch is None:
            branch = self._get_current_branch()

        result = self._get_commits(
            branch=branch, start=start, number=number, blame=blame
        )
        return 0
