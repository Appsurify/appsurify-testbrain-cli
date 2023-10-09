import logging
from typing import Optional, Union, Dict, Any
from testbrain.core import TestbrainContext
from testbrain.git2testbrain.client import Git2TestbrainAPIClient
from testbrain.git2testbrain.repository import GitRepository
from testbrain.git2testbrain.types import T_SHA, PathLike, T_Branch
from testbrain.git2testbrain.models import Payload


logger = logging.getLogger(__name__)


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
        logger.debug("Initializing components: client and repository")

        self.repository = GitRepository(repo_dir=repo_dir, repo_name=repo_name)
        self.client = Git2TestbrainAPIClient(server=server, token=token)

        self.project = project
        # logger.warning("Git2TestbrainController Project_ID not converted...")
        self.project_id = self.get_project_id()

    def get_project_id(self) -> int:
        project_id = self.client.get_project_id(name=self.project)
        if project_id is None:
            logger.error(f"Can't continue without project id")
        return project_id

    def get_payload(
        self,
        branch: Union[T_Branch, None],
        commit: T_SHA,
        number: int,
        reverse: Optional[bool] = True,
        numstat: Optional[bool] = True,
        raw: Optional[bool] = True,
        patch: Optional[bool] = True,
        blame: Optional[bool] = False,
    ) -> Payload:
        if branch is None:
            branch = self.repository.get_current_branch()
            logger.debug(f"branch is None. Use current active branch: {branch}")

        commits = self.repository.get_commits(
            branch=branch,
            commit=commit,
            number=number,
            reverse=reverse,
            numstat=numstat,
            raw=raw,
            patch=patch,
            blame=blame,
        )
        repo_name = self.repository.repo_name
        ref = branch
        base_ref = ""
        before = commits[0].sha
        after = commits[-1].sha
        head_commit = commits[-1]
        size = len(commits)
        ref_type = "commit"
        file_tree = []
        payload: Payload = Payload(
            repo_name=repo_name,
            ref=ref,
            base_ref=base_ref,
            before=before,
            after=after,
            head_commit=head_commit,
            size=size,
            ref_type=ref_type,
            file_tree=file_tree,
            commits=commits,
        )
        return payload

    def deliver_repository_changes(self, payload, timeout, max_retries):
        ...
