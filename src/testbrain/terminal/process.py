import logging
import os
import re
import subprocess
import abc
import typing as t
import pathlib
from .exceptions import ProcessExecutionError


logger = logging.getLogger(__name__)


class Process(abc.ABC):
    _work_dir: pathlib.Path

    def __init__(self, work_dir: t.Optional[pathlib.Path] = None):
        if work_dir is None:
            work_dir = pathlib.Path(".").resolve()

        self._work_dir = work_dir

    @property
    def work_dir(self) -> pathlib.Path:
        return self._work_dir

    def execute(self, command: t.Union[str, t.List[str]]) -> t.Union[str, bytes]:
        if isinstance(command, list):
            command = " ".join(command)
        try:
            result = subprocess.run(
                command,
                text=True,
                check=True,
                capture_output=True,
                shell=True,
                cwd=self.work_dir,
            )
            return result.stdout.strip()
        except FileNotFoundError as exc:
            err_msg = f"Failed change PWD to {self.work_dir}: Directory not found"
            raise ProcessExecutionError(
                returncode=127, cmd=command, stderr=err_msg
            ) from exc
        except NotADirectoryError as exc:
            err_msg = f"Failed change PWD to {self.work_dir}: This is not a directory"
            raise ProcessExecutionError(
                returncode=127, cmd=command, stderr=err_msg
            ) from exc
        except PermissionError as exc:
            err_msg = f"Failed to run {command}: Permission error"
            raise ProcessExecutionError(
                returncode=127, cmd=command, stderr=err_msg
            ) from exc
        except (subprocess.CalledProcessError,) as exc:
            err_msg = (
                f"Failed to run {exc.cmd}: "
                f"return code {exc.returncode}, "
                f"output: {exc.stdout}, error: {exc.stderr}"
            )
            raise ProcessExecutionError(
                returncode=exc.returncode,
                cmd=exc.cmd,
                output=exc.stdout,
                stderr=exc.stderr,
            ) from exc
