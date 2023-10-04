import re
import binascii
from typing import Dict, LiteralString, Any

from testbrain.repository.git.types import *
from testbrain.repository.git.models import *
from testbrain.repository.git.patterns import *
from testbrain.repository.git.diff import *

def parse_stats_from_text(text: str) -> "Stats":
    hsh = {
        "total": {
            "additions": 0,
            "insertions": 0,
            "deletions": 0,
            "changes": 0,
            "lines": 0,
            "files": 0,
            "total": 0
        },
        "files": {}
    }

    for line in text.splitlines():

        (raw_insertions, raw_deletions, filename) = line.split("\t")

        if '{' in filename:
            root_path = filename[:filename.find("{")]
            mid_path = \
                filename[filename.find("{") + 1:filename.find("}")].split(
                    "=>")[-1].strip()
            end_path = filename[filename.find("}") + 1:]
            filename = root_path + mid_path + end_path
            filename = filename.replace("//", "/")

        if " => " in filename:
            filename = filename.split(" => ")[1]

        insertions = raw_insertions != "-" and int(raw_insertions) or 0
        deletions = raw_deletions != "-" and int(raw_deletions) or 0

        hsh["total"]["additions"] += insertions
        hsh["total"]["insertions"] += insertions
        hsh["total"]["deletions"] += deletions
        hsh["total"]["changes"] += insertions + deletions
        hsh["total"]["lines"] += insertions + deletions
        hsh["total"]["total"] += insertions + deletions
        hsh["total"]["files"] += 1

        file_obj: CommitFile = CommitFile(**{
            "filename": filename.strip(),
            "sha": '',
            "additions": insertions,
            "insertions": insertions,
            "deletions": deletions,
            "changes": insertions + deletions,
            "lines": insertions + deletions,
            "status": FileStatusEnum.unknown,
            "previous_filename": '',
            "patch": '',
            "blame": ''
        })
        hsh["files"][filename.strip()] = file_obj
    return Stats(total=hsh["total"], files=hsh["files"])


def parse_person_from_text(text: str) -> Person:
    name, email, date = text.split("\t")
    return Person(name=name, email=email, date=date)


def parse_parent_from_text(text: Union[T_SHA, List[T_SHA]]) -> List[Commit]:
    if isinstance(text, str):
        return [Commit(sha=sha) for sha in text.split(" ")]
    return [Commit(sha=sha) for sha in text]


def parse_commits_from_text(text: str) -> List[Commit]:
    commits: List[Commit] = []
    for commit_match in RE_COMMIT_LIST.finditer(text):
        # commits_dict[commit_match['sha']] = parse_single_commit(commit_match)
        commits.append(parse_single_commit(commit_match))
    return commits


def parse_single_commit(commit_match: Union[Match[str], dict]) -> Commit:
    # stats = parse_stats_from_text(commit_dict['stats'])
    # patch = parse_diffs_from_patch(commit_dict['patch'] or '')
    if isinstance(commit_match, Match):
        commit_dict = commit_match.groupdict()
    else:
        commit_dict = commit_match

    commit = Commit(
        sha=commit_dict['sha'],
        tree=commit_dict['tree'],
        date=commit_dict['date'],
        author=parse_person_from_text(commit_dict['author']),
        committer=parse_person_from_text(commit_dict['committer']),
        message=commit_dict['message'],
        parents=parse_parent_from_text(commit_dict['parents']),
    )

    stats: Stats = Stats()
    if commit_dict['stats']:
        stats = parse_stats_from_text(commit_dict['stats'])

    diffs: 'DiffIndex' = DiffIndex()
    if commit_dict['patch']:
        diffs = Diff.from_patch(commit_dict['patch'])

    commit_files = merge_files_and_diffs(files=stats.files, diffs=diffs)
    commit.files = commit_files

    return commit


def merge_files_and_diffs(files: Dict[str, CommitFile], diffs: 'DiffIndex'):
    diffs_dict = diffs.as_dict()

    commit_files: List[CommitFile] = []

    for filename, commit_file in files.items():
        file_diff: Diff = diffs_dict.get(filename, None)
        if file_diff:
            commit_file.patch = file_diff.diff
            if file_diff.b_blob:
                commit_file.sha = file_diff.b_blob['sha']

            if file_diff.change_type == 'A':
                commit_file.status = FileStatusEnum.added
            elif file_diff.change_type == 'D':
                commit_file.status = FileStatusEnum.deleted
            elif file_diff.change_type == 'C':
                commit_file.status = FileStatusEnum.copied
                commit_file.previous_filename = file_diff.a_path
            elif file_diff.change_type == 'R':
                commit_file.status = FileStatusEnum.renamed
                commit_file.previous_filename = file_diff.a_path
            elif file_diff.change_type == 'M':
                commit_file.status = FileStatusEnum.modified
            else:
                commit_file.status = FileStatusEnum.unknown

        commit_files.append(commit_file)

    return commit_files
