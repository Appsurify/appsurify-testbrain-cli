import datetime
import typing as t
from enum import Enum

from pydantic import BaseModel


class Branch(BaseModel):
    name: str


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
    filename: str
    sha: t.Optional[str] = ""
    additions: int = 0
    insertions: int = 0
    deletions: int = 0
    changes: int = 0
    lines: int = 0
    status: t.Optional[FileStatusEnum] = FileStatusEnum.unknown
    previous_filename: t.Optional[str] = ""
    patch: t.Optional[str] = ""
    blame: t.Optional[str] = ""


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
    sha: str
    tree: t.Optional[str] = ""
    date: t.Optional[datetime.datetime] = None
    author: t.Optional[Person] = None
    committer: t.Optional[Person] = None
    message: t.Optional[str] = ""
    parents: t.Optional[t.List["Commit"]] = []
    stats: t.Optional[CommitStat] = CommitStat()
    files: t.Optional[t.List[CommitFile]] = []


class Payload(BaseModel):
    repo_name: str
    ref: str
    base_ref: str
    size: int
    ref_type: str = "commit"
    before: t.Optional[str] = ""
    after: t.Optional[str] = ""
    head_commit: t.Optional[Commit] = None
    commits: t.Optional[t.List[Commit]] = []
    file_tree: t.Optional[t.List[str]] = []
