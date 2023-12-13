import logging
import pathlib
import re
import typing as t

from testbrain.contrib.terminal import Process, ProcessExecutionError

from ..base import AbstractVCS
from ..exceptions import BranchNotFound, CommitNotFound, ProcessError
from .utils import parse_commits_from_text

logger = logging.getLogger(__name__)


class GitProcess(Process):
    def remote_url(self) -> str:
        command = ["git", "config", "--get", "remote.origin.url"]
        result = self.execute(command=command)
        return result

    def fetch(self, rev: t.Optional[str] = None) -> str:
        params = []
        if not rev:
            params.append("-a")
        else:
            params.append(rev)

        command = ["git", "fetch", *params]
        try:
            result = self.execute(command=command)
        except ProcessExecutionError as exc:
            err_msg = exc.stderr.splitlines()[0]
            logger.critical(f"Failed fetch: {err_msg}")
            raise ProcessError(f"Failed fetch: {err_msg}") from exc

        return result

    def checkout(self, rev: str, detach: t.Optional[bool] = False) -> str:
        params = []
        if detach:
            params.append("--detach")

        command = ["git", "checkout", rev, *params]
        result = self.execute(command=command)
        return result

    def rev_parse(self, rev: str) -> str:
        """
        >>> git = GitProcess()
        >>> git.checkout("releases/2023.10.24")
        >>> "Your branch is up to date with 'origin/releases/2023.10.24'."
        >>> git.rev_parse("releases/2023.10.24")
        '6f4fc965428d1d311c02c2de4996c4265765d131'

        """
        command = ["git", "rev-parse", rev]
        try:
            result = self.execute(command=command)
        except ProcessExecutionError as exc:
            err_msg = exc.stderr.splitlines()[0]
            logger.critical(f"Failed rev-parse: {err_msg}")
            raise ProcessError(f"Failed rev-parse: {err_msg}") from exc
        return result

    def branch(
        self,
        local: t.Optional[bool] = False,
        remote: t.Optional[bool] = False,
        show_current: t.Optional[bool] = False,
    ) -> str:
        extra_params: list = []
        if remote:
            extra_params = ["-r"]
        if local and remote:
            extra_params = ["-a"]
        if show_current:
            extra_params = ["--show-current"]
        command = ["git", "branch", *extra_params]
        result = self.execute(command=command)
        return result

    def validate_commit(self, branch: str, commit: str) -> str:
        command = ["git", "branch", "-a", "--contains", commit]
        try:
            result = self.execute(command)
            if not re.search(f"{branch}$", result):
                raise ProcessError("Failed validate commit")
        except ProcessExecutionError as exc:
            raise ProcessError("Failed validate commit") from exc
        return result

    def log(
        self,
        rev: str,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> str:
        params: list = [
            f"-n {number}",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
        ]

        if reverse:
            params.append("--reverse")

        if raw:
            params.append("--raw")

        if numstat:
            params.append("--numstat")

        if patch:
            params.append("-p")

        tab = "%x09"
        pretty_format = (
            "%n"
            f"COMMIT:{tab}%H%n"
            f"TREE:{tab}%T%n"
            f"DATE:{tab}%aI%n"
            f"AUTHOR:{tab}%an{tab}%ae{tab}%aI%n"
            f"COMMITTER:{tab}%cn{tab}%ce{tab}%cI%n"
            f"MESSAGE:{tab}%s%n"
            f"PARENTS:{tab}%P%n"
        )

        command = [
            "git",
            "log",
            *params,
            f'--pretty=format:"{pretty_format}"',
            str(rev),
        ]
        try:
            result = self.execute(command=command)
        except ProcessExecutionError as exc:
            err_msg = exc.stderr.splitlines()[0]
            logger.critical(f"Failed get rev history: {err_msg}")
            raise ProcessError(f"Failed get rev history: {err_msg}") from exc
        return result

    def ls_files(self, rev: str) -> str:
        logger.debug(f"Get files tree for rev: {repr(rev)}")
        params: list = ["--name-only", "-r", rev]

        command = ["git", "ls-tree", *params]
        try:
            result = self.execute(command=command)
        except ProcessExecutionError as exc:
            err_msg = exc.stderr.splitlines()[0]
            logger.critical(f"Failed get file list: {err_msg}")
            raise ProcessError(f"Failed get file list: {err_msg}") from exc
        return result


class GitVCS(AbstractVCS):
    _process: t.Optional["GitProcess"] = None

    def __init__(
        self,
        repo_dir: t.Optional[t.Union[pathlib.Path, str]] = None,
        repo_name: t.Optional[str] = None,
    ):
        super().__init__(repo_dir, repo_name)
        self._fix_renames()

    @property
    def process(self) -> "GitProcess":
        if self._process is None:
            self._process = GitProcess(self.repo_dir)
        return self._process

    def _fix_renames(self, limit: t.Optional[int] = 999999):
        try:
            self.process.execute(
                ["git", "config", "--global", "merge.renameLimit", str(limit)]
            )
            self.process.execute(
                ["git", "config", "--global", "diff.renameLimit", str(limit)]
            )
            self.process.execute(["git", "config", "--global", "diff.renames", "0"])
        except ProcessExecutionError:
            logger.warning("Cant fix rename limits GLOBAL")

        try:
            self.process.execute(["git", "config", "merge.renameLimit", str(limit)])
            self.process.execute(["git", "config", "diff.renameLimit", str(limit)])
            self.process.execute(["git", "config", "diff.renames", "0"])
        except ProcessExecutionError:
            logger.warning("Cant fix rename limits LOCAL")

    def _get_repo_name(self) -> str:
        result = self.process.remote_url()
        remote_url = result.replace(".git", "")
        if not remote_url:
            remote_url = self.repo_dir.as_posix()
        repo_name = remote_url.split("/")[-1]
        return repo_name

    def get_current_branch(self) -> t.AnyStr:
        logger.debug("Get current active branch from git")
        result = self.process.branch(show_current=True)
        if result == "":
            result = None
        logger.debug(f"Current active branch '{result}'")
        return result

    def get_branch(self, branch_name: str) -> t.Tuple[str, str, bool]:
        def clean_name(value: str) -> str:
            value = value.replace("*", "")
            value = value.lstrip().rstrip()
            return value

        branches = self.process.branch(local=True, remote=True)
        branches = [clean_name(record) for record in branches.splitlines()]
        _branch = None
        _remote = False
        for branch in branches:
            if branch == branch_name:
                _branch = branch
                break
            elif branch == f"remotes/origin/{branch_name}":
                _branch = f"origin/{branch_name}"
                _remote = True
                break
            else:
                continue

        if _branch is None:
            raise BranchNotFound(f"Branch '{branch_name}' not found")

        branch_name = _branch
        branch_sha = self.process.rev_parse(rev=branch_name)
        branch_remote = _remote
        return branch_name, branch_sha, branch_remote

    def validate_commit(self, branch: str, commit: str) -> t.Any:
        try:
            _ = self.process.validate_commit(branch=branch, commit=commit)
            return True
        except ProcessError as exc:
            raise CommitNotFound(
                f"Commit '{commit}' not found in '{branch}' history"
            ) from exc

    def fetch(self, branch: t.Optional[str] = None) -> bool:
        logger.debug("Fetch git history")
        _ = self.process.fetch(rev=branch)
        return True

    def checkout(
        self,
        branch: str,
        commit: str,
        detach: t.Optional[bool] = False,
        remote: t.Optional[bool] = False,
    ) -> bool:
        if commit == "HEAD":
            if remote:
                detach = False
            self.process.checkout(rev=branch, detach=detach)
        else:
            branch_head = self.process.rev_parse(rev=branch)
            if commit != branch_head:
                self.process.checkout(rev=commit, detach=detach)
        return True

    def commits(
        self,
        commit: str = "HEAD",
        number: int = 1,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> t.List[t.Dict]:
        result = self.process.log(
            rev=commit,
            number=number,
            reverse=reverse,
            numstat=numstat,
            raw=raw,
            patch=patch,
        )

        commits = parse_commits_from_text(result)

        for commit in commits:
            parent_commits = commit["parents"].copy()
            commit["parents"] = []
            for parent in parent_commits:
                parent_result = self.process.log(
                    rev=parent["sha"],
                    number=1,
                    numstat=False,
                    raw=False,
                    patch=False,
                )
                parent_commit = parse_commits_from_text(parent_result)
                commit["parents"].extend(parent_commit)

        return commits

    def file_tree(self, branch: t.Optional[str] = None) -> t.Optional[t.List[str]]:
        if branch is None:
            branch = None
        result = self.process.ls_files(rev=branch)
        file_tree = result.splitlines()
        file_tree = [file.lstrip().rstrip() for file in file_tree]
        return file_tree
