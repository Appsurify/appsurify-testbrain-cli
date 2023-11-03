import abc
import logging
import typing as t

from testbrain.repository.client import RepositoryClient
from testbrain.repository.models import Payload
from testbrain.repository.types import T_SHA, PathLike, T_Branch
from testbrain.repository.vcs.git import GitVCS

logger = logging.getLogger(__name__)


class PushService(object):
    _client: t.Optional[RepositoryClient] = None
    _vcs: t.Optional[GitVCS] = None
    _payload: t.Optional[Payload] = None

    def __init__(
        self,
        server: str,
        token: str,
        project: str,
        repo_dir: t.Optional[PathLike] = None,
        repo_name: t.Optional[str] = None,
    ):
        logger.debug("Initializing components - 'client' and 'repository'")
        self.server = server
        self.token = token
        self.project = project
        self.repo_dir = repo_dir
        self.repo_name = repo_name

    def _get_project_id(self) -> int:
        response = self.client.get_project_id(name=self.project)
        json_data = response.json()
        project_id = json_data.get("project_id")
        error = json_data.get("error")
        if not project_id:
            logger.warning("Can't continue without project ID.")
            if error is not None:
                logger.error(f"{error}")
            raise Exception("No project ID provided")

        if isinstance(project_id, str):
            project_id = int(project_id)

        # return project_id
        # if project_id is None:
        #     logger.error(f"Can't continue without project ID")
        logger.info(f"Convert project name to id '{self.project}' -> '{project_id}'")
        return project_id

    @property
    def client(self) -> t.Optional[RepositoryClient]:
        if self._client is None:
            self._client = RepositoryClient(server=self.server, token=self.token)
        return self._client

    @property
    def vcs(self) -> t.Optional[GitVCS]:
        if self._vcs is None:
            self._vcs = GitVCS(repo_dir=self.repo_dir, repo_name=self.repo_name)
        return self._vcs

    def fetch_changes_payload(
        self,
        branch: t.Union[T_Branch, None],
        commit: T_SHA,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
        blame: t.Optional[bool] = False,
        file_tree: bool = False,
    ) -> Payload:
        if branch is None:
            branch = self.vcs.current_branch
            logger.debug(f"branch is None. Use current active branch: {branch}")

        if blame:
            logger.warning(
                "In the current version, the "
                "ability to collect blame information is disabled."
            )

        logger.info("Looking at the changes in the repository")

        commits = self.vcs.commits(
            branch=branch,
            commit=commit,
            number=number,
            reverse=reverse,
            numstat=numstat,
            raw=raw,
            patch=patch,
        )

        if file_tree:
            commit_files = self.vcs.file_tree(branch=branch)
        else:
            commit_files = []

        repo_name = self.vcs.repo_name
        ref = branch
        base_ref = ""
        before = commits[0].sha
        after = commits[-1].sha
        head_commit = commits[-1]
        size = len(commits)
        ref_type = "commit"

        payload: Payload = Payload(
            repo_name=repo_name,
            ref=ref,
            base_ref=base_ref,
            before=before,
            after=after,
            head_commit=head_commit,
            size=size,
            ref_type=ref_type,
            file_tree=commit_files,
            commits=commits,
        )
        # logger.debug(f"Changes payload: {payload.model_dump_json()}")
        return payload

    def send_changes_payload(
        self,
        payload: Payload,
        timeout: t.Optional[int] = None,
        max_retries: t.Optional[int] = None,
    ):
        project_id = self._get_project_id()

        payload_json = payload.model_dump_json()
        payload_json = payload_json.encode("utf-8")
        result = self.client.send_changes_payload(
            project_id=project_id,
            data=payload_json,
            timeout=timeout,
            max_retries=max_retries,
        )
        return result

    def push_changes(
        self,
        branch: t.Union[T_Branch, None],
        commit: T_SHA,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
        blame: t.Optional[bool] = False,
        file_tree: t.Optional[bool] = False,
        timeout: t.Optional[int] = None,
        max_retries: t.Optional[int] = None,
    ) -> t.Any:
        payload = self.fetch_changes_payload(
            branch=branch,
            commit=commit,
            number=number,
            reverse=reverse,
            numstat=numstat,
            raw=raw,
            patch=patch,
            blame=blame,
            file_tree=file_tree,
        )

        result = self.send_changes_payload(
            payload=payload, timeout=timeout, max_retries=max_retries
        )
        return result
