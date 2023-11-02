import logging
import os
import re
import subprocess
import abc
import typing as t
import pathlib
from dataclasses import dataclass

from .types import T_SHA, T_Branch, T_File, PathLike
from .models import Commit
from .utils import parse_commits_from_text

logger = logging.getLogger(__name__)


class SourceCodeManager(abc.ABC):
    """Base class for version control systems."""

    _repo_name: t.Optional[str] = None
    _repo_dir: t.Optional[PathLike] = None

    def __init__(
        self, repo_dir: t.Optional[PathLike] = None, repo_name: t.Optional[str] = None
    ):
        repo_dir = repo_dir or pathlib.Path(".")
        self._repo_dir = pathlib.Path(repo_dir).resolve()
        self._repo_name = repo_name

    @property
    def repo_dir(self) -> PathLike:
        return self._repo_dir

    @property
    def repo_name(self):
        if self._repo_name is None:
            self._repo_name = self.get_repo_name()
        return self._repo_name

    @property
    def current_branch(self) -> T_Branch:
        if self._current_branch is None:
            self._current_branch = self.get_current_branch()
        return self._current_branch

    @abc.abstractmethod
    def get_repo_name(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_current_branch(self) -> T_Branch:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_commits(
        self,
        branch: T_Branch,
        commit: T_SHA,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> t.List[Commit]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_file_tree(self, branch: T_Branch) -> t.Optional[t.List[T_File]]:
        raise NotImplementedError()


class Git(SourceCodeManager):
    """Git implementation."""

    def __init__(
        self, repo_dir: t.Optional[PathLike] = None, repo_name: t.Optional[str] = None
    ) -> None:
        super().__init__(repo_dir, repo_name)
        self._fix_renames(limit=999999)

    def _fix_renames(self, limit: t.Optional[int] = 999999):
        try:
            self._execute(
                ["git", "config", "--global", "merge.renameLimit", str(limit)]
            )
            self._execute(["git", "config", "--global", "diff.renameLimit", str(limit)])
            self._execute(["git", "config", "--global", "diff.renames", "0"])
        except ExecutionError:
            logger.warning("Cant fix rename limits GLOBAL")
        try:
            self._execute(["git", "config", "merge.renameLimit", str(limit)])
            self._execute(["git", "config", "diff.renameLimit", str(limit)])
            self._execute(["git", "config", "diff.renames", "0"])
        except ExecutionError:
            logger.warning("Cant fix rename limits LOCAL")

    def remote_url(self) -> str:
        cmd = ["git", "config", "--get", "remote.origin.url"]
        result = self._execute(command=cmd)
        return result

    def get_repo_name(self) -> str:
        remote_url = self.remote_url()
        remote_url = remote_url.replace(".git", "")
        if not remote_url:
            remote_url = str(self.repo_dir)
        repo_name = remote_url.split("/")[-1]
        return repo_name

    def get_current_branch(self) -> T_Branch:
        cmd = ["git", "branch", "--show-current"]
        result = self._execute(command=cmd)
        return result

    def get_commits(
        self,
        branch: T_Branch,
        commit: T_SHA,
        number: int,
        reverse: t.Optional[bool] = True,
        numstat: t.Optional[bool] = True,
        raw: t.Optional[bool] = True,
        patch: t.Optional[bool] = True,
    ) -> t.List[Commit]:
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
        cmd = [
            "git",
            "log",
            *extra_params,
            f"--pretty=format:{pretty_format}",
            str(commit),
        ]
        result = self._execute(command=cmd)
        commits = parse_commits_from_text(result)
        for commit in commits:
            parent_commits = commit.parents.copy()
            commit.parents = []
            for parent in parent_commits:
                parent_log_result = self.cmd.execute_log(
                    branch=branch,
                    commit=parent.sha,
                    number=1,
                    numstat=False,
                    raw=False,
                    patch=False,
                )
                parent_commit = parse_commits_from_text(parent_log_result)
                commit.parents.extend(parent_commit)
        return commits

    def get_file_tree(
        self, branch: t.Optional[T_Branch] = None
    ) -> t.Optional[t.List[T_File]]:
        extra_params: list = ["--name-only"]
        if branch is not None:
            branch = self.current_branch
        extra_params.append(f"-r {branch}")
        cmd = ["git", "ls-tree", *extra_params]
        result = self._execute(command=cmd)
        file_tree = result.splitlines()
        file_tree = [file.lstrip().rstrip() for file in file_tree]
        return file_tree
