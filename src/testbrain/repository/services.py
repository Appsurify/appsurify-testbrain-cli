import abc
import logging
import typing as t

from testbrain.repository.client import RepositoryClient
from testbrain.repository.exceptions import (
    BranchNotFound,
    CommitNotFound,
    ProjectNotFound,
    VCSError,
    VCSServiceError,
)
from testbrain.repository.models import Commit, Payload
from testbrain.repository.types import T_SHA, PathLike, T_Branch, T_File
from testbrain.repository.vcs.git import GitVCS

logger = logging.getLogger(__name__)


class PushService(object):
    _client: t.Optional[RepositoryClient] = None
    _vcs: t.Optional[GitVCS] = None

    _payload: t.Optional[Payload] = None

    def __init__(
        self,
        project: str,
        server: str,
        token: str,
        repo_dir: PathLike,
        repo_name: t.Optional[str] = None,
        pr_mode: t.Optional[bool] = False,
    ):
        self.project = project
        self.pr_mode = pr_mode

        self._client = RepositoryClient(server=server, token=token)

        self._vcs = GitVCS(
            repo_dir=repo_dir,
            repo_name=repo_name,
        )

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
    def client(self) -> t.Optional[RepositoryClient]:
        return self._client

    @property
    def vcs(self) -> t.Optional[GitVCS]:
        return self._vcs

    def validate_branch(self, branch: t.Optional[T_Branch] = None) -> t.Any:
        """
        >>> import logging
        >>> logging.basicConfig(level=logging.INFO)
        >>> logger = logging.getLogger()
        >>> from repository.services import PushService
        >>> service = PushService(
        >>>     server="", token="", project="",
        >>>     repo_dir="/GitHub/appsurify-testbrain-cli",
        >>>     pr_mode=True
        >>> )
        >>> logger.info(">>> releases/2023.10.24 <<<")
        >>> b = service.validate_branch(branch="releases/2023.10.24")
        >>> logger.info(b)
        >>> logger.info(">>> releases/2023.10.25 <<<")
        >>> b = service.validate_branch(branch="releases/2023.10.25")
        >>> logger.info(b)
        >>> logger.info(">>> releases/2023.10.26 <<<")
        >>> b = service.validate_branch(branch="releases/2023.10.26")
        >>> logger.info(b)
        >>> logger.info(">>> None <<<")
        >>> b = service.validate_branch(branch=None)
        >>> logger.info(b)
        """
        if branch == "":
            branch = None

        _current = self.vcs.get_current_branch()
        if not _current:
            logger.warning("Branch cannot be determined. Repository is DETACH")

        if branch is None:
            if _current is None:
                error_msg = "It is not possible to continue without a branch."
                logger.critical(error_msg)
                raise VCSServiceError(error_msg)

            branch = _current
            logger.info(f"Use branch '{branch}'")
            return branch

        else:
            if branch == _current:
                logger.info(f"Use branch '{branch}'")
                return branch
            else:
                if not self.pr_mode:
                    error_msg = (
                        "The specified branch does not match "
                        "the current branch. Fix --branch or use '--pr-mode'"
                    )
                    logger.critical(error_msg)
                    raise VCSServiceError(error_msg)
                try:
                    _branch, _head, _remote = self.vcs.get_branch(branch_name=branch)
                    branch = _branch
                except BranchNotFound:
                    logger.warning(f"Branch '{branch}' not found into repository.")

                logger.warning("PR Mode enabled.")
                logger.info(f"Use branch '{branch}'")
                return branch

    def get_commits(
        self,
        commit: T_SHA,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
        blame: t.Optional[bool] = False,
        **kwargs: t.Any,
    ) -> t.List[Commit]:
        if blame:
            logger.warning(
                "In the current version, the "
                "ability to collect blame information is disabled."
            )

        commits = self.vcs.commits(
            commit=commit,
            number=number,
            reverse=reverse,
            numstat=numstat,
            raw=raw,
            patch=patch,
        )

        return commits

    def get_file_tree(
        self, branch: T_Branch, minimize: t.Optional[bool] = False, **kwargs: t.Any
    ) -> t.List[T_File]:
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
        ref = branch
        base_ref = ""
        before = commits[0].sha
        after = commits[-1].sha
        head_commit = commits[-1]
        size = len(commits)
        ref_type = "commit"

        payload: Payload = Payload(
            repo_name=self.vcs.repo_name,
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


class CheckoutService(object):
    _vcs: t.Optional[GitVCS] = None

    def __init__(
        self,
        repo_dir: t.Optional[PathLike] = None,
        pr_mode: t.Optional[bool] = False,
        sync: t.Optional[bool] = False,
    ):
        self.repo_dir = repo_dir
        self.pr_mode = pr_mode
        self.sync = sync

    @property
    def vcs(self) -> t.Optional[GitVCS]:
        if self._vcs is None:
            self._vcs = GitVCS(repo_dir=self.repo_dir)
        return self._vcs

    def fetch(self, branch: t.Optional[T_Branch] = None) -> bool:
        return self.vcs.fetch(branch=branch)

    def checkout(
        self,
        branch: t.Optional[T_Branch] = None,
        commit: t.Optional[T_SHA] = "HEAD",
    ) -> bool:
        """
        svc = CheckoutService(repo_dir="/GitHub/appsurify-testbrain-cli")
        svc.checkout(branch="releases/2023.10.24")
        svc.checkout(branch="releases/2023.10.24", commit="HEAD")
        svc.checkout(branch="releases/2023.10.24", commit="2d517fd")
        raise

        svc = CheckoutService(repo_dir="/GitHub/appsurify-testbrain-cli", pr_mode=True)
        svc.checkout(branch="releases/2023.10.24")
        svc.checkout(branch="releases/2023.10.24", commit="HEAD")
        svc.checkout(branch="releases/2023.10.24", commit="2d517fd")

        """
        if self.sync:
            self.fetch(branch=branch)

        logger.debug(f"Checkout branch '{branch}' with '{commit}'")

        if branch is None:
            branch = self.vcs.get_current_branch()

        if branch is None and self.pr_mode:
            logger.debug("Branch cannot be determined. Repository is in DETACH state.")
            logger.info("Repository already detached and PR mode is enabled.")
            return True

        try:
            _branch, _head, _remote = self.vcs.get_branch(branch_name=branch)
            logger.debug(f"Found branch '{_branch}' with HEAD '{_head}'")
        except VCSError as exc:
            error_msg = "Cant detect branch and commit. Maybe use '--pr-mode'"
            logger.critical(error_msg)
            raise VCSServiceError(error_msg) from exc

        if commit != "HEAD" and _head.startswith(commit):
            commit = "HEAD"

        if commit != "HEAD":
            try:
                _result = self.vcs.validate_commit(branch=branch, commit=commit)
                logger.debug(
                    f"The branch '{branch}' contained "
                    f"a commit '{commit}' in history. {_result}"
                )
            except CommitNotFound as exc:
                error_msg = (
                    f"The branch '{branch}' does not contain "
                    f"a commit '{commit}' in history."
                )
                logger.critical(error_msg)
                raise VCSServiceError(error_msg) from exc

        if commit != "HEAD" and self.pr_mode is False:
            error_msg = (
                "You specified a non-HEAD commit for the branch. Please use PR mode."
            )
            logger.critical(error_msg)
            raise VCSServiceError(error_msg)

        if self.pr_mode and _remote:
            logger.warning(
                f"This branch '{branch}' is remote. Detach will not be applied."
            )

        self.vcs.checkout(
            branch=branch, commit=commit, detach=self.pr_mode, remote=_remote
        )
        logger.info(f"Branch '{branch}' checkouted with '{commit}'")
        return True
