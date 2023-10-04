import datetime
from pydantic import BaseModel, validator, model_validator, field_validator
from testbrain.repository.git.types import *


class Branch(BaseModel):
    name: T_Branch


class Person(BaseModel):
    name: str
    email: Optional[str] = ""
    date: Optional[datetime.datetime] = None


class FileStatusEnum(str, Enum):
    added = 'added'
    deleted = 'deleted'
    modified = 'modified'
    copied = 'copied'
    renamed = 'renamed'
    removed = 'removed'
    unknown = 'unknown'


class CommitFile(BaseModel):
    filename: Union[T_File, PathLike]
    sha: Optional[T_SHA] = ''
    additions: int = 0
    insertions: int = 0
    deletions: int = 0
    changes: int = 0
    lines: int = 0
    status: Optional[FileStatusEnum] = FileStatusEnum.unknown
    previous_filename: Optional[T_File] = ''
    patch: Optional[T_Patch] = ''
    blame: Optional[T_Blame] = ''


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
    files: Dict[str, CommitFile] = {}


class Commit(BaseModel):
    sha: T_SHA
    tree: Optional[T_SHA] = ""
    date: Optional[datetime.datetime] = None
    author: Optional[Person] = None
    committer: Optional[Person] = None
    message: Optional[str] = ""
    parents: Optional[List['Commit']] = []
    stats: Optional[CommitStat] = CommitStat()
    files: Optional[List[CommitFile]] = []


class Events(BaseModel):
    repo_name: str
    ref: T_Branch
    base_ref: T_Branch
    size: int
    ref_type: str = 'commit'
    before: Optional[Commit] = None
    after: Optional[Commit] = None
    head_commit: Optional[Commit] = None
    commits: Optional[List[Commit]] = []
    file_tree: Optional[List[T_File]] = []
