import abc
import logging
import typing as t

from testbrain.repository.client import RepositoryClient
from testbrain.repository.exceptions import ProjectNotFound
from testbrain.repository.models import Commit, Payload
from testbrain.repository.types import T_SHA, PathLike, T_Branch, T_File
from testbrain.repository.vcs.git import GitVCS

logger = logging.getLogger(__name__)


class PushService(object):
    _client: t.Optional[RepositoryClient] = None
    _vcs: t.Optional[GitVCS] = None
    _payload: t.Optional[Payload] = None
    _repo_name: str = None

    def __init__(
        self,
        server: str,
        token: str,
        project: str,
        repo_dir: t.Optional[PathLike] = None,
        repo_name: t.Optional[str] = None,
    ):
        self.server = server
        self.token = token
        self.project = project
        self.repo_dir = repo_dir
        self._repo_name = repo_name

    def _get_project_id(self) -> int:
        response = self.client.get_project_id(name=self.project)
        json_data = response.json()
        project_id = json_data.get("project_id")
        error = json_data.get("error")
        if not project_id:
            logger.debug(f"Response from server: {self.project} > {error}")
            logger.critical(f"Project '{self.project}' not found on server.")
            raise ProjectNotFound(f"Project '{self.project}' not found on server.")

        if isinstance(project_id, str):
            project_id = int(project_id)

        return project_id

    @property
    def repo_name(self) -> str:
        if self._repo_name is None:
            self._repo_name = self.vcs.repo_name
        return self._repo_name

    @property
    def client(self) -> t.Optional[RepositoryClient]:
        if self._client is None:
            self._client = RepositoryClient(server=self.server, token=self.token)
        return self._client

    @property
    def vcs(self) -> t.Optional[GitVCS]:
        if self._vcs is None:
            self._vcs = GitVCS(repo_dir=self.repo_dir, repo_name=self._repo_name)
        return self._vcs

    def get_current_branch(self) -> T_Branch:
        branch = self.vcs.current_branch
        return branch

    def get_repository_commits(
        self,
        branch: T_Branch,
        commit: T_SHA,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
        blame: t.Optional[bool] = False,
        **kwargs: t.Any,
    ) -> t.List[Commit]:
        logger.debug(f"extra kwargs {kwargs}")
        if blame:
            logger.warning(
                "In the current version, the "
                "ability to collect blame information is disabled."
            )

        commits = self.vcs.commits(
            branch=branch,
            commit=commit,
            number=number,
            reverse=reverse,
            numstat=numstat,
            raw=raw,
            patch=patch,
        )

        return commits

    def get_repository_file_tree(
        self, branch: T_Branch, minimize: t.Optional[bool] = False, **kwargs: t.Any
    ) -> t.List[T_File]:
        logger.debug(f"extra kwargs {kwargs}")

        if minimize:
            return []

        file_tree = self.vcs.file_tree(branch=branch)
        return file_tree

    def make_changes_payload(
        self,
        branch: T_Branch,
        commits: t.List[Commit],
        file_tree: t.Optional[t.List[T_File]],
        **kwargs: t.Any,
    ) -> Payload:
        logger.debug(f"extra kwargs {kwargs}")

        ref = branch
        base_ref = ""
        before = commits[0].sha
        after = commits[-1].sha
        head_commit = commits[-1]
        size = len(commits)
        ref_type = "commit"

        payload: Payload = Payload(
            repo_name=self.repo_name,
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

    def send_changes_payload(
        self,
        payload: Payload,
        timeout: t.Optional[int] = None,
        max_retries: t.Optional[int] = None,
        **kwargs: t.Any,
    ):
        logger.debug(f"extra kwargs {kwargs}")

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
