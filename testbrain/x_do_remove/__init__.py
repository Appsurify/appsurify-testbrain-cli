import binascii
import traceback
import warnings
import sys
import argparse
import subprocess
import json
import re
import logging
import os
import threading
import logging.config
import datetime
import shlex
from collections import defaultdict

try:
    import requests, urllib3
    from requests.adapters import HTTPAdapter
    from requests.sessions import Session
    from requests.adapters import Retry
except ImportError:
    warnings.warn(
        "Module 'requests' not found. Please install it, e.g. 'pip install requests'."
        "Then run the command again."
    )
    sys.exit(1)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Syntax sugar.
_ver = sys.version_info

#: Python 2.x?
is_py2 = _ver[0] == 2

if is_py2:
    raise Exception("Python 2.x is deprecated.")

#: Python 3.x?
is_py3 = _ver[0] == 3

#: OS Windows
is_windows = os.name == "nt"

#: OS MacOS or Linux
is_posix = os.name == "posix"

DEBUG = True


def exception_handler(type, value, tb):
    logging.exception(
        "Uncaught exception: {0} {1} - Line : {2} ".format(
            str(value), str(type), str(tb.tb_lineno)
        )
    )


# Install exception handler
# sys.excepthook = exception_handler


def gittoappsurifyInit():
    if not os.path.exists("./.testbrain"):
        os.makedirs("./.testbrain")
    if not os.path.exists("./.testbrain/debug"):
        os.makedirs("./.testbrain/debug")


gittoappsurifyInit()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)-8s [%(funcName)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "./.testbrain/debug.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 7,
        },
    },
    "loggers": {
        "": {
            "level": "INFO" if not DEBUG else "DEBUG",
            "handlers": ["console", "file"],
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

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

DEBUG = True
COMMIT_COUNT = 10

# PATTERNS
RE_OCTAL_BYTE = re.compile(r"""\\\\([0-9]{3})""")
# RE_COMMIT_HEADER = re.compile(
#     r"""^Commit:\t(?P<sha>[0-9A-Fa-f]+)\nDate:\t(?P<date>.*)\nTree:\t(?P<tree>[0-9A-Fa-f]+)\nParents:\t(?P<parents>.*)\nAuthor:\t(?P<author>.*)\nCommitter:\t(?P<committer>.*)\nMessage:\t(?P<message>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
#     re.VERBOSE | re.MULTILINE)

# New regex for smaller commands
RE_COMMIT_HEADER_COMMIT_INFO = re.compile(
    r"""^Commit:\s*(?P<sha>[0-9A-Fa-f]+)\n\s*Date:\s*(?P<date>.*)\n\s*Tree:\s*(?P<tree>[0-9A-Fa-f]+)\n\s*Parents:\t(?P<parents>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
    re.VERBOSE | re.MULTILINE,
)
RE_COMMIT_HEADER_COMMIT_PERSON = re.compile(
    r"""^Author:\s*(?P<author>.*)\n\s*Committer:\s*(?P<committer>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
    re.VERBOSE | re.MULTILINE,
)
RE_COMMIT_HEADER_MSG = re.compile(
    r"""^Message:\s*(?P<message>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
    re.VERBOSE | re.MULTILINE,
)

RE_COMMIT_DIFF = re.compile(
    r"""^diff[ ]--git[ ](?P<a_path_fallback>"?a/.+?"?)[ ](?P<b_path_fallback>"?b/.+?"?)\n(?:^old[ ]mode[ ](?P<old_mode>\d+)\n^new[ ]mode[ ](?P<new_mode>\d+)(?:\n|$))?(?:^similarity[ ]index[ ]\d+%\n^rename[ ]from[ ](?P<rename_from>.*)\n^rename[ ]to[ ](?P<rename_to>.*)(?:\n|$))?(?:^new[ ]file[ ]mode[ ](?P<new_file_mode>.+)(?:\n|$))?(?:^deleted[ ]file[ ]mode[ ](?P<deleted_file_mode>.+)(?:\n|$))?(?:^index[ ](?P<a_blob_id>[0-9A-Fa-f]+)\.\.(?P<b_blob_id>[0-9A-Fa-f]+)[ ]?(?P<b_mode>.+)?(?:\n|$))?(?:^---[ ](?P<a_path>[^\t\n\r\f\v]*)[\t\r\f\v]*(?:\n|$))?(?:^\+\+\+[ ](?P<b_path>[^\t\n\r\f\v]*)[\t\r\f\v]*(?:\n|$))?""",
    re.VERBOSE | re.MULTILINE,
)
RE_COMMIT_HEADER_JENKINS = re.compile(
    r"""^Commit:\s*(?P<sha>[0-9A-Fa-f]+)\n\s*Date:\s*(?P<date>.*)\n\s*Tree:\s*(?P<tree>[0-9A-Fa-f]+)\n\s*Parents:\s*(?P<parents>.*)\n\s*Author:\s*(?P<author>.*)\n\s*Committer:\s*(?P<committer>.*)\n\s*Message:\s*(?P<message>.*)?(?:\n\n|$)?(?P<file_stats>(?:^:.+\n)+)?(?P<file_numstats>(?:.+\t.*\t.*\n)+)?(?:\n|\n\n|$)?(?P<patch>(?:diff[ ]--git(?:.+\n)+)+)?(?:\n\n|$)?""",
    re.VERBOSE | re.MULTILINE,
)

REPOSITORY_NAME = ""


class BasePlatform(object):
    FORMATS = {
        "ssh": r"%(_user)s@%(host)s:%(repo)s.git",
        "ssh2": r"ssh://(_user)s@%(host)s:%(port)s%(path)s%(repo)s.git",
        "http": r"http://%(host)s/%(repo)s.git",
        "https": r"http://%(host)s/%(repo)s.git",
        "git": r"git://%(host)s/%(repo)s.git",
    }

    PATTERNS = {
        "ssh": r"(?P<_user>.+)s@(?P<domain>.+)s:(?P<repo>.+)s.git",
        "ssh2": r"(ssh:\/\/)?(?P<_user>.+)@(?P<domain>.+):(?P<port>\d{2,5})(?P<path>\/(.+(\/))?)(?P<repo>[^\/\d].+).git",
        "http": r"http://(?P<domain>.+)s/(?P<repo>.+)s.git",
        "https": r"http://(?P<domain>.+)s/(?P<repo>.+)s.git",
        "git": r"git://(?P<domain>.+)s/(?P<repo>.+)s.git",
    }

    # None means it matches all domains
    DOMAINS = None
    DEFAULTS = {}

    def __init__(self):
        # Precompile PATTERNS
        self.COMPILED_PATTERNS = dict(
            (proto, re.compile(regex)) for proto, regex in self.PATTERNS.items()
        )

        # Supported protocols
        self.PROTOCOLS = self.PATTERNS.keys()


class BitbucketPlatform(BasePlatform):
    PATTERNS = {
        "https": r"https://(?P<_user>.+)@(?P<domain>.+)/(?P<owner>.+)/(?P<repo>.+).git",
        "ssh": r"git@(?P<domain>.+):(?P<owner>.+)/(?P<repo>.+).git",
    }
    FORMATS = {
        "https": r"https://%(owner)s@%(domain)s/%(owner)s/%(repo)s.git",
        "ssh": r"git@%(domain)s:%(owner)s/%(repo)s.git",
    }
    DOMAINS = ("bitbucket.org",)
    DEFAULTS = {"_user": "git"}


class GitHubPlatform(BasePlatform):
    PATTERNS = {
        "https": r"https://(?P<domain>.+)/(?P<owner>.+)/(?P<repo>.+)(.git)?",
        "ssh": r"git@(?P<domain>.+):(?P<owner>.+)/(?P<repo>.+).git",
        "git": r"git://(?P<domain>.+)/(?P<owner>.+)/(?P<repo>.+).git",
    }
    FORMATS = {
        "https": r"https://%(domain)s/%(owner)s/%(repo)s.git",
        "ssh": r"git@%(domain)s:%(owner)s/%(repo)s.git",
        "git": r"git://%(domain)s/%(owner)s/%(repo)s.git",
    }
    DOMAINS = (
        "github.com",
        "gist.github.com",
    )
    DEFAULTS = {"_user": "git"}


class GitLabPlatform(BasePlatform):
    PATTERNS = {
        "https": r"https://(?P<domain>.+)/(?P<owner>.+)/(?P<repo>.+)(.git)?",
        "ssh": r"git@(?P<domain>.+):(?P<owner>.+)/(?P<repo>.+).git",
        "git": r"git://(?P<domain>.+)/(?P<owner>.+)/(?P<repo>.+).git",
    }
    FORMATS = {
        "https": r"https://%(domain)s/%(owner)s/%(repo)s.git",
        "ssh": r"git@%(domain)s:%(owner)s/%(repo)s.git",
        "git": r"git://%(domain)s/%(owner)s/%(repo)s.git",
    }
    DEFAULTS = {"_user": "git"}


PLATFORMS = (
    # name -> Platform object
    ("github", GitHubPlatform()),
    ("bitbucket", BitbucketPlatform()),
    ("gitlab", GitLabPlatform()),
    # Match url
    ("base", BasePlatform()),
)

PLATFORMS_MAP = dict(PLATFORMS)

SUPPORTED_ATTRIBUTES = (
    "domain",
    "repo",
    "owner",
    "_user",
    "port",
    "path",
    "url",
    "platform",
    "protocol",
)


def parse_repo_url(url, check_domain=True):
    try:
        # Values are None by default
        parsed_info = defaultdict(lambda: None)
        parsed_info["port"] = ""
        parsed_info["path"] = ""

        # Defaults to all attributes
        map(parsed_info.setdefault, SUPPORTED_ATTRIBUTES)

        for name, platform in PLATFORMS:
            for protocol, regex in platform.COMPILED_PATTERNS.items():
                # Match current regex against URL
                match = regex.match(url)

                # Skip if not matched
                if not match:
                    # print("[%s] URL: %s dit not match %s" % (name, url, regex.pattern))
                    continue

                # Skip if domain is bad
                domain = match.group("domain")
                # print('[%s] DOMAIN = %s' % (url, domain,))
                if check_domain:
                    if platform.DOMAINS and not (domain in platform.DOMAINS):
                        # print("domain: %s not in %s" % (domain, platform.DOMAINS))
                        continue

                # Get matches as dictionary
                matches = match.groupdict()

                # Update info with matches
                parsed_info.update(matches)

                # add in platform defaults
                parsed_info.update(platform.DEFAULTS)

                # Update info with platform info
                parsed_info.update(
                    {
                        "url": url,
                        "platform": name,
                        "protocol": protocol,
                    }
                )
                return parsed_info

        # Empty if none matched
    except Exception as ex:
        print("parse_repo_url", ex)
        sys.exit(1)
    return parsed_info


REQUIRED_ATTRIBUTES = (
    "domain",
    "repo",
)


class GitUrlParsed(object):
    def __init__(self, parsed_info):
        self._parsed = parsed_info

        # Set parsed objects as attributes
        for k, v in parsed_info.items():
            setattr(self, k, v)

    def _valid_attrs(self):
        return all([getattr(self, attr, None) for attr in REQUIRED_ATTRIBUTES])

    @property
    def valid(self):
        return all(
            [
                self._valid_attrs(),
            ]
        )

    @property
    def _platform_obj(self):
        return PLATFORMS_MAP[self.platform]

    ##
    # Alias properties
    ##
    @property
    def host(self):
        return self.domain

    @property
    def user(self):
        if hasattr(self, "_user"):
            return self._user

        return self.owner

    ##
    # Format URL to protocol
    ##
    def format(self, protocol):
        return self._platform_obj.FORMATS[protocol] % self._parsed

    ##
    # Normalize
    ##
    @property
    def normalized(self):
        return self.format(self.protocol)

    ##
    # Rewriting
    ##
    @property
    def url2ssh(self):
        return self.format("ssh")

    @property
    def url2http(self):
        return self.format("http")

    @property
    def url2https(self):
        return self.format("https")

    @property
    def url2git(self):
        return self.format("git")

    # All supported Urls for a repo
    @property
    def urls(self):
        return dict(
            (protocol, self.format(protocol))
            for protocol in self._platform_obj.PROTOCOLS
        )

    ##
    # Platforms
    ##
    @property
    def github(self):
        return self.platform == "github"

    @property
    def bitbucket(self):
        return self.platform == "bitbucket"

    @property
    def friendcode(self):
        return self.platform == "friendcode"

    @property
    def assembla(self):
        return self.platform == "assembla"

    @property
    def gitlab(self):
        return self.platform == "gitlab"

    ##
    # Get data as dict
    ##
    @property
    def data(self):
        return dict(self._parsed)


def get_repo_name(dflt="UNKNOWN"):
    try:
        repo_name = dflt
        remote_repo = execute(COMMAND_REMOTE_URL)
        try:
            r = GitUrlParsed(parse_repo_url(url=remote_repo, check_domain=True))
            repo_name = r.repo
        except Exception as exc:
            logging.exception(exc, exc_info=True)
        logging.debug("REPO_NAME: {}".format(repo_name))
        repo_name = repo_name.replace(".git", "")
    except Exception as ex:
        print("get_repo_name", ex)
        sys.exit(1)
    return repo_name


class ThreadWithReturnValue(threading.Thread):
    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None
    ):
        threading.Thread.__init__(self, group, target, name, args, kwargs, Verbose)
        self._return = None

    def run(self):
        if self._Thread__target is not None:
            self._return = self._Thread__target(
                *self._Thread__args, **self._Thread__kwargs
            )

    def join(self):
        threading.Thread.join(self, timeout=2)
        return self._return


def _octal_repl(match_obj):
    value = match_obj.group(1)
    value = int(value, 8)
    value = chr(value)
    return value


def _decode_path(path, has_ab_prefix=True):
    try:
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

        try:
            path = RE_OCTAL_BYTE.sub(_octal_repl, path)
            if has_ab_prefix:
                assert path.startswith("a/") or path.startswith("b/")
                path = path[2:]
        except UnicodeDecodeError:
            logging.error("Error decode path: {}".format(path))
    except Exception as ex:
        print("_decode_path", ex)
        sys.exit(1)
    return path


def _pick_best_path(path_match, rename_match, path_fallback_match):
    if path_match:
        return _decode_path(path_match)

    if rename_match:
        return _decode_path(rename_match, has_ab_prefix=False)

    if path_fallback_match:
        return _decode_path(path_fallback_match)

    return None


def _parse_numstats(text):
    try:
        repo_name = REPOSITORY_NAME
        hsh = {
            "total": {
                "additions": 0,
                "deletions": 0,
                "changes": 0,
                "total": 0,
                "files": 0,
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
            hsh["total"]["deletions"] += deletions
            hsh["total"]["changes"] += insertions + deletions
            hsh["total"]["total"] += insertions + deletions
            hsh["total"]["files"] += 1
            hsh["files"][filename.strip()] = {
                "filename": filename.strip(),
                "additions": insertions,
                "deletions": deletions,
                "changes": insertions + deletions,
            }
    except Exception as ex:
        print("_parse_numstats", ex)
        sys.exit(1)
    return (hsh["total"], hsh["files"])


def _parse_stats(text):
    try:
        diffs = dict()
        repo_name = REPOSITORY_NAME

        for line in text.splitlines():
            try:
                line = line
            except Exception as e:
                pass

            if not line.startswith(":"):
                continue

            meta, _, path = line[1:].partition("\t")
            old_mode, new_mode, a_blob_id, b_blob_id, _change_type = meta.split(None, 4)

            change_type = _change_type[0]
            score_str = "".join(_change_type[1:])
            score = int(score_str) if score_str.isdigit() else None
            path = path.strip()
            a_path = path
            b_path = path
            deleted_file = False
            new_file = False
            rename_from = None
            rename_to = None

            a_blob = binascii.a2b_hex(a_blob_id)
            b_blob = binascii.a2b_hex(b_blob_id)

            filename = a_path
            previous_filename = ""
            status = ""
            sha = b_blob_id
            if change_type == "D":
                b_blob_id = None
                deleted_file = True
                filename = a_path
                status = "deleted"
            elif change_type == "A":
                a_blob_id = None
                new_file = True
                filename = a_path
                status = "added"
            elif change_type == "R":
                a_path, b_path = path.split("\t", 1)
                a_path = a_path
                b_path = b_path
                rename_from, rename_to = a_path, b_path
                previous_filename = a_path
                filename = b_path
                status = "renamed"
            elif change_type == "M":
                status = "modified"
            elif change_type == "T":
                filename = a_path
                status = "renamed"

            diff = dict(
                filename=filename if filename else filename,
                previous_filename=previous_filename
                if previous_filename
                else previous_filename,
                sha=sha,
                status=status,
                a_path=a_path if a_path else a_path,
                b_path=b_path if b_path else b_path,
                a_blob_id=a_blob_id,
                a_blob=a_blob,
                b_blob_id=b_blob_id,
                b_blob=b_blob,
                a_mode=old_mode,
                b_mode=new_mode,
                new_file=new_file,
                deleted_file=deleted_file,
                rename_from=rename_from,
                rename_to=rename_to,
                change_type=change_type,
                score=score,
                patch="",
            )

            diffs[filename if filename else filename] = diff
    except Exception as ex:
        print("_parse_stats", ex)
        sys.exit(1)
    return diffs


def _parse_patch(text):
    try:
        diffs = list()
        previous_header = None
        repo_name = REPOSITORY_NAME

        for header in RE_COMMIT_DIFF.finditer(text):
            (
                a_path_fallback,
                b_path_fallback,
                old_mode,
                new_mode,
                rename_from,
                rename_to,
                new_file_mode,
                deleted_file_mode,
                a_blob_id,
                b_blob_id,
                b_mode,
                a_path,
                b_path,
            ) = header.groups()

            new_file, deleted_file = bool(new_file_mode), bool(deleted_file_mode)
            a_path = _pick_best_path(a_path, rename_from, a_path_fallback)
            b_path = _pick_best_path(b_path, rename_to, b_path_fallback)

            if previous_header is not None:
                patch = text[previous_header.end() : header.start()]
                diffs[-1]["patch"] = patch

            a_mode = (
                old_mode
                or deleted_file_mode
                or (a_path and (b_mode or new_mode or new_file_mode))
            )
            b_mode = b_mode or new_mode or new_file_mode or (b_path and a_mode)

            a_blob_id = a_blob_id and a_blob_id
            b_blob_id = b_blob_id and b_blob_id

            a_blob = binascii.a2b_hex(a_blob_id) if a_blob_id else a_blob_id
            b_blob = binascii.a2b_hex(b_blob_id) if b_blob_id else b_blob_id

            change_type = ""
            filename = a_path
            previous_filename = ""
            status = ""
            sha = b_blob_id
            if new_file:
                change_type = "A"
                filename = b_path
                status = "added"
            elif deleted_file:
                change_type = "D"
                filename = a_path
                status = "deleted"
            elif a_path != b_path:
                change_type = "R"
                filename = b_path
                previous_filename = a_path
                status = "renamed"
            elif (a_blob and b_blob and a_blob != b_blob) or (
                not a_blob and not b_blob and a_mode != b_mode
            ):
                change_type = "M"
                status = "modified"

            diff = dict(
                filename=filename if filename else filename,
                previous_filename=previous_filename
                if previous_filename
                else previous_filename,
                sha=sha,
                status=status,
                a_path=a_path if a_path else a_path,
                b_path=b_path if b_path else b_path,
                a_blob_id=a_blob_id,
                a_blob=a_blob,
                b_blob_id=b_blob_id,
                b_blob=b_blob,
                a_mode=a_mode and a_mode,
                b_mode=b_mode and b_mode,
                new_file=new_file,
                deleted_file=deleted_file,
                rename_from=rename_from,
                rename_to=rename_to,
                change_type=change_type,
                score="",
            )

            diffs.append(diff)

            previous_header = header

            if diffs:
                patch = text[header.end() :]
                diffs[-1]["patch"] = patch

        dict_diffs = dict()
        for diff in diffs:
            dict_diffs[diff["filename"]] = diff
    except Exception as ex:
        print("_parse_patch", ex)
        sys.exit(1)
    return dict_diffs


def is_datetime_format(text):
    try:
        datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S %z")
        return True
    except ValueError:
        return False


def _parse_person(text):
    try:
        (person_name, person_email, person_date) = text.split("\t")
        if not is_datetime_format(person_date):
            person_date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S %z")

        person_date = person_date.split(" ")
        person_date = "{}T{}{}".format(person_date[0], person_date[1], person_date[2])
    except Exception as ex:
        print("_parse_person_error", ex)
        sys.exit(1)
    return {"name": person_name, "email": person_email, "date": person_date}


def execute(commandLine):
    try:
        process = subprocess.Popen(
            commandLine, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        out = process.stdout.read().strip().decode("UTF-8", errors="ignore")
        error = process.stderr.read().strip().decode("UTF-8", errors="ignore")

        if error:
            process.kill()
            if DEBUG:
                logging.debug("Execution '{}'".format(repr(commandLine)))
                logging.debug("with error '{}'".format(error))
            raise Exception(error)
    except Exception as ex:
        print("execute", ex)
        sys.exit(1)
    return out


def get_commits_sha(start, number, branch):
    try:
        get_all_commits_sha_cmd = COMMAND_GET_ALL_COMMITS_SHA.format(branch)
        all_commits_sha = execute(get_all_commits_sha_cmd)
        all_commits_sha = all_commits_sha.split("\n")
        if start == "latest":
            index = 0
        else:
            try:
                index = all_commits_sha.index(start)
            except ValueError:
                logging.error(
                    "Commit '{}' not found on branch '{}'".format(start, branch)
                )
                sys.exit(1)
        commits_sha = all_commits_sha[index : index + number]
        commits_sha.reverse()
    except Exception as ex:
        print("get_commits_sha", ex)
        sys.exit(1)
    return commits_sha


def request(url, token, data, event):
    headers = {
        "Content-Type": "application/json",
        "X-GitRepository-Event": event,
        "token": token,
    }
    try:
        session = Session()
        session.mount("http://", HTTPAdapter(max_retries=3))
        session.mount("https://", HTTPAdapter(max_retries=3))
        resp = session.post(
            url=url, data=data, headers=headers, verify=False, allow_redirects=True
        )
        result = (resp.status_code, resp.reason)
        if resp.status_code == 401:
            logging.info("Could not verify, please check it and try again.")
            sys.exit(1)
        if resp.status_code != 200:
            logging.info(
                "Can't not get a connection to the server, please check your url or token and try again. Http status {}.  Reason {}".format(
                    resp.status_code, resp.reason
                )
            )
            sys.exit(1)
            # raise Exception('Can\'t not get a connection to the server, please check your url or token and try again.')
    except Exception as e:
        logging.debug(
            "Can't not get a connection to the server, please check your url try again."
        )
        result = (None, None)
    return result


def get_project_id(base_url, project_name, token):
    try:
        url = base_url + "/api/ssh_v2/hook/fetch/?project_name={}".format(project_name)
        print(url)
        headers = {"Content-Type": "application/json", "token": token}
        session = Session()
        session.mount("http://", HTTPAdapter(max_retries=3))
        session.mount("https://", HTTPAdapter(max_retries=3))
        try:
            resp = session.get(
                url=url, headers=headers, verify=False, allow_redirects=True
            )
        except Exception as exc:
            logging.debug(
                "Unable to get project id '{}' exist in branches: '{}'".format(
                    type(exc), str(exc)
                )
            )
            raise Exception(
                "Unable to get project id '{}' exist in branches: '{}'".format(
                    type(exc), str(exc)
                )
            )

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 401:
            logging.debug("Could not verify your token, please check it and try again.")
            sys.exit(1)
            # raise Exception('Could not verify your token, please check it and try again.')

        if resp.status_code != 200:
            logging.info(
                "Can't not get a connection to the server, please check your url or token and try again. Http status {}.  Reason {}".format(
                    resp.status_code, resp.reason
                )
            )
            sys.exit(1)
            # raise Exception('Can\'t not get a connection to the server, please check your url or token and try again.')
    except Exception as ex:
        print("get_project_id", ex)
        sys.exit(1)


def get_commit_branch(sha):
    try:
        branch_list = list()
        output = execute(COMMAND_COMMIT_BRANCH.format(sha))

        for line in output.splitlines():
            if "HEAD" in line:
                continue

            line = line.replace("*", "")
            line = line.rstrip().lstrip()

            if "refs/remotes/origin/" in line:
                line = line[len("refs/remotes/origin/") :]
            elif "remotes/origin/" in line:
                line = line[len("remotes/origin/") :]
            elif "origin/" in line:
                line = line[len("origin/") :]
            elif "refs/heads/" in line:
                line = line[len("refs/heads/") :]
            elif "heads/" in line:
                line = line[len("heads/") :]

            branch_list.append(line)

        logging.debug(
            "Commit '{}' exist in branches: '{}'".format(sha, len(branch_list))
        )
        return list(set(branch_list))
    except Exception as ex:
        print("get_commit_branch", ex)
        sys.exit(1)


# exclude = set(['.git', '$tf'])
# allFileNames = []
# DirectoryPath = '.'
# def get_file_tree():
#     for path, subdirs, files in os.walk(DirectoryPath):
#         subdirs[:] = [sub for sub in subdirs if sub not in exclude]
#         for name in files:
#             allFileNames.append(os.path.join(path, name).lstrip('.').lstrip('/'))
#     return allFileNames
exclude = set([".git", "$tf"])


def get_file_tree():
    try:
        files_paths = []
        # repo_name = get_repo_name()
        repo_name = REPOSITORY_NAME
        for path, subdirs, files in os.walk("."):
            subdirs[:] = [sub for sub in subdirs if sub not in exclude]
            for name in files:
                file_path = (
                    os.path.join(path, name).lstrip(".").lstrip("/").lstrip("\\")
                )
                repo_file_path = file_path
                files_paths.append(repo_file_path)
        return files_paths
    except Exception as ex:
        print("get_file_tree", ex)
        sys.exit(1)


def get_parent_commit_min(sha_parent, blame=False):
    try:
        logging.debug("[Parrent] Commit cmd for commit info : {}".format(sha_parent))
        # Get commit, parents
        commit_cmd = COMMAND_COMMIT_COMMIT_INFO_MIN.format(sha_parent)
        if is_windows:
            commit_cmd = commit_cmd.replace("'", '"')
            commit_cmd = commit_cmd.replace("\t", "%x09")

        logging.debug("Commit cmd for commit info : {}".format(commit_cmd))
        output = execute(commit_cmd)
        logging.debug("Output commit info {}".format(output))

        commit_info = RE_COMMIT_HEADER_COMMIT_INFO.findall(output)[0]
        logging.debug("Output info regex {}".format(commit_info))
        commit_numstats = {
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "total": 0,
            "files": 0,
        }
        sha, date, tree, parents, file_stats, file_numstats, patch = commit_info
        logging.debug("parents {}".format(commit_info))
        date = date.split(" ")
        date = "{}T{}{}".format(date[0], date[1], date[2])

        # Get person involve commit info
        commit_cmd = COMMAND_COMMIT_PERSON_INFO_MIN.format(sha_parent)
        if is_windows:
            commit_cmd = commit_cmd.replace("'", '"')
            commit_cmd = commit_cmd.replace("\t", "%x09")

        logging.debug(
            "Commit cmd for commit person related info : {}".format(commit_cmd)
        )
        output = execute(commit_cmd)

        logging.debug("Output person involve commit info {}".format(output))

        commit_person = RE_COMMIT_HEADER_COMMIT_PERSON.findall(output)[0]
        logging.debug("Output person regex {}".format(commit_person))
        author, committer, file_stats, file_numstats, patch = commit_person

        author = _parse_person(author)
        committer = _parse_person(committer)

        # Get commit message info
        commit_cmd = COMMAND_COMMIT_MSG_MIN.format(sha_parent)
        if is_windows:
            commit_cmd = commit_cmd.replace("'", '"')
        logging.debug("Commit cmd for commit message: {}".format(commit_cmd))
        output = execute(commit_cmd)
        logging.debug("Output commit message info {}".format(output))
        commit_msg = RE_COMMIT_HEADER_MSG.findall(output)[0]
        logging.debug("Output msg regex {}".format(commit_msg))

        message, file_stats, file_numstats, patch = commit_msg
        commit_numstats = {
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "total": 0,
            "files": 0,
        }

        commit = dict(
            sha=sha,
            tree=tree,
            parents=parents,
            date=date,
            message=message,
            author=author,
            committer=committer,
            stats=commit_numstats,
            files=[],
            added=[],
            removed=[],
            modified=[],
        )

        if file_numstats:
            commit_numstats, file_numstats = _parse_numstats(file_numstats)
        else:
            file_numstats = {}

        if file_stats:
            file_stats = _parse_stats(file_stats)
        else:
            file_stats = {}

        if patch:
            patch = _parse_patch(patch)
        else:
            patch = {}

        filename_list_1 = []
        filename_list_2 = []
        filename_list_3 = []

        for filename, data in file_numstats.items():
            filename_list_1.append(filename)

        for filename, data in file_stats.items():
            filename_list_2.append(filename)

        for filename, data in patch.items():
            filename_list_3.append(filename)

        for filename in set(filename_list_1 + filename_list_2 + filename_list_3):
            if isinstance(filename, bytes):
                filename = filename.decode("utf-8", errors="ignore")

            try:
                numstat = file_numstats[filename]
                stat = file_stats[filename]
                diff = patch[filename]
            except Exception as e:
                traceback.print_exc()
                continue

            if blame:
                try:
                    blame = get_commit_file_blame(
                        filename=filename, sha=sha, patch=diff["patch"]
                    )
                except Exception as e:
                    blame = ""
            else:
                blame = ""

            file_object = dict(
                filename=filename,
                additions=numstat["additions"],
                deletions=numstat["deletions"],
                changes=numstat["changes"],
                sha=stat["sha"],
                status=stat["status"],
                previous_filename=stat["previous_filename"],
                patch=diff["patch"],
                blame=blame or "",
            )

            if stat["status"] == "added":
                commit["added"].append(filename)
            elif stat["status"] == "added":
                commit["added"].append(filename)
            elif stat["status"] == "deleted":
                commit["removed"].append(filename)
            elif stat["status"] == "modified":
                commit["modified"].append(filename)
            elif stat["status"] == "renamed":
                commit["removed"].append(stat["previous_filename"])
                commit["added"].append(filename)
            elif stat["status"] == "unknown":
                commit["modified"].append(filename)

            commit["files"].append(file_object)

        return commit
    except Exception as ex:
        print("get_parent_commit", ex)
        sys.exit(1)


def get_parent_commit(sha_parent, blame=False):
    try:
        # Get commit, parents
        commit_cmd = COMMAND_COMMIT_COMMIT_INFO.format(sha_parent)
        if is_windows:
            commit_cmd = commit_cmd.replace("'", '"')
            commit_cmd = commit_cmd.replace("\t", "%x09")

        logging.debug("Commit cmd for commit info : {}".format(commit_cmd))
        output = execute(commit_cmd)
        logging.debug("Output commit info {}".format(output))

        commit_info = RE_COMMIT_HEADER_COMMIT_INFO.findall(output)[0]
        logging.debug("Output info regex {}".format(commit_info))
        commit_numstats = {
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "total": 0,
            "files": 0,
        }
        sha, date, tree, parents, file_stats, file_numstats, patch = commit_info
        logging.debug("parents {}".format(commit_info))
        date = date.split(" ")
        date = "{}T{}{}".format(date[0], date[1], date[2])

        # Get person involve commit info
        commit_cmd = COMMAND_COMMIT_PERSON_INFO.format(sha_parent)
        if is_windows:
            commit_cmd = commit_cmd.replace("'", '"')
            commit_cmd = commit_cmd.replace("\t", "%x09")

        logging.debug(
            "Commit cmd for commit person related info : {}".format(commit_cmd)
        )
        output = execute(commit_cmd)

        logging.debug("Output person involve commit info {}".format(output))

        commit_person = RE_COMMIT_HEADER_COMMIT_PERSON.findall(output)[0]
        logging.debug("Output person regex {}".format(commit_person))
        author, committer, file_stats, file_numstats, patch = commit_person

        author = _parse_person(author)
        committer = _parse_person(committer)

        # Get commit message info
        commit_cmd = COMMAND_COMMIT_MSG.format(sha_parent)
        if is_windows:
            commit_cmd = commit_cmd.replace("'", '"')
        logging.debug("Commit cmd for commit message: {}".format(commit_cmd))
        output = execute(commit_cmd)
        logging.debug("Output commit message info {}".format(output))
        commit_msg = RE_COMMIT_HEADER_MSG.findall(output)[0]
        logging.debug("Output msg regex {}".format(commit_msg))

        message, file_stats, file_numstats, patch = commit_msg
        commit_numstats = {
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "total": 0,
            "files": 0,
        }

        commit = dict(
            sha=sha,
            tree=tree,
            parents=parents,
            date=date,
            message=message,
            author=author,
            committer=committer,
            stats=commit_numstats,
            files=[],
            added=[],
            removed=[],
            modified=[],
        )

        if file_numstats:
            commit_numstats, file_numstats = _parse_numstats(file_numstats)
        else:
            file_numstats = {}

        if file_stats:
            file_stats = _parse_stats(file_stats)
        else:
            file_stats = {}

        if patch:
            patch = _parse_patch(patch)
        else:
            patch = {}

        filename_list_1 = []
        filename_list_2 = []
        filename_list_3 = []

        for filename, data in file_numstats.items():
            filename_list_1.append(filename)

        for filename, data in file_stats.items():
            filename_list_2.append(filename)

        for filename, data in patch.items():
            filename_list_3.append(filename)

        for filename in set(filename_list_1 + filename_list_2 + filename_list_3):
            if isinstance(filename, bytes):
                filename = filename.decode("utf-8", errors="ignore")

            try:
                numstat = file_numstats[filename]
                stat = file_stats[filename]
                diff = patch[filename]
            except Exception as e:
                traceback.print_exc()
                continue

            if blame:
                try:
                    blame = get_commit_file_blame(
                        filename=filename, sha=sha, patch=diff["patch"]
                    )
                except Exception as e:
                    blame = ""
            else:
                blame = ""

            file_object = dict(
                filename=filename,
                additions=numstat["additions"],
                deletions=numstat["deletions"],
                changes=numstat["changes"],
                sha=stat["sha"],
                status=stat["status"],
                previous_filename=stat["previous_filename"],
                patch=diff["patch"],
                blame=blame or "",
            )

            if stat["status"] == "added":
                commit["added"].append(filename)
            elif stat["status"] == "added":
                commit["added"].append(filename)
            elif stat["status"] == "deleted":
                commit["removed"].append(filename)
            elif stat["status"] == "modified":
                commit["modified"].append(filename)
            elif stat["status"] == "renamed":
                commit["removed"].append(stat["previous_filename"])
                commit["added"].append(filename)
            elif stat["status"] == "unknown":
                commit["modified"].append(filename)

            commit["files"].append(file_object)

        return commit
    except Exception as ex:
        print("get_parent_commit", ex)
        sys.exit(1)


def get_commit_file_blame(filename, sha, patch, ignore=True):
    try:
        if ignore:
            return ""

        blame = list()
        patch_strings = patch.split("\n")
        current_string_number = 0
        previous_number = 0
        group = []
        groups = []
        for stat_string in patch_strings:
            if "@@" in stat_string:
                try:
                    current_string_number = abs(
                        int(
                            stat_string.split(" @@ ")[0]
                            .split("@@ ")[-1]
                            .split(" ")[0]
                            .split(",")[0]
                        )
                    )
                except Exception:
                    continue
            else:
                if stat_string.startswith("-"):
                    if current_string_number - previous_number == 1:
                        group.append(current_string_number)
                    else:
                        groups.append(group)
                        group = [current_string_number]
                    previous_number = current_string_number
                current_string_number += 1
        groups.append(group)

        threads = list()
    except Exception as ex:
        print("get_commit_file_blame", ex)
        sys.exit(1)

    def _get_blame(sha, start_string, end_string, filename):
        result = ""
        try:
            result = execute(
                COMMAND_COMMIT_FILE_BLAME.format(
                    sha, start_string, end_string, filename
                )
            )

        except Exception as e:
            if str(e).startswith("fatal: file "):
                result = ""
            elif str(e).startswith("fatal: no such"):
                try:
                    if execution_type.lower() == "jenkins":
                        corrective_sha = execute(
                            COMMAND_COMMIT_FILE_BLAME_FIX_JENKINS.format(sha, filename)
                        )
                    else:
                        corrective_sha = execute(
                            COMMAND_COMMIT_FILE_BLAME_FIX.format(sha, filename)
                        )
                    result = execute(
                        COMMAND_COMMIT_FILE_BLAME.format(
                            corrective_sha, start_string, end_string, filename
                        )
                    )
                except Exception as e:
                    result = ""
            else:
                result = ""

        return result

    try:
        for string_group in groups:
            if not string_group:
                continue

            x = ThreadWithReturnValue(
                target=_get_blame,
                args=(
                    sha,
                    string_group[0],
                    string_group[-1],
                    filename,
                ),
            )
            threads.append(x)
            x.start()

        for index, thread in enumerate(threads):
            result = thread.join()
            if result or result != "":
                blame.append(result)

        if len(blame) > 0:
            return "\n\n".join(blame)
        return ""
    except Exception as ex:
        print("_get_blame", ex)
        sys.exit(1)


def get_commit(sha, blame=False):
    try:
        # Get commit, parents
        commit_cmd = COMMAND_COMMIT_COMMIT_INFO.format(sha)
        if is_windows:
            commit_cmd = commit_cmd.replace("'", '"')
            commit_cmd = commit_cmd.replace("\t", "%x09")

        logging.debug("Commit cmd for commit info : {}".format(commit_cmd))
        output = execute(commit_cmd)
        logging.debug("Output commit info {}".format(output))

        commit_info = RE_COMMIT_HEADER_COMMIT_INFO.findall(output)[0]

        commit_numstats = {
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "total": 0,
            "files": 0,
        }
        sha, date, tree, parents, file_stats, file_numstats, patch = commit_info
        logging.debug("parents {}".format(commit_info))
        date = date.split(" ")
        date = "{}T{}{}".format(date[0], date[1], date[2])

        # Get person involve commit info
        commit_cmd = COMMAND_COMMIT_PERSON_INFO.format(sha)
        if is_windows:
            commit_cmd = commit_cmd.replace("'", '"')
            commit_cmd = commit_cmd.replace("\t", "%x09")

        logging.debug(
            "Commit cmd for commit person related info : {}".format(commit_cmd)
        )
        output = execute(commit_cmd)

        logging.debug("Output person involve commit info {}".format(output))

        commit_person = RE_COMMIT_HEADER_COMMIT_PERSON.findall(output)[0]

        author, committer, file_stats, file_numstats, patch = commit_person

        author = _parse_person(author)
        committer = _parse_person(committer)

        # Get commit message info
        commit_cmd = COMMAND_COMMIT_MSG.format(sha)
        if is_windows:
            commit_cmd = commit_cmd.replace("'", '"')
        logging.debug("Commit cmd for commit message: {}".format(commit_cmd))
        output = execute(commit_cmd)
        logging.debug("Output commit message info {}".format(output))
        commit_msg = RE_COMMIT_HEADER_MSG.findall(output)[0]

        message, file_stats, file_numstats, patch = commit_msg
        commit_numstats = {
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "total": 0,
            "files": 0,
        }

        sha_parent_list = [
            parent_sha for parent_sha in parents.split(" ") if parent_sha
        ]
        logging.debug("sha_parent_list {}".format(sha_parent_list))
        parent_commits = list()
        for sha_parent in sha_parent_list:
            # parent_commit = get_parent_commit(sha_parent=sha_parent, blame=blame)
            if minimize:
                parent_commit = get_parent_commit_min(
                    sha_parent=sha_parent, blame=blame
                )
            else:
                parent_commit = get_parent_commit(sha_parent=sha_parent, blame=blame)
            parent_commits.append(parent_commit)
        logging.debug("parent_commits {}".format(parent_commits))

        commit = dict(
            sha=sha,
            tree=tree,
            parents=parent_commits,
            date=date,
            message=message,
            author=author,
            committer=committer,
            stats=commit_numstats,
            files=[],
            added=[],
            removed=[],
            modified=[],
        )

        if file_numstats:
            commit_numstats, file_numstats = _parse_numstats(file_numstats)
        else:
            file_numstats = {}
        logging.debug("parsed numstats")
        if file_stats:
            file_stats = _parse_stats(file_stats)
        else:
            file_stats = {}
        logging.debug("parsed file_stats")
        if patch:
            patch = _parse_patch(patch)
        else:
            patch = {}
        logging.debug("parsed _parse_patch")
        filename_list_1 = []
        filename_list_2 = []
        filename_list_3 = []

        for filename, data in file_numstats.items():
            filename_list_1.append(filename)

        for filename, data in file_stats.items():
            filename_list_2.append(filename)

        for filename, data in patch.items():
            filename_list_3.append(filename)
        logging.debug("parsed filename")
        for filename in set(filename_list_1 + filename_list_2 + filename_list_3):
            try:
                numstat = file_numstats[filename]
                stat = file_stats[filename]
                diff = patch[filename]
            except Exception as e:
                traceback.print_exc()
                continue

            if blame:
                try:
                    blame = get_commit_file_blame(
                        filename=filename, sha=sha, patch=diff["patch"]
                    )
                except Exception as e:
                    blame = ""
            else:
                blame = ""

            file_object = dict(
                filename=filename,
                additions=numstat["additions"],
                deletions=numstat["deletions"],
                changes=numstat["changes"],
                sha=stat["sha"],
                status=stat["status"],
                previous_filename=stat["previous_filename"],
                patch=diff["patch"],
                blame=blame or "",
            )

            if stat["status"] == "added":
                commit["added"].append(filename)
            elif stat["status"] == "added":
                commit["added"].append(filename)
            elif stat["status"] == "deleted":
                commit["removed"].append(filename)
            elif stat["status"] == "modified":
                commit["modified"].append(filename)
            elif stat["status"] == "renamed":
                commit["removed"].append(stat["previous_filename"])
                commit["added"].append(filename)
            elif stat["status"] == "unknown":
                commit["modified"].append(filename)

            commit["files"].append(file_object)

        return commit
    except Exception as ex:
        print("get_commit", ex)
        sys.exit(1)


def wrap_push_event(ref, commits, file_tree, repo_name=""):
    try:
        data = {
            "before": commits[0]["sha"],
            "after": commits[-1]["sha"],
            "ref": ref,
            "base_ref": "",
            "ref_type": "commit",
            "commits": commits,
            "size": len(commits),
            "head_commit": commits[-1],
            "file_tree": file_tree,
            "repo_name": repo_name,
        }
        return json.dumps(data)
    except Exception as e:
        logging.debug("Incorrect chunk: '{}'. {}".format(commits, e), exc_info=DEBUG)
        return json.dumps({})


def performPush(url, token, start, number, branch, blame, repo_name=""):
    try:
        logging.debug("Getting Commits")
        sha_list = get_commits_sha(start=start, number=number, branch=branch)
        logging.debug("Commits found {}".format(sha_list))
        commits = list()
        logging.debug("Getting Commit Details")
        for sha in sha_list:
            commit = get_commit(sha=sha, blame=blame)
            logging.debug("Commit Details Found")
            commits.append(commit)
            logging.debug("Commit Added")
        logging.debug("Getting FileTree")
        file_tree = get_file_tree()
        logging.debug("Wrapping Data")
        data = wrap_push_event(
            ref=branch, commits=commits, file_tree=file_tree, repo_name=repo_name
        )
        current_time = (
            datetime.datetime.now(datetime.timezone.utc)
            .astimezone()
            .strftime("%Y-%m-%dT")
        )
        logging.debug("Writing Logs")
        with open(f"./.testbrain/debug/{current_time}.json", "w") as f:
            f.write(data)
        logging.debug("Sending Data")
        status_code, content = request(url, token, data, event="push")
        logging.info("Data has been sent with status_code {}".format(status_code))
    except Exception as ex:
        print("performPush_error", ex)
        sys.exit(1)


def gittoappsurify():
    logging.info("Started syncing commits to {}".format(base_url))
    performPush(
        url=url,
        token=token,
        start=start,
        number=number,
        branch=branch,
        blame=blame,
        repo_name=REPOSITORY_NAME,
    )
    logging.info("Successfully synced commits to {}".format(base_url))
    logging.info("Start commit: {}".format(start))
    logging.info("Number of commit(s): {}".format(number))


# example usage gittoappsurify --url "https://demo.appsurify.com/" --project "GitScript"
# --token "MTU6ZW9FZUxhcXpMZU9CdGZZVmZ4U3BFM3g5MmhVcDl5ZmQzampUWEM1SWRfNA"

# --start "a3b8cad7c079beab89e8fba3f497fe5a1fff367d" --branch "master"
parser = argparse.ArgumentParser(
    description="Sync a number of commits before a specific commit"
)

parser.add_argument(
    "--url", type=str, required=True, help="Enter your organization url"
)
parser.add_argument("--project", type=str, required=True, help="Enter project name")
parser.add_argument(
    "--token", type=str, required=True, help="The API key to communicate with API"
)
parser.add_argument(
    "--start",
    type=str,
    required=True,
    help="Enter the commit that would be the starter",
)
parser.add_argument(
    "--number", type=int, help="Enter the number of commits that would be returned"
)
parser.add_argument(
    "--branch",
    type=str,
    required=True,
    help="Enter the explicity branch to process commit",
)
parser.add_argument(
    "--blame", action="store_true", help="Choose to commit revision of each line or not"
)
parser.add_argument(
    "--debug", action="store_true", help="Write data of commits to json file"
)
parser.add_argument(
    "--repo_name", type=str, required=False, default="", help="Define repository name"
)
parser.add_argument(
    "--auto_repo_name",
    action="store_true",
    default=False,
    help="Use GitRepository remote as repository name.",
)
parser.add_argument(
    "--execution_type",
    type=str,
    required=False,
    default="default",
    help="Execution modification",
)
parser.add_argument("--minimize", dest="minimize", action="store_true")
parser.set_defaults(minimize=False)

args = parser.parse_args()
base_url = args.url.rstrip("/")
project = args.project
token = args.token
start = args.start
number = args.number if args.number else 100
branch = args.branch
blame = args.blame
debug = args.debug
execution_type = args.execution_type
minimize = args.minimize

if debug:
    logging.info("Setting debug")
    logging.getLogger().setLevel(logging.DEBUG)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.DEBUG)
debug = True

repo_name = args.repo_name
auto_repo_name = args.auto_repo_name
if auto_repo_name:
    REPOSITORY_NAME = get_repo_name()
else:
    REPOSITORY_NAME = repo_name
logging.debug("Finding project id")

try:
    project_id_data = get_project_id(
        base_url=base_url, project_name=project, token=token
    )
except Exception as exc:
    sys.exit(1)
logging.debug("Project id set")

if "project_id" in project_id_data:
    project_id = project_id_data["project_id"]
    url = base_url + "/api/ssh_v2/hook/{}/".format(project_id)
elif "error" in project_id_data:
    logging.debug("Project not found")
    sys.exit(1)

if __name__ == "__main__":
    gittoappsurify()
