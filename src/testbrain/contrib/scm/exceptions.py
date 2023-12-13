class SCMError(Exception):
    ...


class BranchNotFound(SCMError):
    ...


class CommitNotFound(SCMError):
    ...


class ProcessError(SCMError):
    ...
