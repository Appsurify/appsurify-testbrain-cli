import logging
import os
import re
import subprocess
import abc
import typing as t
import pathlib

from testbrain.terminal import Process
from ..types import T_SHA, T_Branch, T_File, PathLike
from ..models import Commit
from ..utils import parse_commits_from_text
from .base import BaseVCS


logger = logging.getLogger(__name__)


class GitVCS(BaseVCS):
    _process: t.Optional["GitProcess"] = None

    @property
    def process(self) -> "GitProcess":
        if self._process is None:
            self._process = GitProcess(self.repo_dir)
        return self._process

    def _get_repo_name(self) -> str:
        ...

    def _get_current_branch(self) -> T_Branch:
        ...

    def branches(self) -> t.List[T_Branch]:
        ...

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
        log_result = self.process.log(
            branch=branch,
            commit=commit,
            number=number,
            reverse=reverse,
            numstat=numstat,
            raw=raw,
            patch=patch,
        )
        commits = parse_commits_from_text(log_result)
        for commit in commits:
            parent_commits = commit.parents.copy()
            commit.parents = []
            for parent in parent_commits:
                parent_log_result = self.process.log(
                    branch=branch,
                    commit=parent.sha,
                    number=1,
                    numstat=False,
                    raw=False,
                    patch=False,
                )
                parent_commit = parse_commits_from_text(parent_log_result)
                commit.parents.extend(parent_commit)

        logger.info(f"Finished searching and processing {len(commits)} commits")
        return commits

    def file_tree(self, branch: T_Branch) -> t.Optional[t.List[T_File]]:
        ...


class GitProcess(Process):
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
