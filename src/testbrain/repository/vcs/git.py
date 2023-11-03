import abc
import logging
import os
import pathlib
import re
import subprocess
import typing as t

from testbrain.repository.models import Commit
from testbrain.repository.types import T_SHA, PathLike, T_Branch, T_File
from testbrain.repository.utils import parse_commits_from_text
from testbrain.repository.vcs.base import BaseVCS
from testbrain.terminal import Process, ProcessExecutionError

logger = logging.getLogger(__name__)


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

    def _get_current_branch(self) -> T_Branch:
        logger.debug("Get current active branch from repository")
        result = self.process.branch(show_current=True)
        logger.debug(f"Current active branch '{result}'")
        return result

    def branches(self) -> t.List[T_Branch]:
        def clean_branch(name: str) -> str:
            return name.replace("*", "").lstrip().rstrip()

        result = self.process.branch()
        branches = result.splitlines()
        branches = [clean_branch(branch) for branch in branches]
        return branches

    def commits(
        self,
        branch: T_Branch,
        commit: T_SHA,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> t.List[Commit]:
        result = self.process.log(
            branch=branch,
            commit=commit,
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
                    branch=branch,
                    commit=parent.sha,
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
            branch = self.current_branch
        result = self.process.ls_files(branch=branch)
        file_tree = result.splitlines()
        file_tree = [file.lstrip().rstrip() for file in file_tree]
        return file_tree


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

    def branch(self, show_current: bool = False) -> str:
        extra_params: list = []
        if show_current:
            extra_params.append("--show-current")
        command = ["git", "branch", *extra_params]
        result = self.execute(command=command)
        return result

    def log(
        self,
        branch: T_Branch,
        commit: T_SHA,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> str:
        extra_params: list = [
            "--abbrev=40",
            "--first-parent",
            "--full-diff",
            "--full-index",
            f"-n {number}",
            f"--remotes {branch}",
        ]

        if reverse:
            extra_params.append("--reverse")

        if raw:
            extra_params.append("--raw")

        if numstat:
            extra_params.append("--numstat")

        if patch:
            extra_params.append("-p")

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
            *extra_params,
            f"--pretty=format:{pretty_format}",
            str(commit),
        ]

        result = self.execute(command=command)
        return result

    def ls_files(self, branch: t.Optional[T_Branch] = None) -> str:
        extra_params: list = ["--name-only"]
        if branch is not None:
            extra_params.append(f"-r {branch}")

        command = ["git", "ls-tree", *extra_params]
        result = self.execute(command=command)
        return result
