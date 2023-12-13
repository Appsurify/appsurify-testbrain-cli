import pathlib
import typing as t

import pytest

from testbrain.contrib.scm.git.process import GitVCS
from testbrain.contrib.scm.exceptions import (
    ProcessError,
    BranchNotFound,
    CommitNotFound,
)


FAKE_LOG_OUTPUT = (
    "COMMIT:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n"
    "TREE:\ta2bd09a6cc8a36da7fd43a3b8445967584873e5e\n"
    "DATE:\t2023-09-29T16:13:45+03:00\n"
    "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
    "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
    "MESSAGE:\tMerge branch 'dev'\n"
    "PARENTS:\t27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210 "
    "0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd\n"
    "\n\n"
    "COMMIT:\t39c54991d3cd7f4bae68d6b58549e7e2ab084a23\n"
    "TREE:\t5c86012497523e000b3ddfd9a95967da58d77fe9\n"
    "DATE:\t2023-10-02T13:23:02+03:00\n"
    "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T13:23:02+03:00\n"
    "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T13:23:02+03:00\n"
    "MESSAGE:\tRenamed files\n"
    "PARENTS:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n\n"
    "1\t1\tCONTRIB.txt\n"
    "1\t0\tREADME.md\n"
    "0\t1\tREADME.txt"
    "\n\n"
    "diff --git a/CONTRIB.txt b/CONTRIB.txt\n"
    "index 01ea8a03269d7d23931cd2a7aa8940b14f850257.."
    "7cb38a976dd950aef3eee5e8a63c334100d7044b 100644\n"
    "--- a/CONTRIB.txt\n+++ b/CONTRIB.txt\n"
    "@@ -1 +1 @@\n-Other\n+-- empty --\n\\ No newline at end of file\n"
    "diff --git a/README.md b/README.md\n"
    "new file mode 100644\n"
    "index 0000000000000000000000000000000000000000.."
    "52da238091fabcd84e921bb6029d9addf9afd02f\n"
    "--- /dev/null\n+++ b/README.md\n"
    "@@ -0,0 +1 @@\n+# README\n\\ No newline at end of file\n"
    "diff --git a/README.txt b/README.txt\n"
    "deleted file mode 100644\n"
    "index 8038dd2b0751f5c895754871bdc6daa400008c08.."
    "0000000000000000000000000000000000000000\n"
    "--- a/README.txt\n+++ /dev/null\n@@ -1 +0,0 @@\n-QA works\n"
    "\\ No newline at end of file\n"
    "\n\n"
    "COMMIT:\tceff1b9d2d403e83b9c7c39e5baa47eff61a3524\n"
    "TREE:\tb6f23611cb888a619940c71582de2dad6e04cd42\n"
    "DATE:\t2023-10-02T13:44:07+03:00\n"
    "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T13:44:07+03:00\n"
    "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T13:44:07+03:00\n"
    "MESSAGE:\tCONTRIB rename\nPARENTS:\t39c54991d3cd7f4bae68d6b58549e7e2ab084a23\n\n"
    "0\t0\tCONTRIB.txt => CONTRIB.md"
    "\n\n"
    "diff --git a/CONTRIB.txt b/CONTRIB.md\n"
    "similarity index 100%\nrename from CONTRIB.txt\nrename to CONTRIB.md"
    "\n\n\n"
    "COMMIT:\t2c5ebc4c21b8db4917c9a30173e3f5307f8552f9\n"
    "TREE:\t60fc93ce6ab91eb56d3f3f06a3abb77b1e5b3e22\n"
    "DATE:\t2023-10-02T20:01:48+03:00\n"
    "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T20:01:48+03:00\n"
    "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T20:01:48+03:00\n"
    "MESSAGE:\tChanges\nPARENTS:\tceff1b9d2d403e83b9c7c39e5baa47eff61a3524"
    "\n\n"
    "2\t1\tCONTRIB.md\n"
    "2\t1\tREADME.md"
    "\n\n"
    "diff --git a/CONTRIB.md b/CONTRIB.md\n"
    "index 7cb38a976dd950aef3eee5e8a63c334100d7044b.."
    "7b2014660cadcd1abd84890b72177c7a35402b11 100644\n"
    "--- a/CONTRIB.md\n+++ b/CONTRIB.md\n"
    "@@ -1 +1,2 @@\n--- empty --\n\\ No newline at end of file\n"
    "+-- empty --\n+Another one\n\\ No newline at end of file\n"
    "diff --git a/README.md b/README.md\n"
    "index 52da238091fabcd84e921bb6029d9addf9afd02f.."
    "78f497a48b0b909b166245a15c8d8e8ccacc9914 100644\n"
    "--- a/README.md\n+++ b/README.md\n"
    "@@ -1 +1,2 @@\n-# README\n\\ No newline at end of file\n"
    "+# README\n+## New headline\n\\ No newline at end of file"
)


def register_limits(fp):
    limit = 999999

    fp.register(["git", "config", "--global", "merge.renameLimit", str(limit)])
    fp.register(["git", "config", "--global", "diff.renameLimit", str(limit)])
    fp.register(["git", "config", "--global", "diff.renames", "0"])

    fp.register(["git", "config", "merge.renameLimit", str(limit)])
    fp.register(["git", "config", "diff.renameLimit", str(limit)])
    fp.register(["git", "config", "diff.renames", "0"])


def test_git_vcs(fp):
    limit = 999999

    fp.register(["git", "config", "--global", "merge.renameLimit", str(limit)])
    fp.register(["git", "config", "--global", "diff.renameLimit", str(limit)])
    fp.register(["git", "config", "--global", "diff.renames", "0"])

    fp.register(["git", "config", "merge.renameLimit", str(limit)])
    fp.register(["git", "config", "diff.renameLimit", str(limit)])
    fp.register(["git", "config", "diff.renames", "0"])

    git_vcs = GitVCS()

    assert git_vcs is not None

    with pytest.raises(fp.exceptions.ProcessNotRegisteredError):
        # this will fail, as "ls" command is not registered
        git_vcs2 = GitVCS(repo_dir="./")
        assert git_vcs2.repo_dir == "./"

    register_limits(fp)
    git_vcs3 = GitVCS(repo_dir="./")
    assert git_vcs3.repo_dir == pathlib.Path("./").resolve()


def test_git_vcs_get_repo_name(fp):
    register_limits(fp)
    git_vcs = GitVCS(
        repo_dir="./appsurify-testbrain-cli", repo_name="appsurify-testbrain-cli"
    )

    assert git_vcs.repo_dir == pathlib.Path("./appsurify-testbrain-cli").resolve()
    assert git_vcs.repo_name == "appsurify-testbrain-cli"

    register_limits(fp)
    fp.register(
        ["git", "config", "--get", "remote.origin.url"],
        stdout="https://github.com/Appsurify/appsurify-testbrain-cli.git",
    )
    git_vcs = GitVCS(repo_dir="./appsurify-testbrain-cli")
    assert git_vcs.repo_dir == pathlib.Path("./appsurify-testbrain-cli").resolve()
    assert git_vcs.repo_name == "appsurify-testbrain-cli"

    register_limits(fp)
    fp.register(
        ["git", "config", "--get", "remote.origin.url"],
        stdout="",
    )
    git_vcs = GitVCS(repo_dir="./appsurify-testbrain-cli")
    assert git_vcs.repo_dir == pathlib.Path("./appsurify-testbrain-cli").resolve()
    assert git_vcs.repo_name == "appsurify-testbrain-cli"


def test_git_vcs_get_current_branch(fp):
    register_limits(fp)
    fp.register(
        ["git", "branch", "--show-current"],
        stdout="main",
    )
    git_vcs = GitVCS()
    branch = git_vcs.get_current_branch()
    assert branch == "main"


def test_git_vcs_get_branch(fp):
    register_limits(fp)
    fp.register(
        ["git", "branch", "-a"],
        stdout="* main\n"
        "remotes/origin/HEAD -> origin/main\n"
        "remotes/origin/main\n"
        "remotes/origin/rev/2023.11.9",
    )
    fp.register(
        ["git", "rev-parse", "main"], stdout="6d3bdaed89913b8b3ea6ca66f8fd2361cc0498dd"
    )
    git_vcs = GitVCS()
    branch, sha, remote = git_vcs.get_branch(branch_name="main")
    assert branch == "main"
    assert sha == "6d3bdaed89913b8b3ea6ca66f8fd2361cc0498dd"
    assert remote is False

    register_limits(fp)
    fp.register(
        ["git", "branch", "-a"],
        stdout="* main\n"
        "remotes/origin/HEAD -> origin/main\n"
        "remotes/origin/main\n"
        "remotes/origin/rev/2023.11.9",
    )
    fp.register(
        ["git", "rev-parse", "main"], stdout="6d3bdaed89913b8b3ea6ca66f8fd2361cc0498dd"
    )
    git_vcs = GitVCS()

    with pytest.raises(BranchNotFound):
        branch, sha, remote = git_vcs.get_branch(branch_name="dev")


@pytest.mark.skip(reason="no way of currently testing this")
def test_git_vcs_validate_commit(fp):
    ...


@pytest.mark.skip(reason="no way of currently testing this")
def test_git_vcs_fetch(fp):
    ...


@pytest.mark.skip(reason="no way of currently testing this")
def test_git_vcs_checkout(fp):
    ...


@pytest.mark.skip(reason="no way of currently testing this")
def test_git_vcs_commits(fp):
    ...


@pytest.mark.skip(reason="no way of currently testing this")
def test_git_vcs_file_tree(fp):
    ...
