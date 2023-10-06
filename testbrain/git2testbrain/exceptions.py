from testbrain.git2testbrain.types import Optional


class GitCommandException(BaseException):
    def __init__(self, cmd: str, error: str, out: Optional[str] = None):
        self.cmd = cmd
        self.error = error
        self.out = out

    def __str__(self):
        return f"Exec {self.cmd} - {self.error}"
