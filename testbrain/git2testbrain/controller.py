import logging
from typing import Optional, Union

from testbrain.git2testbrain.client import Git2TestbrainAPIClient
from testbrain.git2testbrain.models import Payload
from testbrain.git2testbrain.repository import GitRepository
from testbrain.git2testbrain.types import T_SHA, PathLike, T_Branch

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
        logger.debug("Initializing components - 'client' and 'repository'")

        self.repository = GitRepository(repo_dir=repo_dir, repo_name=repo_name)
        self.client = Git2TestbrainAPIClient(server=server, token=token)

        self.project = project
        # logger.warning("Git2TestbrainController Project_ID not converted...")

    def get_project_id(self) -> int:
        response = self.client.get_project_id(name=self.project)

        if not response:
            raise Exception("can not get project_ID")

        json_data = response.json()
        project_id = json_data.get("project_id")
        if isinstance(project_id, str):
            project_id = int(project_id)
        # return project_id
        # if project_id is None:
        #     logger.error(f"Can't continue without project ID")
        logger.info(f"Convert project name to id '{self.project}' -> '{project_id}'")
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
        file_tree: Optional[bool] = False,
    ) -> Payload:
        if branch is None:
            branch = self.repository.get_current_branch()
            logger.debug(f"branch is None. Use current active branch: {branch}")

        logger.info("Looking at the changes in the repository")
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
        logger.debug(f"Delivery payload: {payload.model_dump_json()}")
        return payload

    def deliver_repository_changes(
        self,
        payload: Payload,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        project_id = self.get_project_id()

        payload_json = payload.model_dump_json()

        result = self.client.deliver_hook_payload(
            project_id=project_id,
            data=payload_json,
            timeout=timeout,
            max_retries=max_retries,
        )
        return result
