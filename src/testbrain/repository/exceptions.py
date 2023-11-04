class VCSError(Exception):
    ...


class ProjectNotFound(VCSError):
    ...


class VCSProcessError(VCSError):
    ...
