import subprocess
from testbrain.repository.git.types import *


class GitException(BaseException):
    def __init__(self, cmd: str, error: str, out: Optional[str] = None):
        self.cmd = cmd
        self.error = error
        self.out = out


class GitCmd(object):
    def __init__(self, repo_dir: Optional[PathLike] = None):
        repo_dir = repo_dir or pathlib.Path(".")
        self.repo_dir = pathlib.Path(repo_dir).resolve()

    def _execute(self, command_line: str) -> str:
        process = subprocess.Popen(
            command_line,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=self.repo_dir,
        )

        out = process.stdout.read()
        out = out.strip().decode("UTF-8", errors="ignore")

        error = process.stderr.read()
        error = error.strip().decode("UTF-8", errors="ignore")

        if error:
            process.kill()
            raise GitException(cmd=command_line, error=error, out=out)

        return out

    def execute_remote_url(self) -> str:
        cmd = f"git config --get remote.origin.url"
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
        start: T_SHA,
        number: int,
        reverse: Optional[bool] = True,
        numstat: Optional[bool] = True,
        raw: Optional[bool] = False,
        blame: Optional[bool] = False,
        minimize: Optional[bool] = False,
    ) -> str:
        extra_params: list = [
            "-p",
            "-M",
            "--abbrev=40",
            "--first-parent",
            "--full-diff",
            "--full-index",
            f"-n {number}",
            f"--remotes {branch}",
        ]

        if reverse:
            extra_params.append("--reverse")

        if numstat:
            extra_params.append("--numstat")

        if raw:
            extra_params.append("--raw")

        pretty_format = (
            "%n"
            "COMMIT:\t%H%n"
            "TREE:\t%T%n"
            "DATE:\t%aI%n"
            "AUTHOR:\t%an\t%ae\t%aI%n"
            "COMMITTER:\t%cn\t%ce\t%cI%n"
            "MESSAGE:\t%s%n"
            "PARENTS:\t%P%n"
        )

        cmd = (
            f"git log {' '.join(extra_params)} "
            f"--pretty=format:'{pretty_format}' "
            f"{start}"
        )
        cmd_result = self._execute(command_line=cmd)
        return cmd_result
