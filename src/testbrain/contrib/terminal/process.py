import abc
import logging
import os
import pathlib
import subprocess
import typing as t

from testbrain.contrib.terminal.exceptions import ProcessExecutionError

logger = logging.getLogger(__name__)


class Process(abc.ABC):
    _work_dir: pathlib.Path

    def __init__(self, work_dir: t.Optional[pathlib.Path] = None):
        if work_dir is None:
            work_dir = pathlib.Path(".").resolve()

        self._work_dir = work_dir
        logger.debug(f"Set up execution working dir - {self._work_dir}")

        logger.debug("Set up environment: inherited from OS")
        self.env = os.environ

    @property
    def work_dir(self) -> pathlib.Path:
        return self._work_dir

    def execute(self, command: t.Union[str, t.List[str]]) -> str:
        ret_value = ""

        if isinstance(command, list):
            command = " ".join(command)

        proc_output: t.Optional["subprocess.CompletedProcess"] = None

        try:
            logger.debug(f"Exec process {command}")
            proc_output = subprocess.run(
                command,
                text=False,
                check=True,
                capture_output=True,
                shell=True,
                cwd=self.work_dir,
                env=self.env,
            )
            logger.debug(f"Exec output: {proc_output.stdout}")
            ret_value = proc_output.stdout.decode("utf-8")
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
            raise ProcessExecutionError(
                returncode=exc.returncode,
                cmd=exc.cmd,
                output=exc.stdout,
                stderr=exc.stderr,
            ) from exc
        except UnicodeDecodeError as exc:
            logger.debug(f"Failed to run {command}: {exc}")
            err_msg = "Codec can't decode byte from output. Decode with ignoring char."
            logger.warning(err_msg)
            if proc_output:
                ret_value = proc_output.stdout.decode("utf-8", errors="ignore")
        return ret_value.strip()
