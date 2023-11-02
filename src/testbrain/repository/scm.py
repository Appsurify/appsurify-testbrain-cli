import logging
import os
import re
import typing as t
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile


logger = logging.getLogger(__name__)


@dataclass
class SCMInfo:
    """Information about the current source code manager and state."""

    tool: t.Optional[t.Type["SourceCodeManager"]] = None
    commit_sha: t.Optional[str] = None
    branch_name: t.Optional[str] = None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        tool_name = self.tool.__name__ if self.tool else "No SCM tool"
        return (
            f"SCMInfo(tool={tool_name}, "
            f"branch_name={self.branch_name}, "
            f"commit_sha={self.commit_sha}"
        )


class SourceCodeManager:
    """Base class for version control systems."""

    _TEST_USABLE_COMMAND: t.ClassVar[t.List[str]] = []
    _SHOW_CURRENT_BRANCH_COMMAND: t.ClassVar[t.List[str]] = []
    _SHOW_REMOTE_URL_COMMAND: t.ClassVar[t.List[str]] = []

    @classmethod
    def is_usable(cls) -> bool:
        """Is the VCS implementation usable."""
        try:
            result = subprocess.run(
                cls._TEST_USABLE_COMMAND, check=True, capture_output=True
            )  # noqa: S603
            return result.returncode == 0
        except (
            FileNotFoundError,
            PermissionError,
            NotADirectoryError,
            subprocess.CalledProcessError,
        ):
            return False

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.__class__.__name__}"


class Git(SourceCodeManager):
    """Git implementation."""

    _TEST_USABLE_COMMAND: t.ClassVar[t.List[str]] = ["git", "rev-parse", "--git-dir"]
    _SHOW_CURRENT_BRANCH_COMMAND: t.ClassVar[t.List[str]] = [
        "git",
        "branch",
        "--show-current",
    ]
    _SHOW_REMOTE_URL_COMMAND: t.ClassVar[t.List[str]] = [
        "git",
        "config",
        "--get",
        "remote.origin.url",
    ]


class Mercurial(SourceCodeManager):
    """Mercurial implementation."""

    _TEST_USABLE_COMMAND: t.ClassVar[t.List[str]] = ["hg", "root"]


def get_scm_info() -> t.Union[SourceCodeManager, SCMInfo]:
    """Return a dict with the latest source code management info."""
    if Git.is_usable():
        return Git()
    # elif Mercurial.is_usable():
    #     return Mercurial.latest_tag_info(tag_pattern)
    else:
        return SCMInfo()
