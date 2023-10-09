from typing import Optional


class GitCommandException(Exception):
    def __init__(self, cmd: str, error: str, out: Optional[str] = None):
        self.cmd = cmd
        self.error = error
        self.out = out

    def __str__(self):
        return f"Exec {self.cmd} - {self.error}"
