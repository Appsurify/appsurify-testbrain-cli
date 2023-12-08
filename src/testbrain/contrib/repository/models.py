import datetime
import typing as t
from enum import Enum

from pydantic import BaseModel

from testbrain.contrib.repository.types import (
    T_SHA,
    PathLike,
    T_Blame,
    T_Branch,
    T_File,
    T_Patch,
)


class Branch(BaseModel):
    name: T_Branch


class Person(BaseModel):
    name: str
    email: t.Optional[str] = ""
    date: t.Optional[datetime.datetime] = None


class FileStatusEnum(str, Enum):
    added = "added"
    deleted = "deleted"
    modified = "modified"
    copied = "copied"
    renamed = "renamed"
    removed = "removed"
    unknown = "unknown"


class CommitFile(BaseModel):
    filename: t.Union[T_File, PathLike]
    sha: t.Optional[T_SHA] = ""
    additions: int = 0
    insertions: int = 0
    deletions: int = 0
    changes: int = 0
    lines: int = 0
    status: t.Optional[FileStatusEnum] = FileStatusEnum.unknown
    previous_filename: t.Optional[T_File] = ""
    patch: t.Optional[T_Patch] = ""
    blame: t.Optional[T_Blame] = ""


class CommitStat(BaseModel):
    additions: int = 0
    insertions: int = 0
    deletions: int = 0
    changes: int = 0
    lines: int = 0
    files: int = 0
    total: int = 0


class Stats(BaseModel):
    total: CommitStat = CommitStat()
    files: t.Dict[str, CommitFile] = {}


class Commit(BaseModel):
    sha: T_SHA
    tree: t.Optional[T_SHA] = ""
    date: t.Optional[datetime.datetime] = None
    author: t.Optional[Person] = None
    committer: t.Optional[Person] = None
    message: t.Optional[str] = ""
    parents: t.Optional[t.List["Commit"]] = []
    stats: t.Optional[CommitStat] = CommitStat()
    files: t.Optional[t.List[CommitFile]] = []


class Payload(BaseModel):
    repo_name: str
    ref: T_Branch
    base_ref: T_Branch
    size: int
    ref_type: str = "commit"
    before: t.Optional[T_SHA] = ""
    after: t.Optional[T_SHA] = ""
    head_commit: t.Optional[Commit] = None
    commits: t.Optional[t.List[Commit]] = []
    file_tree: t.Optional[t.List[T_File]] = []
