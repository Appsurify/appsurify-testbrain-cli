import logging
import pathlib
import subprocess
from typing import List, Optional

from testbrain.git2testbrain.exceptions import GitCommandException
from testbrain.git2testbrain.models import Commit
from testbrain.git2testbrain.types import T_SHA, PathLike, T_Branch
from testbrain.git2testbrain.utils import parse_commits_from_text

logger = logging.getLogger(__name__)


class GitRepository(object):
    def __init__(self, repo_dir: PathLike, repo_name: Optional[str] = None):
        repo_dir = repo_dir or pathlib.Path(".")
        self.repo_dir = pathlib.Path(repo_dir).resolve()
        self.cmd = GitCommand(repo_dir=self.repo_dir)
        self.repo_name = repo_name or self.get_repo_name()
        logger.debug(
            f"Initialized repository for GIT: {self.repo_name}({self.repo_dir})"
        )

    def get_repo_name(self) -> str:
        remote_url = self.cmd.execute_remote_url()
        remote_url = remote_url.replace(".git", "")
        if not remote_url:
            remote_url = str(self.repo_dir)
        repo_name = remote_url.split("/")[-1]
        return repo_name

    def get_current_branch(self) -> T_Branch:
        logger.debug("Get current active branch from repository")
        branch_str = self.cmd.execute_branches(show_current=True)
        logger.debug(f"Current active branch '{branch_str}'")
        return branch_str

    def get_commits(
        self,
        branch: T_Branch,
        commit: T_SHA,
        number: int,
        reverse: Optional[bool] = True,
        numstat: Optional[bool] = True,
        raw: Optional[bool] = True,
        patch: Optional[bool] = True,
        blame: Optional[bool] = False,
    ) -> List[Commit]:
        logger.debug("Begin searching and processing commits")
        log_result = self.cmd.execute_log(
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

        logger.info(f"Finished searching and processing {len(commits)} commits")
        return commits


class GitCommand(object):
    def __init__(self, repo_dir: Optional[PathLike] = None):
        repo_dir = repo_dir or pathlib.Path(".")
        self.repo_dir = pathlib.Path(repo_dir).resolve()

    def _execute(self, command_line: str) -> str:
        logger.debug(f"Executing GIT command: {command_line}")
        process = subprocess.Popen(
            command_line,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=self.repo_dir,
        )

        out = process.stdout.read()
        out = out.strip().decode("UTF-8", errors="ignore")
        # logger.debug(f"Executing result (out) GIT command:\n{out}")

        error = process.stderr.read()
        error = error.strip().decode("UTF-8", errors="ignore")
        # logger.debug(f"Executing result (error) GIT command:\n{error}")

        if error:
            logger.error(f"Error executing: {command_line}")
            process.kill()
            exc = GitCommandException(cmd=command_line, error=error, out=out)
            raise exc

        return out

    def execute_remote_url(self) -> str:
        cmd = "git config --get remote.origin.url"
        cmd_result = self._execute(command_line=cmd)
        return cmd_result

    def execute_branches(self, show_current: bool = False) -> str:
        extra_params: list = []
        if show_current:
            extra_params.append("--show-current")
        cmd = f"git branch {' '.join(extra_params)}"
        cmd_result = self._execute(command_line=cmd)
        return cmd_result

    def execute_log(
        self,
        branch: T_Branch,
        commit: T_SHA,
        number: int,
        reverse: Optional[bool] = True,
        numstat: Optional[bool] = True,
        raw: Optional[bool] = True,
        patch: Optional[bool] = True,
    ) -> str:
        logger.debug(
            f"Executing 'git log' with params: "
            f"branch='{branch}' "
            f"commit='{commit}' "
            f"number='{number}' "
            f"reverse='{reverse}' "
            f"numstat='{numstat}' "
            f"raw='{raw}' "
            f"patch='{patch}' "
        )
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

        cmd = (
            f'git log {" ".join(extra_params)} '
            f'--pretty=format:"{pretty_format}" '
            f"{commit}"
        )
        cmd_result = self._execute(command_line=cmd)
        logger.debug(
            f"Executing 'git log' result data size "
            f"- {len(cmd_result.encode('utf-8', errors='ignore'))} bytes"
        )
        return cmd_result
