import binascii
import pathlib
import traceback
import warnings
import sys
import subprocess
import json
import re
import os
import threading
import datetime
import shlex
from collections import defaultdict
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, validator
from git import Repo
from enum import Enum, IntEnum

COMMAND_GET_ALL_COMMITS_SHA = "git log --pretty=format:%H {} --"
COMMAND_GET_ALL_COMMITS_SHA_JENKINS = "git log --pretty=format:%%H {} --"

# Divide into smaller commands
COMMAND_COMMIT_COMMIT_INFO = "git show --reverse --first-parent --raw --numstat --abbrev=40 --full-index -p -M --pretty=format:'Commit:\t%H%nDate:\t%ai%nTree:\t%T%nParents:\t%P%n' {}"
COMMAND_COMMIT_COMMIT_INFO_MIN = "git show --reverse --first-parent --abbrev=40 --full-index -s -M --pretty=format:'Commit:\t%H%nDate:\t%ai%nTree:\t%T%nParents:\t%P%n' {}"

COMMAND_COMMIT_PERSON_INFO = "git show --reverse --first-parent --raw --numstat --abbrev=40 --full-index -p -M --pretty=format:'Author:\t%an\t%ae\t%ai%nCommitter:\t%cn\t%ce\t%ci%n' {}"
COMMAND_COMMIT_PERSON_INFO_MIN = "git show --reverse --first-parent --abbrev=40 --full-index -s -M --pretty=format:'Author:\t%an\t%ae\t%ai%nCommitter:\t%cn\t%ce\t%ci%n' {}"

COMMAND_COMMIT_MSG = "git show --reverse --first-parent --raw --numstat --abbrev=40 --full-index -p -M --pretty=format:'Message:\t%s%n' {}"
COMMAND_COMMIT_MSG_MIN = "git show --reverse --first-parent --abbrev=40 --full-index -s -M --pretty=format:'Message:\t%s%n' {}"

# COMMAND_COMMIT = "git show --reverse --first-parent --raw --numstat --abbrev=40 --full-index -p -M --pretty=format:'Commit:\t%H%nDate:\t%ai%nTree:\t%T%nParents:\t%P%nAuthor:\t%an\t%ae\t%ai%nCommitter:\t%cn\t%ce\t%ci%nMessage:\t%s%n' {}"
COMMAND_COMMIT_BRANCH = "git branch --contains {}"
COMMAND_COMMIT_FILE_BLAME = "git blame {}^ -L {},{} -- {}"
COMMAND_COMMIT_FILE_BLAME_FIX = "git log --pretty=%H -1 {}^ -- {}"
COMMAND_COMMIT_FILE_BLAME_FIX_JENKINS = "git log --pretty=%%H -1 {}^ -- {}"
COMMAND_REMOTE_URL = "git config --get remote.origin.url"

# PATTERNS
RE_OCTAL_BYTE = re.compile(r"""\\\\([0-9]{3})""")
# RE_COMMIT_HEADER = re.compile(
#     r"""^Commit:\t(?P<sha>[0-9A-Fa-f]+)\nDate:\t(?P<date>.*)\nTree:\t(?P<tree>[0-9A-Fa-f]+)\nParents:\t(?P<parents>.*)\nAuthor:\t(?P<author>.*)\nCommitter:\t(?P<committer>.*)\nMessage:\t(?P<message>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
#     re.VERBOSE | re.MULTILINE)

# New regex for smaller commands
RE_COMMIT_HEADER_COMMIT_INFO = re.compile(
    r"""^Commit:\s*(?P<sha>[0-9A-Fa-f]+)\n\s*Date:\s*(?P<date>.*)\n\s*Tree:\s*(?P<tree>[0-9A-Fa-f]+)\n\s*Parents:\t(?P<parents>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
    re.VERBOSE | re.MULTILINE)
RE_COMMIT_HEADER_COMMIT_PERSON = re.compile(
    r"""^Author:\s*(?P<author>.*)\n\s*Committer:\s*(?P<committer>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
    re.VERBOSE | re.MULTILINE)
RE_COMMIT_HEADER_MSG = re.compile(
    r"""^Message:\s*(?P<message>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
    re.VERBOSE | re.MULTILINE)

RE_COMMIT_DIFF = re.compile(
    r"""^diff[ ]--git[ ](?P<a_path_fallback>"?a/.+?"?)[ ](?P<b_path_fallback>"?b/.+?"?)\n(?:^old[ ]mode[ ](?P<old_mode>\d+)\n^new[ ]mode[ ](?P<new_mode>\d+)(?:\n|$))?(?:^similarity[ ]index[ ]\d+%\n^rename[ ]from[ ](?P<rename_from>.*)\n^rename[ ]to[ ](?P<rename_to>.*)(?:\n|$))?(?:^new[ ]file[ ]mode[ ](?P<new_file_mode>.+)(?:\n|$))?(?:^deleted[ ]file[ ]mode[ ](?P<deleted_file_mode>.+)(?:\n|$))?(?:^index[ ](?P<a_blob_id>[0-9A-Fa-f]+)\.\.(?P<b_blob_id>[0-9A-Fa-f]+)[ ]?(?P<b_mode>.+)?(?:\n|$))?(?:^---[ ](?P<a_path>[^\t\n\r\f\v]*)[\t\r\f\v]*(?:\n|$))?(?:^\+\+\+[ ](?P<b_path>[^\t\n\r\f\v]*)[\t\r\f\v]*(?:\n|$))?""",
    re.VERBOSE | re.MULTILINE)
RE_COMMIT_HEADER_JENKINS = re.compile(
    r"""^Commit:\s*(?P<sha>[0-9A-Fa-f]+)\n\s*Date:\s*(?P<date>.*)\n\s*Tree:\s*(?P<tree>[0-9A-Fa-f]+)\n\s*Parents:\s*(?P<parents>.*)\n\s*Author:\s*(?P<author>.*)\n\s*Committer:\s*(?P<committer>.*)\n\s*Message:\s*(?P<message>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
    re.VERBOSE | re.MULTILINE)




RE_COMMIT_LIST = re.compile(
    r"""^Commit:\s*(?P<sha>[0-9A-Fa-f]+)\n\s*Tree:\s*(?P<tree>[0-9A-Fa-f]+)\n\s*Date:\s*(?P<date>.*)\n\s*Author:\s*(?P<author>.*)\n\s*Committer:\s*(?P<committer>.*)?\nMessage:\s*(?P<message>.*)\n\s*Parents:\s*(?P<parents>.*)\n\s(?P<file_stats>(?:^:.+\n)+)(?P<file_numstats>(?:.+\n)+)\n?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
    re.VERBOSE | re.MULTILINE)


class GitException(BaseException):
    ...


def execute(commandLine, cwd=pathlib.Path('.').absolute()):
    process = subprocess.Popen(commandLine,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               cwd=cwd)

    out = process.stdout.read().strip().decode('UTF-8', errors='ignore')
    error = process.stderr.read().strip().decode('UTF-8', errors='ignore')

    if error:
        process.kill()
        raise GitException(error)
    return out


class Branch:
    ...


class FileStatusEnum(str, Enum):
    added = 'added'
    deleted = 'deleted'
    modified = 'modified'
    renamed = 'renamed'
    removed = 'removed'
    unknown = 'unknown'


class File(BaseModel):
    filename: str
    sha: str
    status: FileStatusEnum = FileStatusEnum.unknown
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    previous_filename: Optional[str] = ''
    patch: Optional[str] = ''
    blame: Optional[str] = ''


class CommitStats(BaseModel):
    insertions: int = 0
    deletions: int = 0
    lines: int = 0
    files: int = 0


class Commit(BaseModel):
    sha: Optional[str] = ''
    tree: Optional[str] = ''
    date: Optional[datetime.datetime] = None
    author: Optional[str] = ''
    committer: Optional[str] = ''
    message: Optional[str] = ''
    parents: Optional[List[str]] = []
    stats: Optional[CommitStats] = CommitStats()
    files: Optional[List[File]] = []
    
    @validator("stats", pre=True)
    def parse_stats(cls, value):
        hsh: dict[str, Union[dict[str, int], dict[Any, Any]]] = {
            "total": {"insertions": 0, "deletions": 0, "lines": 0, "files": 0},
            "files": {},
        }
        for line in value.splitlines():
            (raw_insertions, raw_deletions, filename) = line.split("\t")
            insertions = raw_insertions != "-" and int(raw_insertions) or 0
            deletions = raw_deletions != "-" and int(raw_deletions) or 0
            hsh["total"]["insertions"] += insertions
            hsh["total"]["deletions"] += deletions
            hsh["total"]["lines"] += insertions + deletions
            hsh["total"]["files"] += 1
            files_dict = {
                "insertions": insertions,
                "deletions": deletions,
                "lines": insertions + deletions,
            }
            hsh["files"][filename.strip()] = files_dict
        return CommitStats(**hsh['total'])
    
    @validator("parents", pre=True)
    def parse_parents(cls, value):
        value = value.split(" ")
        value = list(filter(lambda x: x != '', value))
        return value

    @validator("date", pre=True)
    def parse_date(cls, value):
        return datetime.datetime.strptime(
            value,
            "%Y-%m-%d %H:%M:%S %z"
        )


class GitRepository(object):

    def __init__(self, directory):
        self.directory = directory

    def commits_list(self, start, number, branch=None):

        if not branch:
            branch = execute("git branch --show-current", cwd=self.directory)

        if start == 'latest':
            start = 'HEAD'

        splitter = '#########'

        get_all_commits_cmd = f"git log " \
                              f"--reverse " \
                              f"--first-parent " \
                              f"--raw " \
                              f"--numstat " \
                              f"--no-renames " \
                              f"--abbrev=40 " \
                              f"--full-index -p -M " \
                              f"--pretty=format:'{splitter}%nCommit:\t%H%nTree:\t%T%nDate:\t%ai%nAuthor:\t%an\t%ae\t%ai%nCommitter:\t%cn\t%ce\t%ci%nMessage:\t%s%nParents:\t%P%n' -n {number} --remotes {branch} {start}"
        result = execute(get_all_commits_cmd, self.directory)

        for commit in result.split(f"{splitter}\n"):
            if not commit:
                continue

            commit = commit.lstrip()

            print("*"*10)
            commit_info = RE_COMMIT_LIST.match(commit)
            commit_info_grp = commit_info.groupdict()
            c = Commit(**commit_info_grp, stats=commit_info_grp['file_numstats'])

            print(f"OK")

        return []
