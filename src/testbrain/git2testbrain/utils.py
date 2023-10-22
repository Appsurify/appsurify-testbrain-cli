import binascii
from typing import Dict, Iterator, List, Match, Optional, TypeVar, Union, cast

from testbrain.git2testbrain.models import (
    Commit,
    CommitFile,
    FileStatusEnum,
    Person,
    Stats,
)
from testbrain.git2testbrain.patterns import (
    RE_COMMIT_DIFF,
    RE_COMMIT_LIST,
    RE_OCTAL_BYTE,
)
from testbrain.git2testbrain.types import T_SHA, Lit_change_type

T_Diff = TypeVar("T_Diff", bound="Diff")


def parse_stats_from_text(text: str) -> Stats:
    hsh = {
        "total": {
            "additions": 0,
            "insertions": 0,
            "deletions": 0,
            "changes": 0,
            "lines": 0,
            "files": 0,
            "total": 0,
        },
        "files": {},
    }

    for line in text.splitlines():
        (raw_insertions, raw_deletions, filename) = line.split("\t")

        if "{" in filename:
            root_path = filename[: filename.find("{")]
            mid_path = (
                filename[filename.find("{") + 1 : filename.find("}")]
                .split("=>")[-1]
                .strip()
            )
            end_path = filename[filename.find("}") + 1 :]
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

        file_obj: CommitFile = CommitFile(
            **{
                "filename": filename.strip(),
                "sha": "",
                "additions": insertions,
                "insertions": insertions,
                "deletions": deletions,
                "changes": insertions + deletions,
                "lines": insertions + deletions,
                "status": FileStatusEnum.unknown,
                "previous_filename": "",
                "patch": "",
                "blame": "",
            }
        )
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
        commit: Commit = parse_single_commit(commit_match)
        commits.append(commit)
    return commits


def parse_commits_from_text_iter(text: str) -> Iterator[Commit]:
    for commit_match in RE_COMMIT_LIST.finditer(text):
        yield parse_single_commit(commit_match)


def parse_single_commit(commit_match: Union[Match[str], dict]) -> Commit:
    if isinstance(commit_match, Match):
        commit_dict = commit_match.groupdict()
    else:
        commit_dict = commit_match

    commit = Commit(
        sha=commit_dict["sha"],
        tree=commit_dict["tree"],
        date=commit_dict["date"],
        author=parse_person_from_text(commit_dict["author"]),
        committer=parse_person_from_text(commit_dict["committer"]),
        message=commit_dict["message"],
        parents=parse_parent_from_text(commit_dict["parents"]),
    )

    stats: Stats = Stats()
    if commit_dict["numstats"]:
        stats = parse_stats_from_text(commit_dict["numstats"])

    raw_diffs: Optional[DiffIndex] = None
    if commit_dict["raw"]:
        raw_diffs = Diff.from_raw(commit_dict["raw"])

    patch_diffs: Optional[DiffIndex] = None
    if commit_dict["patch"]:
        patch_diffs = Diff.from_patch(commit_dict["patch"])

    diffs = patch_diffs or raw_diffs

    commit_files = merge_files_and_diffs(files=stats.files, diffs=diffs)
    commit.files = commit_files

    return commit


def merge_files_and_diffs(
    files: Dict[str, CommitFile], diffs: Optional["DiffIndex"] = None
):
    diffs_dict = {}
    if diffs is not None:
        diffs_dict = diffs.as_dict()

    commit_files: List[CommitFile] = []

    for filename, commit_file in files.items():
        file_diff: Diff = diffs_dict.get(filename, None)
        if file_diff:
            commit_file.patch = file_diff.diff
            if file_diff.b_blob:
                commit_file.sha = file_diff.b_blob["sha"]

            if file_diff.change_type == "A":
                commit_file.status = FileStatusEnum.added
            elif file_diff.change_type == "D":
                commit_file.status = FileStatusEnum.deleted
                commit_file.sha = file_diff.NULL_HEX_SHA
            elif file_diff.change_type == "C":
                commit_file.status = FileStatusEnum.copied
                commit_file.previous_filename = file_diff.a_path
            elif file_diff.change_type == "R":
                commit_file.status = FileStatusEnum.renamed
                commit_file.previous_filename = file_diff.a_path
            elif file_diff.change_type == "M":
                commit_file.status = FileStatusEnum.modified
            else:
                commit_file.status = FileStatusEnum.unknown

        commit_files.append(commit_file)

    return commit_files


hex_to_bin = binascii.a2b_hex
bin_to_hex = binascii.b2a_hex


def _octal_repl(match_obj: Match) -> bytes:
    value = match_obj.group(1)
    value = int(value, 8)
    value = bytes(bytearray((value,)))
    return value


def decode_path(path: str, has_ab_prefix: bool = True) -> Optional[str]:
    if path == "/dev/null":
        return None

    if path.startswith('"') and path.endswith('"'):
        path = (
            path[1:-1]
            .replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace('\\"', '"')
            .replace("\\\\", "\\")
        )

    path = RE_OCTAL_BYTE.sub(_octal_repl, path)

    if has_ab_prefix:
        assert path.startswith("a/") or path.startswith("b/")
        path = path[2:]

    return path


def mode_str_to_int(mode_str: str) -> int:
    """
    :param mode_str: string like 755 or 644 or 100644
    :return:
        String identifying a mode compatible to the mode methods ids of the
        stat module regarding the rwx permissions for user, group and other,
        special flags and file system flags, i.e. whether it is a symlink
        for example."""
    mode = 0
    for iteration, char in enumerate(reversed(mode_str[-6:])):
        char = cast(Union[str, int], char)
        mode += int(char) << iteration * 3
    # END for each char
    return mode


class DiffIndex(List[T_Diff]):
    # change type invariant identifying possible ways a blob can have changed
    # A = Added
    # D = Deleted
    # R = Renamed
    # M = Modified
    # T = Changed in the type
    change_type = ("A", "C", "D", "R", "M", "T", "U")

    def iter_change_type(self, change_type: Lit_change_type) -> Iterator[T_Diff]:
        """
        :return:
            iterator yielding Diff instances that match the given change_type

        :param change_type:
            Member of DiffIndex.change_type, namely:

            * "A" for added paths
            * "D" for deleted paths
            * "R" for renamed paths
            * "M" for paths with modified data
            * "T" for changed in the type paths
        """
        if change_type not in self.change_type:
            raise ValueError("Invalid change type: %s" % change_type)

        iterator = iter(self)
        for diff_idx in iterator:
            if diff_idx.change_type == change_type:
                yield diff_idx
            elif change_type == "A" and diff_idx.new_file:
                yield diff_idx
            elif change_type == "D" and diff_idx.deleted_file:
                yield diff_idx
            elif change_type == "C" and diff_idx.copied_file:
                yield diff_idx
            elif change_type == "R" and diff_idx.renamed:
                yield diff_idx
            elif (
                change_type == "M"
                and diff_idx.a_blob
                and diff_idx.b_blob
                and diff_idx.a_blob != diff_idx.b_blob
            ):
                yield diff_idx
        # END for each diff

    def as_dict(self) -> Dict[str, T_Diff]:
        diff_dict = {}
        iterator = iter(self)
        for diff in iterator:
            if diff.change_type == "A":
                diff_dict[diff.b_path] = diff
            elif diff.change_type == "D":
                diff_dict[diff.a_path] = diff
            elif diff.change_type == "R":
                diff_dict[diff.b_path] = diff
            elif diff.change_type == "C":
                diff_dict[diff.b_path] = diff
            else:
                diff_dict[diff.a_path] = diff
        return diff_dict


class Diff(object):
    # precompiled regex
    re_header = RE_COMMIT_DIFF

    # can be used for comparisons
    NULL_HEX_SHA = "0" * 40
    NULL_BIN_SHA = "\0" * 20

    __slots__ = (
        "a_blob",
        "b_blob",
        "a_mode",
        "b_mode",
        "a_rawpath",
        "b_rawpath",
        "new_file",
        "deleted_file",
        "copied_file",
        "raw_rename_from",
        "raw_rename_to",
        "diff",
        "change_type",
        "score",
    )

    def __init__(
        self,
        a_rawpath: Union[str, None],
        b_rawpath: Union[str, None],
        a_blob_id: Union[str, None],
        b_blob_id: Union[str, None],
        a_mode: Union[str, None],
        b_mode: Union[str, None],
        new_file: bool,
        deleted_file: bool,
        copied_file: bool,
        raw_rename_from: Optional[str],
        raw_rename_to: Optional[str],
        diff: Union[str, None],
        change_type: Optional[Lit_change_type],
        score: Optional[int],
    ) -> None:
        self.a_rawpath = a_rawpath
        self.b_rawpath = b_rawpath

        self.a_mode = mode_str_to_int(a_mode) if a_mode else None
        self.b_mode = mode_str_to_int(b_mode) if b_mode else None

        self.a_blob: Union[Dict, None]
        if a_blob_id is None or a_blob_id == self.NULL_HEX_SHA:
            self.a_blob = None
        else:
            self.a_blob = dict(
                binsha=hex_to_bin(a_blob_id),
                sha=a_blob_id,
                mode=self.a_mode,
                path=self.a_path,
            )

        self.b_blob: Union[Dict, None]
        if b_blob_id is None or b_blob_id == self.NULL_HEX_SHA:
            self.b_blob = None
        else:
            self.b_blob = dict(
                binsha=hex_to_bin(b_blob_id),
                sha=b_blob_id,
                mode=self.b_mode,
                path=self.b_path,
            )

        self.new_file: bool = new_file
        self.deleted_file: bool = deleted_file
        self.copied_file: bool = copied_file

        # be clear and use None instead of empty strings
        # assert raw_rename_from is None or isinstance(raw_rename_from, bytes)
        # assert raw_rename_to is None or isinstance(raw_rename_to, bytes)
        self.raw_rename_from = raw_rename_from or None
        self.raw_rename_to = raw_rename_to or None

        self.diff = diff
        self.score = score

        change_type: Union[Lit_change_type, None]
        # change_type = FileStatusEnum.unknown
        if self.new_file:
            change_type = "A"  # FileStatusEnum.added
        elif self.deleted_file:
            change_type = "D"  # FileStatusEnum.deleted
        elif self.copied_file:
            change_type = "C"  # FileStatusEnum.copied
        elif self.rename_from != self.rename_to:
            change_type = "R"  # FileStatusEnum.renamed
        elif self.a_blob and self.b_blob and self.a_blob != self.b_blob:
            change_type = "M"  # FileStatusEnum.modified
        self.change_type = change_type

    def __eq__(self, other: object) -> bool:
        for name in self.__slots__:
            if getattr(self, name) != getattr(other, name):
                return False
        # END for each name
        return True

    def __ne__(self, other: object) -> bool:
        return not (self == other)

    def __hash__(self) -> int:
        return hash(tuple(getattr(self, n) for n in self.__slots__))

    def __str__(self) -> str:
        h: str = "%s"
        if self.a_blob:
            h %= self.a_blob["path"]
        elif self.b_blob:
            h %= self.b_blob["path"]

        msg: str = ""
        line_length = 0  # line length
        for b, n in zip((self.a_blob, self.b_blob), ("lhs", "rhs")):
            if b:
                line = "\n%s: %o | %s" % (n, b["mode"], b["hexsha"])
            else:
                line = "\n%s: None" % n
            # END if blob is not None
            line_length = max(len(line), line_length)
            msg += line
        # END for each blob

        # add headline
        h += "\n" + "=" * line_length

        if self.deleted_file:
            msg += "\nfile deleted in rhs"
        if self.new_file:
            msg += "\nfile added in rhs"
        if self.copied_file:
            msg += f"\nfile {self.b_path!r} copied from {self.a_path!r}"
        if self.rename_from:
            msg += f"\nfile renamed from {self.rename_from!r}"
        if self.rename_to:
            msg += f"\nfile renamed to {self.rename_to!r}"
        if self.diff:
            msg += "\n---"
            try:
                msg += self.diff
            except UnicodeDecodeError:
                msg += "OMITTED BINARY DATA"
            # end handle encoding
            msg += "\n---"
        # END diff info

        # Python2 silliness: have to assure we convert our
        # likely to be unicode object to a string with the
        # right encoding. Otherwise, it tries to
        # convert it using ascii, which may fail ungracefully
        res = h + msg
        # end
        return res

    @property
    def a_path(self) -> Optional[str]:
        return self.a_rawpath if self.a_rawpath else None

    @property
    def b_path(self) -> Optional[str]:
        return self.b_rawpath if self.b_rawpath else None

    @property
    def rename_from(self) -> Optional[str]:
        return self.raw_rename_from if self.raw_rename_from else None

    @property
    def rename_to(self) -> Optional[str]:
        return self.raw_rename_to if self.raw_rename_to else None

    @property
    def renamed(self) -> bool:
        """:returns: True if the blob of our diff has been renamed
        :note: This property is deprecated, please use ``renamed_file``.
        """
        return self.renamed_file

    @property
    def renamed_file(self) -> bool:
        """:returns: True if the blob of our diff has been renamed"""
        return self.rename_from != self.rename_to

    @classmethod
    def _pick_best_path(
        cls, path_match: str, rename_match: str, path_fallback_match: str
    ) -> Optional[str]:
        if path_match:
            return decode_path(path_match)

        if rename_match:
            return decode_path(rename_match, has_ab_prefix=False)

        if path_fallback_match:
            return decode_path(path_fallback_match)

        return None

    @classmethod
    def _index_from_patch_format(cls, text: str) -> DiffIndex:
        index: "DiffIndex" = DiffIndex()
        previous_header: Union[Match[str], None] = None
        header: Union[Match[str], None] = None
        # a_path: str
        # b_path: str
        # a_mode: str
        # b_mode: str
        for _header in cls.re_header.finditer(text):
            (
                a_path_fallback,
                b_path_fallback,
                old_mode,
                new_mode,
                rename_from,
                rename_to,
                new_file_mode,
                deleted_file_mode,
                copied_file_name,
                a_blob_id,
                b_blob_id,
                b_mode,
                a_path,
                b_path,
            ) = _header.groups()

            new_file, deleted_file, copied_file = (
                bool(new_file_mode),
                bool(deleted_file_mode),
                bool(copied_file_name),
            )

            a_path = cls._pick_best_path(a_path, rename_from, a_path_fallback)
            b_path = cls._pick_best_path(b_path, rename_to, b_path_fallback)

            # Our only means to find the actual text is to see
            # what has not been matched by our regex,
            # and then retroactively assign it to our index
            if previous_header is not None:
                index[-1].diff = text[previous_header.end() : _header.start()]
            # end assign actual diff

            a_mode = (
                old_mode
                or deleted_file_mode
                or (a_path and (b_mode or new_mode or new_file_mode))
            )
            b_mode = b_mode or new_mode or new_file_mode or (b_path and a_mode)

            index.append(
                Diff(
                    a_path,
                    b_path,
                    a_blob_id,
                    b_blob_id,
                    a_mode,
                    b_mode,
                    new_file,
                    deleted_file,
                    copied_file,
                    rename_from,
                    rename_to,
                    None,
                    None,
                    None,
                )
            )

            previous_header = _header
            header = _header
        # end for each header we parse
        if index and header:
            index[-1].diff = text[header.end() :]
        # end assign last diff

        return index

    @classmethod
    def _index_from_raw_format(cls, text: str) -> DiffIndex:
        """Create a new DiffIndex from the given stream which must be in raw format.
        :return: git.DiffIndex"""
        # handles
        # :100644 100644 687099101... 37c5e30c8... M    .gitignore

        index: "DiffIndex" = DiffIndex()

        # Discard everything before the first colon, and the colon itself.
        # _, _, lines = text.partition(":")
        lines = text.splitlines()

        for line in lines:
            line = line.replace(":", "", 1)
            if not line:
                # The line data is empty, skip
                continue
            # Stage 1
            info, _, path = line.partition("\t")
            # Stage 2
            meta, _, _ = info.partition("\x00")

            path = path.rstrip("\x00")
            a_blob_id: Optional[str]
            b_blob_id: Optional[str]
            old_mode, new_mode, a_blob_id, b_blob_id, _change_type = meta.split(None, 4)
            # Change type can be R100
            # R: status letter
            # 100: score (in case of copy and rename)
            # assert is_change_type(_change_type[0]),
            # f"Unexpected value for change_type received: {_change_type[0]}"
            change_type: Lit_change_type = cast(Lit_change_type, _change_type[0])
            score_str = "".join(_change_type[1:])
            score = int(score_str) if score_str.isdigit() else None
            path = path.strip()
            a_path = path
            b_path = path
            deleted_file = False
            new_file = False
            copied_file = False
            rename_from = None
            rename_to = None

            # NOTE: We cannot conclude from the existence of a blob to change type
            # as diffs with the working do not have blobs yet
            if change_type == "D":
                b_blob_id = None  # Optional[str]
                deleted_file = True
            elif change_type == "A":
                a_blob_id = None
                new_file = True
            elif change_type == "C":
                copied_file = True
                a_path_str, b_path_str = path.split("\t", 1)
                a_path = a_path_str
                b_path = b_path_str
            elif change_type == "R":
                a_path_str, b_path_str = path.split("\t", 1)
                a_path = a_path_str
                b_path = b_path_str
                rename_from, rename_to = a_path, b_path
            elif change_type == "T":
                # Nothing to do
                pass
            # END add/remove handling

            diff = Diff(
                a_path,
                b_path,
                a_blob_id,
                b_blob_id,
                old_mode,
                new_mode,
                new_file,
                deleted_file,
                copied_file,
                rename_from,
                rename_to,
                "",
                change_type,
                score,
            )
            index.append(diff)

        return index

    @classmethod
    def from_patch(cls, text: str) -> DiffIndex:
        return cls._index_from_patch_format(text)

    @classmethod
    def from_raw(cls, text: str) -> DiffIndex:
        return cls._index_from_raw_format(text)
