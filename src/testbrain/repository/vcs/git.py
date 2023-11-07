import abc
import logging
import os
import pathlib
import re
import subprocess
import typing as t

from testbrain.repository.exceptions import (
    VCSProcessError,
    BranchNotFound,
    CommitNotFound,
)
from testbrain.repository.models import Commit
from testbrain.repository.types import T_SHA, PathLike, T_Branch, T_File
from testbrain.repository.utils import parse_commits_from_text
from testbrain.repository.vcs.base import BaseVCS
from testbrain.terminal.exceptions import ProcessExecutionError
from testbrain.terminal.process import Process

logger = logging.getLogger(__name__)


class GitProcess(Process):
    def __init__(self, work_dir: t.Optional[pathlib.Path] = None):
        super().__init__(work_dir)
        self._fix_renames(limit=999999)

    def _fix_renames(self, limit: t.Optional[int] = 999999):
        try:
            self.execute(["git", "config", "--global", "merge.renameLimit", str(limit)])
            self.execute(["git", "config", "--global", "diff.renameLimit", str(limit)])
            self.execute(["git", "config", "--global", "diff.renames", "0"])
        except ProcessExecutionError:
            logger.warning("Cant fix rename limits GLOBAL")
        try:
            self.execute(["git", "config", "merge.renameLimit", str(limit)])
            self.execute(["git", "config", "diff.renameLimit", str(limit)])
            self.execute(["git", "config", "diff.renames", "0"])
        except ProcessExecutionError:
            logger.warning("Cant fix rename limits LOCAL")

    def remote_url(self) -> str:
        command = ["git", "config", "--get", "remote.origin.url"]
        result = self.execute(command=command)
        return result

    def fetch(self, rev: t.Optional[t.Union[T_Branch, T_SHA]] = None):
        params = []
        if not rev:
            params.append("-a")
        else:
            params.append(rev)

        command = ["git", "fetch", *params]
        result = self.execute(command=command)
        return result

    def checkout(
        self, rev: t.Union[T_SHA, T_Branch], detach: t.Optional[bool] = False
    ) -> str:
        params = []
        if detach:
            params.append("--detach")

        command = ["git", "checkout", rev, *params]
        result = self.execute(command=command)
        return result

    def rev_parse(self, rev: t.Union[T_Branch, T_SHA]) -> str:
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
            raise VCSProcessError(f"Failed rev-parse: {err_msg}") from exc
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

    def validate_commit(self, branch: T_Branch, commit: T_SHA) -> str:
        command = [
            "git",
            "branch",
            "-a",
            "--contains",
            commit,
            "|",
            "grep",
            "-E",
            f"'(^|\s){branch}$'",
        ]
        try:
            result = self.execute(command)
        except ProcessExecutionError as exc:
            raise VCSProcessError(f"Failed validate commit") from exc
        return result

    def log(
        self,
        rev: t.Union[T_Branch, T_SHA],
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> str:
        params: list = [
            f"-n {number}",
            "--abbrev=40",
            # "--first-parent",
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
            raise VCSProcessError(f"Failed get rev history: {err_msg}") from exc

        return result

    def ls_files(self, rev: t.Union[T_Branch, T_SHA]) -> str:
        logger.debug(f"Get files tree for rev: {repr(rev)}")
        params: list = ["--name-only", "-r", rev]

        command = ["git", "ls-tree", *params]
        result = self.execute(command=command)
        return result


class GitVCS(BaseVCS):
    _process: t.Optional["GitProcess"] = None

    @property
    def process(self) -> "GitProcess":
        if self._process is None:
            self._process = GitProcess(self.repo_dir)
        return self._process

    def _get_repo_name(self) -> str:
        result = self.process.remote_url()
        remote_url = result.replace(".git", "")
        if not remote_url:
            remote_url = str(self.repo_dir)
        repo_name = remote_url.split("/")[-1]
        return repo_name

    def get_current_branch(self) -> T_Branch:
        logger.debug("Get current active branch from repository")
        result = self.process.branch(show_current=True)
        if result == "":
            result = None
        logger.debug(f"Current active branch '{result}'")
        return result

    def get_branch(self, branch_name: T_Branch) -> t.Any:
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

    def validate_commit(self, branch: T_Branch, commit: T_SHA) -> t.Any:
        try:
            _ = self.process.validate_commit(branch=branch, commit=commit)
            return True
        except VCSProcessError as exc:
            raise CommitNotFound(
                f"Commit '{commit}' not found in '{branch}' history"
            ) from exc

    def fetch(self, branch: t.Optional[T_Branch] = None) -> bool:
        logger.debug("Fetch repository history")
        _ = self.process.fetch(rev=branch)
        return True

    def checkout(
        self,
        branch: T_Branch,
        commit: T_SHA,
        detach: t.Optional[bool] = False,
        remote: t.Optional[bool] = False,
    ):
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
        commit: T_SHA = "HEAD",
        number: int = 1,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> t.List[Commit]:
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
            parent_commits = commit.parents.copy()
            commit.parents = []
            for parent in parent_commits:
                parent_result = self.process.log(
                    rev=parent.sha,
                    number=1,
                    numstat=False,
                    raw=False,
                    patch=False,
                )
                parent_commit = parse_commits_from_text(parent_result)
                commit.parents.extend(parent_commit)

        return commits

    def file_tree(
        self, branch: t.Optional[T_Branch] = None
    ) -> t.Optional[t.List[T_File]]:
        if branch is None:
            branch = None
        result = self.process.ls_files(rev=branch)
        file_tree = result.splitlines()
        file_tree = [file.lstrip().rstrip() for file in file_tree]
        return file_tree
