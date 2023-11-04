import abc
import logging
import os
import pathlib
import re
import subprocess
import typing as t

from testbrain.terminal.exceptions import ProcessExecutionError

logger = logging.getLogger(__name__)


class Process(abc.ABC):
    _work_dir: pathlib.Path

    def __init__(self, work_dir: t.Optional[pathlib.Path] = None):
        if work_dir is None:
            work_dir = pathlib.Path(".").resolve()

        self._work_dir = work_dir
        logger.debug(f"Set up execution working dir - {self._work_dir}")

    @property
    def work_dir(self) -> pathlib.Path:
        return self._work_dir

    def execute(self, command: t.Union[str, t.List[str]]) -> t.Union[str, bytes]:
        if isinstance(command, list):
            command = " ".join(command)
        try:
            logger.debug(f"Exec process {command}")
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
            err_msg = (
                f"Failed change working dir to {self.work_dir}: Directory not found"
            )
            logger.debug(err_msg)
            logger.critical(f"Process execution failed: {err_msg}")
            raise ProcessExecutionError(
                returncode=127, cmd=command, stderr=err_msg
            ) from exc
        except NotADirectoryError as exc:
            err_msg = (
                f"Failed change working dir to {self.work_dir}: This is not a directory"
            )
            logger.debug(err_msg)
            logger.critical(f"Process execution failed: {err_msg}")
            raise ProcessExecutionError(
                returncode=127, cmd=command, stderr=err_msg
            ) from exc
        except PermissionError as exc:
            err_msg = f"Failed to run {command}: Permission error"
            logger.debug(err_msg)
            logger.critical(f"Process execution failed: {err_msg}")
            raise ProcessExecutionError(
                returncode=127, cmd=command, stderr=err_msg
            ) from exc
        except (subprocess.CalledProcessError,) as exc:
            err_msg = (
                f"Failed to run {exc.cmd}: "
                f"return code {exc.returncode}, "
                f"output: {exc.stdout}, error: {exc.stderr}"
            )
            logger.debug(err_msg)
            # _stderr = exc.stderr.split("\n")[0]
            # logger.critical(f"Process execution failed: {_stderr}")
            raise ProcessExecutionError(
                returncode=exc.returncode,
                cmd=exc.cmd,
                output=exc.stdout,
                stderr=exc.stderr,
            ) from exc
