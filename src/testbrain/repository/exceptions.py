class VCSError(Exception):
    ...


class BranchNotFound(VCSError):
    ...


class CommitNotFound(VCSError):
    ...


class ProjectNotFound(VCSError):
    ...


class VCSProcessError(VCSError):
    ...


class VCSServiceError(VCSError):
    ...
