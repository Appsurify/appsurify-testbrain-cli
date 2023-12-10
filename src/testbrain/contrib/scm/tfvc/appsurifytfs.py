# -*- coding: utf-8 -*-

#!/usr/bin/env python3
# requires python>3.6

# upload - https://www.youtube.com/watch?v=zhpI6Yhz9_4&ab_channel=MakerBytes
# python setup.py sdist
# twine upload --git-url https://upload.pypi.org/legacy/ dist/*

import json
import logging
import logging.handlers as handlers
import os
import string
import sys
import warnings
from datetime import datetime
from functools import reduce
from subprocess import PIPE, Popen

try:
    import requests
    from requests.adapters import HTTPAdapter, Retry
    from requests.sessions import Session
except ImportError:
    warnings.warn("Please install 'requests'. 'pip install requests'")
    sys.exit(1)

import re

DEFAULT_BRANCH = "$/Philips.PIC/PIIC iX/Main"
CURRENT_BRANCH = DEFAULT_BRANCH

logHandler = handlers.RotatingFileHandler(
    "tfs.log", maxBytes=20 * 1024 * 1024, backupCount=10
)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] <%(module)s> (%(funcName)s) %(lineno)d: %(message)s",
    handlers=(logHandler,),
)


path = ""


if "-path" in sys.argv:
    index = sys.argv.index("-path")
    path = sys.argv[index + 1]
else:
    print("-path is required")
    # quit()

if not path.endswith("\\") and not path.endswith("/"):
    path = path + "/"

if "-organization" in sys.argv:
    index = sys.argv.index("-organization")
    organization = sys.argv[index + 1]
else:
    print("-organization is required")
    # quit()

if "-project" in sys.argv:
    index = sys.argv.index("-project")
    project = sys.argv[index + 1]
else:
    print("-project is required")
    # quit()

if "-posturl" in sys.argv:
    index = sys.argv.index("-posturl")
    POST_URL = sys.argv[index + 1]
else:
    print("-posturl is required")
    # quit()

if "-username" in sys.argv:
    index = sys.argv.index("-username")
    USERNAME = sys.argv[index + 1]
else:
    print("-username is required")
    # quit()

if "-git" in sys.argv:
    index = sys.argv.index("-git")
    REPOSITORY = sys.argv[index + 1]
else:
    print("-git is required")
    # quit()

if "-api" in sys.argv:
    index = sys.argv.index("-api")
    API_KEY = sys.argv[index + 1]
else:
    print("-api is required")
    # quit()


DirectoryPath = path

TFPath = os.getenv("AGENT_HOMEDIRECTORY")

if "-tfpath" in sys.argv:
    TFPath = sys.argv.index("-git")
    REPOSITORY = sys.argv[index + 1]
else:
    if TFPath == "" or TFPath is None:
        print("No AGENT_HOMEDIRECTORY")
        TFPath = "tf"
    else:
        if not TFPath.endswith("\\") and not TFPath.endswith("/"):
            TFPath = TFPath + "\\"
        TFPath = TFPath + "externals\\tf\\tf.exe"

TFPath = TFPath + " "

# TFPath = ""

Tf_Statistics = TFPath + 'diff "{}" /noprompt /version:{}~{} /Format:Unified'
Tf_All_Branches_Created_From_Main = TFPath + "branches ."
TF_LastChangeSet = TFPath + "changeset /noprompt /latest"
TF_Branches_History = (
    TFPath + 'history "{}" /noprompt /format:detailed /sort:Descending /recursive'
)
TF_Patch = TFPath + "difference /shelveset:{} /noprompt"
A = TFPath + "difference /shelveset:testshelve /noprompt"
get_changesets_url = (
    "https://dev.azure.com/{}/{}/_apis/tfvc/changesets?api-version=5.0&skip={}"
)
TFPT_Blame = 'TFPT.EXE annotate /noprompt "{};C{}"'
TF_Shelvet_Details = TFPath + "stat /shelveset:{} /format:detailed /user:*"
TF_Shelvet = TFPath + "shelvesets {} /format:detailed /owner:*"
MoveToMainDirectory = "cd " + DirectoryPath + " && "


EVENT_INSTALL = "install"
EVENT_PUSH = "push"
EVENT_CREATE = "create"
EVENT_DELETE = "delete"

COMMIT_COUNT = 50

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".testbrain.db")
logging.debug("DB_FILE: {}".format(DB_FILE))
CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".testbrain.cache"
)
logging.debug("CACHE_FILE: {}".format(CACHE_FILE))

login_details = ""
print("reset login details")


class FileLockException(Exception):
    pass


class CommitHistory(object):
    def __init__(self, location):
        self.cache = set()
        self.location = os.path.expanduser(location)
        self.load(self.location)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dump()

    def load(self, location):
        if os.path.exists(location):
            self._load()
        else:
            logging.error(
                "Cache file '{location}' does not exists".format(location=location)
            )
        return True

    def _load(self):
        self.cache = set(open(self.location, "r").read().splitlines())

    def dump(self):
        try:
            open(self.location, "w+").write("\n".join(self.cache.__iter__()))
            return True
        except Exception as e:
            logging.error(e, exc_info=True)
            return False

    def add(self, element):
        self.cache.add(element)
        self.dump()
        return True

    def update(self, elements):
        self.cache.update(elements)
        self.dump()
        return True

    def find(self, element):
        return element in self.cache

    def delete(self, element):
        self.cache.discard(element)
        return True

    def reset(self):
        self.cache = set()
        self.dump()
        return True


cache = CommitHistory(location=CACHE_FILE)


class SimpleDB(object):
    def __init__(self, location):
        self.location = os.path.expanduser(location)
        self.load(self.location)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dumpdb()

    def load(self, location):
        if os.path.exists(location):
            self._load()
        else:
            self.db = {}
        return True

    def _load(self):
        self.db = json.load(open(self.location, "r"))

    def dumpdb(self):
        try:
            json.dump(self.db, open(self.location, "w+"))
            return True
        except Exception as e:
            logging.error("Error saving database file. '{}'".format(e), exc_info=True)
            return False

    def set(self, key, value):
        try:
            self.db[str(key)] = value
            self.dumpdb()
        except Exception as e:
            logging.error(
                "Error saving values to database. '{}'".format(e), exc_info=True
            )
            return False

    def get(self, key):
        try:
            return self.db[key]
        except KeyError:
            logging.debug("No Value Can Be Found for {}".format(key))
            return False

    def delete(self, key):
        if not key in self.db:
            return False
        del self.db[key]
        self.dumpdb()
        return True

    def resetdb(self):
        self.db = {}
        self.dumpdb()
        return True


database = SimpleDB(location=DB_FILE)  # TODO: Maybe need move to down


def set_last_changeset_id(key, val):
    database.set(key, val)


def request(event, data):
    headers = {
        "Content-Type": "application/json",
        "X-Git-Event": event,
        "token": API_KEY,
    }
    try:
        retry = Retry(
            total=3,
            connect=120,
            read=120,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504),
            raise_on_redirect=False,
            raise_on_status=False,
        )
        session = Session()
        session.mount("http://", HTTPAdapter(max_retries=retry))
        session.mount("https://", HTTPAdapter(max_retries=retry))
        logging.debug(
            "URL: {} HEADERS(json): {} DATA(json): {}".format(
                POST_URL, json.dumps(headers), json.dumps(data)
            )
        )
        resp = session.post(
            url=POST_URL, data=data, headers=headers, verify=False, allow_redirects=True
        )
        result = (resp.status_code, resp.reason)
    except Exception as e:
        logging.error(e, exc_info=True)
        result = (None, None)
    return result


def get_all_changesets_rest_api():
    arr = []

    def get_data():
        r = requests.get(
            str.format(get_changesets_url, organization, project, len(arr)),
            auth=(),
        )
        if r.status_code == 200:
            json = r.json()
            count = json["count"]
            value = json["value"]
            arr.extend(value)

            if count != len(arr):
                get_data()

    get_data()
    return arr


def execute(commandLine):
    commandLine = commandLine + login_details
    logging.debug("CMD: '{}'".format(commandLine))
    process = Popen(commandLine, shell=True, stdout=PIPE, stderr=PIPE)
    out = process.stdout.read().decode("utf-8", errors="ignore").strip()
    out = str.join("", list([x for x in out if x in string.printable]))
    logging.debug("CMD: '{}' RESULT: {}".format(commandLine, out))
    error = process.stderr.read().decode("utf-8", errors="ignore").strip()
    error = str.join("", list([x for x in error if x in string.printable]))
    if error and not out:
        process.kill()
        logging.error("CMD: '{}' IF ERR OUT {}".format(commandLine, out))
        logging.error("CMD: '{}' {}".format(commandLine, error))
        raise Exception(error)
    return out


def get_last_changeset(branch):
    command = MoveToMainDirectory + TF_LastChangeSet
    output = execute(command.format(branch))
    if output:
        splits = output.split("\n")
        if len(splits) > 1:
            return splits[0][11:].strip()
        else:
            return None
    return None


def get_branch_list():
    branchesDict = {}
    output = execute(MoveToMainDirectory + Tf_All_Branches_Created_From_Main)

    for row in output.split("\n"):
        row = row.strip()
        if row:
            indexA = row.find("Branched from version")
            indexB = row.find("<<")
            index = indexA if indexA > 0 else indexB
            branch = row[row.find(project) + len(project) + 1 : index].strip()
            last_changeSet_id = get_last_changeset(branch)
            branchesDict[branch] = last_changeSet_id
    return branchesDict


def get_last_branch_changeSet(branch, numberOfChangets):
    output = execute(
        MoveToMainDirectory
        + TF_Branches_History.format(branch)
        + (
            ""
            if numberOfChangets == None
            else " /stopafter:{}".format(numberOfChangets)
        )
    )

    endline_char = detect_endline(output)

    changeSetList = []

    output_list = [
        item.lstrip() for item in output.split("-" * 79 + endline_char) if item
    ]

    idx = 0

    for changeset_raw in output_list:
        changeSetDict = {}
        itemsDict = {}

        changeSetDict["branch"] = branch
        changeSetDict["items"] = itemsDict

        changeset_info_items = list()

        propertyNames = f_pattern.findall(changeset_raw)
        for item in propertyNames:
            cur_idx = propertyNames.index(item)
            next_idx = propertyNames.index(item) + 1
            if next_idx <= len(propertyNames) - 1:
                itm = changeset_raw[
                    changeset_raw.find(propertyNames[cur_idx]) : changeset_raw.find(
                        propertyNames[next_idx]
                    )
                ]
            else:
                itm = changeset_raw[changeset_raw.find(propertyNames[cur_idx]) :]
            changeset_info_items.append(itm)

        # changeset_info_items = changeset_raw.split(endline_char + endline_char)
        changeset_items = list()

        for changeset_info_item in changeset_info_items:
            if any(
                changeset_info_item.startswith(keyword)
                for keyword in ["Changeset", "User", "Date"]
            ):
                changeset_info_item = changeset_info_item.split(endline_char)
                changeset_items.extend(changeset_info_item)
            else:
                changeset_info_item = changeset_info_item.replace(endline_char, "\n")
                changeset_items.append(changeset_info_item)

        idx += 1
        for changeset_item in changeset_items:
            for item in pattern.finditer(changeset_item):
                propertyName, propertyData = item.groups()
                propertyName = propertyName.lstrip().rstrip().replace(" ", "_").lower()
                propertyData = propertyData.lstrip().rstrip()

                changeSetDict[propertyName] = propertyData

                if propertyName == "items":
                    for i in propertyData.split("\n"):
                        i = i.lstrip().rstrip()
                        action = i[: i.find("$/")]
                        filename = i[i.find("$/") :]

                        action = action.lstrip().rstrip()
                        filename = filename.lstrip().rstrip()

                        if "," in action:
                            # actions = action.split(', ')
                            # if all(s in actions for s in ('delete', 'source rename')):
                            #     action = 'delete'
                            # if all(s in actions for s in ('delete', 'rollback')):
                            #     action = 'delete'
                            # elif all(s in actions for s in ('encoding', 'edit')):
                            #     action = 'edit'
                            # elif all(s in actions for s in ('merge', 'edit')):
                            #     action = 'edit'
                            # elif all(s in actions for s in ('edit', 'rollback')):
                            #     action = 'edit'
                            # elif all(s in actions for s in ('rename', 'edit')):
                            #     action = 'rename'
                            # elif all(s in actions for s in ('add', 'source rename')):
                            #     action = 'add'
                            if action.startswith("add"):
                                action = "add"
                            elif action.startswith("delete"):
                                action = "delete"
                            elif action.startswith("edit"):
                                action = "edit"
                            elif action.startswith("rename"):
                                action = "edit"
                            elif action.startswith("merge"):
                                action = "edit"
                            elif action.startswith("encoding"):
                                action = "edit"
                            else:
                                action = "edit"

                        if action not in itemsDict:
                            itemsDict[action] = [
                                filename,
                            ]
                        else:
                            itemsDict[action].append(filename)

                    for item in itemsDict:
                        itemsDict[item] = list(set(itemsDict[item]))

                    changeSetDict["items"] = itemsDict

        changeSetDict["branch"] = branch
        changeSetList.append(changeSetDict)

    return changeSetList


def get_diff(fileName, currentChangeSet, previousChangeSet):
    command = MoveToMainDirectory + Tf_Statistics.format(
        fileName, previousChangeSet, currentChangeSet
    )
    try:
        return execute(command)
    except Exception as e:
        logging.error(e, exc_info=True)
        return e.message


def get_file_tree(basePath=""):
    allFileNames = []
    directories = []
    directories.append({"directory": DirectoryPath.strip('"'), "basePath": ""})

    def getAllFileNames(path, basePath=""):
        for dirname, dirnames, filenames in os.walk(path):
            for filename in filenames:
                try:
                    allFileNames.append(basePath + filename)
                except MemoryError:
                    break

            if "$tf" in dirnames:
                # don't go into any $tf directories.
                dirnames.remove("$tf")

            for subdirname in dirnames:
                directories.append(
                    {
                        "directory": os.path.join(dirname, subdirname),
                        "basePath": os.path.join(basePath, subdirname) + "/",
                    }
                )

    for row in directories:
        try:
            getAllFileNames(row["directory"], row["basePath"])
        except MemoryError:
            break

    return allFileNames


def get_blame(fileName, changesetId):
    try:
        command = MoveToMainDirectory + TFPT_Blame.format(fileName, changesetId)
        output = execute(command)
        return output
    except Exception as e:
        logging.error("File not found. {}".format(e), exc_info=True)
        return ""


def get_shelvet_details(name):
    command = MoveToMainDirectory + TF_Shelvet_Details.format(name)
    output = execute(command)
    data = {}
    fileName = ""
    for row in output.split("\n"):
        if row.startswith("$"):
            fileName = row
            data[row] = {}
        elif row.startswith(" "):
            row = row.strip()
            if len(row) == 0:
                continue
            splits = row.split(":")
            data[fileName][splits[0].strip()] = splits[1].strip()

    return data


def get_shelvet_info(name):
    command = MoveToMainDirectory + TF_Shelvet.format(name)
    output = execute(command)
    skipFirstRow = True
    data = {}
    for row in output.split("\n"):
        if skipFirstRow:
            skipFirstRow = False
            continue
        splits = row.split(":")
        if len(splits) < 2:
            continue

        data[splits[0].strip()] = splits[1].strip()

    return data


def wrap_changeset_push_event(
    arr, rest_api_data, file_tree=None, isBlameRequired=True, shouldRunRestApi=False
):
    length = len(arr)

    commits = []
    for changeSet in arr:
        files = []
        items = changeSet.get("items", {})
        # print(changeSet)
        changesetId = changeSet.get("changeset")
        if changesetId is None:
            value = changeSet.get("edit")
            if value is not None:
                # Changeset:
                # length of above string is 11
                changesetId = value[11:]
            else:
                raise Exception("changesetId is not set")

        date = changeSet.get(
            "date", datetime.now().strftime("%A, %B %d, %Y %I:%M:%S %p")
        )

        for key in items:
            if "," in key:
                keys = key.split(",")
                if all(s in keys for s in ("delete", "source rename")):
                    key = "delete"
                else:
                    # raise Exception("Handle multiple keys")
                    key = "edit"

            status = ""

            if key == "edit":
                status = "modified"
            elif key == "add" or key == "branch":
                status = "added"
            elif key == "delete":
                status = "deleted"
            elif key == "rename":
                status = "renamed"

            if isinstance(items[key], (list, tuple)):
                for file_item in items[key]:
                    splittedFiles = file_item.split(";")
                    splittedFile = splittedFiles[0]
                    fileName = splittedFile[splittedFile.rfind("/") + 1 :]

                    blame = ""
                    if isBlameRequired and "." in fileName and status == "modified":
                        blame = get_blame(splittedFile, changesetId)

                    files.append(
                        {
                            "status": status,
                            "deletions": 0,
                            "previous_filename": "",
                            "patch": "",
                            "blame": blame,
                            "sha": changesetId,
                            "additions": 0,
                            "filename": file_item,
                            "changes": 0,
                        }
                    )

            elif isinstance(items[key], str):
                splittedFiles = items[key].split(";")

                splittedFile = splittedFiles[0]
                fileName = splittedFile[splittedFile.rfind("/") + 1 :]

                blame = ""
                if isBlameRequired and "." in fileName and status == "modified":
                    blame = get_blame(splittedFile, changesetId)
                files.append(
                    {
                        "status": status,
                        "deletions": 0,
                        "previous_filename": "",
                        "patch": "",
                        "blame": blame,
                        "sha": changesetId,
                        "additions": 0,
                        "filename": items[key],
                        "changes": 0,
                    }
                )

        added = [x for x in files if "add" in x["status"]]
        modified = [x for x in files if "edit" in x["status"]]
        removed = [x for x in files if "delete" in x["status"]]
        renamed = [x for x in files if "rename" in x["status"]]
        try:
            datetime_object = datetime.strptime(date, "%A, %B %d, %Y %I:%M:%S %p")
            date = datetime_object.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            datetime_object = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            date = datetime_object.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        commit = {
            "files": files,
            "added": added,
            "stats": {
                "deletions": 0,
                "files": len(files),
                "additions": 0,
                "total": 0,
                "changes": 0,
            },
            "modified": modified,
            "tree": "",
            "sha": changesetId,
            "parents": [],
            "date": date,
            "branches": [changeSet["branch"]],
            "message": changeSet.get("comment"),
            "removed": removed,
            "renamed": renamed,
        }

        user = changeSet.get("user", "unknown user")

        commit["author"] = {
            "date": date,
            "name": user,
        }
        commit["committer"] = {"date": date, "name": user}

        commits.append(commit)

    commits.sort(key=lambda x: x["sha"])

    skipFirst = True
    for index, value in enumerate(commits):
        if skipFirst:
            skipFirst = False
            continue

        copy = commits[index - 1].copy()
        copy.pop("parents")
        value["parents"] = [copy]

        for file in value["files"]:
            if "edit" in file["status"]:
                file["patch"] = get_diff(
                    file["filename"][0], value["sha"], value["parents"]
                )

                if "@@" in file["patch"]:
                    patches = file["patch"].split("\n")
                    startParse = False

                    for patch in patches:
                        if startParse:
                            if "-" in patch:
                                file["deletions"] += len(patch[1:])

                            if "+" in patch:
                                file["additions"] += len(patch[1:])

                            if (
                                "==================================================================="
                                in patch
                            ):
                                break

                        if "@@" in patch:
                            startParse = True

                    file["changes"] = sum(
                        file["deletions"] for file in value["files"]
                    ) + sum(file["additions"] for file in value["files"])

        value["stats"]["deletions"] = reduce(
            lambda x, y: x + y["deletions"], value["files"], 0
        )
        value["stats"]["additions"] = reduce(
            lambda x, y: x + y["additions"], value["files"], 0
        )
        value["stats"]["changes"] = (
            value["stats"]["deletions"] + value["stats"]["additions"]
        )
        value["stats"]["total"] = value["stats"]["changes"]

    data = {
        "size": length,
        "commits": commits,
        "head_commit": commits[length - 1],
        "file_tree": file_tree,
        "git": {"name": REPOSITORY, "full_name": "{}/{}".format(USERNAME, REPOSITORY)},
        "ref_type": "commit",
        "after": "",
        "ref": CURRENT_BRANCH,
        "base_ref": "",
        "before": commits[length - 1]["sha"],
    }

    data = to_iso(data)
    return json.dumps(data)


def wrap_shelvet_push_event(arr, info):
    length = len(arr)
    data = {
        "stats": {"deletions": 0, "additions": 0, "total": 0, "changes": 0},
        "tree": "",
        "size": length,
        "head_commit": {},
        "git": {"name": REPOSITORY, "full_name": "{}/{}".format(USERNAME, REPOSITORY)},
        "ref_type": "commit",
        "after": "",
        "ref": CURRENT_BRANCH,
        "base_ref": "",
        "before": "",
    }

    files = []

    for fileName, file_info in list(arr.items()):
        status = ""
        if file_info["Change"] == "edit":
            status = "modified"
        elif file_info["Change"] == "add" or file_info["Change"] == "branch":
            status = "added"
        elif file_info["Change"] == "delete":
            status = "deleted"
        elif file_info["Change"] == "rename":
            status = "renamed"

        files.append(
            {
                "status": status,
                "deletions": 0,
                "previous_filename": "",
                "patch": "",
                "blame": "",
                "sha": file_info["Shelveset"],
                "additions": 0,
                "filename": fileName,
                "changes": 0,
            }
        )

    data["stats"]["files"] = len(files)
    data["head_commit"] = {
        "files": files,
        "committer": {"date": info["Date"], "name": info["Owner"], "email": ""},
        "added": [x for x in files if "add" in x["status"]],
        "modified": [x for x in files if "edit" in x["status"]],
        "removed": [x for x in files if "delete" in x["status"]],
        "renamed": [x for x in files if "rename" in x["status"]],
        "parents": [],
        "date": info["Date"],
        "branches": [CURRENT_BRANCH],
        "message": info["Comment"],
        "file_tree": [x["filename"] for x in files],
    }

    return json.dumps(data)


def detect_endline(text):
    if text.find("\r\n") != -1:
        return "\r\n"
    if text.find("\r") != -1:
        return "\r\r"
    if text.find("\n\n") != -1:
        return "\n\n"
    return ""


def to_iso(data):
    if isinstance(data, str):
        data = str.join("", list([x for x in data if x in string.printable]))
        return data.strip()
    elif isinstance(data, bytes):
        data = data.decode("utf-8", errors="ignore").strip()
        data = str.join("", list([x for x in data if x in string.printable]))
        return data.strip()
    elif isinstance(data, dict):
        for key in data:
            data[key] = to_iso(data[key])
        return data
    elif isinstance(data, list):
        new_list = []
        for item in data:
            new_list.append(to_iso(item))
        return new_list
    else:
        return data


def _get_last_commit_sha(key):
    commit_id = database.get(key)
    logging.debug('_get_last_commit_sha "{}" result "{}"'.format(key, commit_id))
    if commit_id is False:
        commit_id = None
    return commit_id


def slugify(value):
    import re
    import unicodedata

    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
    value = str(re.sub("[^\w\s-]", "", value).strip().lower())
    value = str(re.sub("[-\s]+", "-", value))
    # ...
    return value


def performSync(
    branch,
    shelvet,
    force=False,
    isBlameRequired=True,
    shouldRunRestApi=False,
    numberOfChangets=None,
):
    logging.info(
        "Define branch: {} / {} / {}".format(branch, CURRENT_BRANCH, DEFAULT_BRANCH)
    )
    import time

    start_time = time.time()

    rest_api_data = []
    if shouldRunRestApi:
        rest_api_data = get_all_changesets_rest_api()

    file_tree = get_file_tree()

    end_changeset_id = get_last_changeset(branch)
    logging.debug('end_changeset_id - "{}"'.format(end_changeset_id))

    last_changeset_id = _get_last_commit_sha(branch)
    logging.debug('last_changeset_id - "{}"'.format(last_changeset_id))

    if last_changeset_id == end_changeset_id and force is False:
        logging.debug(
            "last_changeset_id == end_changeset_id and force is False: RETURN"
        )
        return

    if end_changeset_id == None and force is False:
        logging.debug("end_changeset_id == None and force is False: RETURN")
        return

    logging.debug(
        "Call get_last_branch_changeSet args: {} {}".format(branch, numberOfChangets)
    )
    changesets_list = get_last_branch_changeSet(branch, numberOfChangets)
    logging.debug("changesets_list {} {}".format(branch, len(changesets_list)))

    if len(branch) > 0 and len(shelvet) <= 0:
        logging.debug("len(branch) > 0 and len(shelvet) <= 0")
        logging.debug("Call wrap_changeset_push_event")
        changeset_data = wrap_changeset_push_event(
            changesets_list,
            rest_api_data,
            file_tree,
            isBlameRequired,
            shouldRunRestApi=shouldRunRestApi,
        )

        logging.debug("Call request")
        status_code, content = request(EVENT_PUSH, changeset_data)
        logging.debug("Call response [{}] {}".format(status_code, content))
        if status_code in [200, 201]:
            logging.debug(
                "Call set_last_changeset_id args {} {}".format(branch, end_changeset_id)
            )
            set_last_changeset_id(branch, end_changeset_id)
            cache.add(end_changeset_id)
            time.sleep(5)
        else:
            logging.error(
                "EVENT: {} STATUS: {} RESP: {}".format(EVENT_PUSH, status_code, content)
            )

    if len(shelvet) > 0:
        logging.debug("len(shelvet) > 0")
        shelvet_details = get_shelvet_details(shelvet)
        shelvet_info = get_shelvet_info(shelvet)
        shelvet_data = wrap_shelvet_push_event(shelvet_details, shelvet_info)
        logging.debug("Call request")
        status_code, content = request(EVENT_PUSH, shelvet_data)
        logging.debug("Call response [{}] {}".format(status_code, content))
        if status_code in [200, 201]:
            logging.debug(
                "Call set_last_changeset_id args {} {}".format(branch, shelvet)
            )
            set_last_changeset_id(branch, shelvet)
            cache.add(shelvet)
            time.sleep(5)
        else:
            logging.error(
                "EVENT: {} STATUS: {} RESP: {}".format(EVENT_PUSH, status_code, content)
            )

    end_time = time.time()
    logging.debug("Total {} seconds".format(end_time - start_time))


def appsurifytfs(*args):
    global login_details
    logging.info("Start with args: {}".format(" ".join(sys.argv)))
    if "sync" in sys.argv:
        remotes = force = False
        blame = True
        numberOfChangets = None
        shouldRunRestApi = False
        branch = DEFAULT_BRANCH
        shelvet = ""

        if "-f" in sys.argv:
            force = True
        if "--no-blame" in sys.argv:
            blame = False
        if "--set_last_changeset_id" in sys.argv:
            index = sys.argv.index("--set_last_changeset_id")
            numberOfChangets = sys.argv[index + 1]
        if "-runApi" in sys.argv:
            shouldRunRestApi = True
        if "-branch" in sys.argv:
            index = sys.argv.index("-branch")
            branch = sys.argv[index + 1]
            global CURRENT_BRANCH
            CURRENT_BRANCH = branch
        if "-shelvet" in sys.argv:
            index = sys.argv.index("-shelvet")
            shelvet = sys.argv[index + 1]
        if "-shelveset" in sys.argv:
            index = sys.argv.index("-shelveset")
            shelvet = sys.argv[index + 1]
        if "-path" in sys.argv:
            index = sys.argv.index("-path")
            path = sys.argv[index + 1]

        if "-login" in sys.argv:
            index = sys.argv.index("-login")
            login = sys.argv[index + 1]
            login_details = " /loginType:OAuth /login:.," + login

        try:
            performSync(
                branch,
                shelvet,
                force=force,
                isBlameRequired=blame,
                shouldRunRestApi=shouldRunRestApi,
                numberOfChangets=numberOfChangets,
            )
        except Exception as e:
            logging.error(e, exc_info=True)


if __name__ == "__main__":
    appsurifytfs(sys.argv)
