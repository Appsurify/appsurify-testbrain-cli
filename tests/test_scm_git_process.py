import typing as t

import pytest

from testbrain.contrib.scm.git.process import GitProcess, GitVCS
from testbrain.contrib.scm.exceptions import ProcessError


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


def test_git_process(fp):
    git_process = GitProcess()

    assert git_process is not None


def test_git_process_remote_url(fp):
    git_process = GitProcess()
    fp.register(
        ["git", "config", "--get", "remote.origin.url"],
        stdout="https://github.com/Appsurify/appsurify-testbrain-cli.git",
    )
    result_remote_url = git_process.remote_url()

    assert type(result_remote_url) is str
    assert (
        result_remote_url == "https://github.com/Appsurify/appsurify-testbrain-cli.git"
    )


def test_git_process_fetch(fp):
    git_process = GitProcess()
    fp.register(
        ["git", "fetch", "-a"],
        stdout="",
    )
    result_fetch = git_process.fetch()
    assert type(result_fetch) is str
    assert result_fetch == ""

    fp.register(
        ["git", "fetch", "main"],
        stderr=(
            "fatal: 'main' does not appear to be a git git\n"
            "fatal: Could not read from remote git.\n\n"
            "Please make sure you have the correct access rights\n"
            "and the git exists."
        ),
        returncode=128,
    )

    with pytest.raises(ProcessError):
        _ = git_process.fetch(rev="main")


@pytest.mark.skip(reason="no way of currently testing this")
def test_git_process_checkout(fp):
    git_process = GitProcess()
    fp.register(
        ["git", "checkout"],
        stdout="",
    )
    result_checkout = git_process.checkout(rev="main")
    assert type(result_checkout) is str
    assert result_checkout == ""

    result_checkout = git_process.checkout(rev="main", detach=False)
    assert type(result_checkout) is str
    assert result_checkout == ""

    result_checkout = git_process.checkout(rev="main", detach=True)
    assert type(result_checkout) is str
    assert result_checkout == ""


def test_git_process_validate_commit(fp):
    git_process = GitProcess()
    fp.register(
        [
            "git",
            "branch",
            "-a",
            "--contains",
            "6d3bdaed89913b8b3ea6ca66f8fd2361cc0498dd",
        ],
        stdout="* main\nremotes/origin/HEAD -> origin/main\nremotes/origin/main",
    )
    result_validate_commit = git_process.validate_commit(
        branch="main", commit="6d3bdaed89913b8b3ea6ca66f8fd2361cc0498dd"
    )
    assert type(result_validate_commit) is str
    assert (
        result_validate_commit
        == "* main\nremotes/origin/HEAD -> origin/main\nremotes/origin/main"
    )

    fp.register(
        [
            "git",
            "branch",
            "-a",
            "--contains",
            "6d3bdaed89913b8b3ea6ca66f8fd2361cc0498d0",
        ],
        stderr="error: no such commit 6d3bdaed89913b8b3ea6ca66f8fd2361cc0498d0",
        returncode=129,
    )

    with pytest.raises(ProcessError):
        result_validate_commit = git_process.validate_commit(
            branch="main", commit="6d3bdaed89913b8b3ea6ca66f8fd2361cc0498d0"
        )

    fp.register(
        [
            "git",
            "branch",
            "-a",
            "--contains",
            "6d3bdaed89913b8b3ea6ca66f8fd2361cc0498dd",
        ],
        stdout="* main\nremotes/origin/HEAD -> origin/main\nremotes/origin/main",
    )

    with pytest.raises(ProcessError):
        result_validate_commit = git_process.validate_commit(
            branch="dev", commit="6d3bdaed89913b8b3ea6ca66f8fd2361cc0498dd"
        )

    fp.register(
        [
            "git",
            "branch",
            "-a",
            "--contains",
            "6d3bdaed89913b8b3ea6ca66f8fd2361cc0498dd",
        ],
        stdout="* main\nremotes/origin/HEAD -> origin/main\nremotes/origin/main",
    )

    with pytest.raises(ProcessError):
        result_validate_commit = git_process.validate_commit(
            branch="mai", commit="6d3bdaed89913b8b3ea6ca66f8fd2361cc0498dd"
        )


def test_git_process_log(fp):
    git_process = GitProcess()
    fp.register(
        [
            "git",
            "log",
            "-n",
            "4",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            "--raw",
            "--numstat",
            "-p",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "main",
        ],
        stdout=FAKE_LOG_OUTPUT,
    )

    result = git_process.log(rev="main", number=4)

    assert type(result) is str
    assert result == FAKE_LOG_OUTPUT


def test_git_process_ls_files(fp):
    git_process = GitProcess()
    fp.register(
        ["git", "ls-tree", "--name-only", "-r", "main"],
        stdout="usage/network.py\n"
        "usage/sql/all_original/dataset-org-proj-ts.sql\n"
        "usage/sql/all_original/dataset-org-proj-ts.sql-tpl\n"
        "usage/sql/all_original/dataset-organization-all.sql\n"
        "usage/sql/all_original/predict-org-proj-ts-commit.sql\n"
        "usage/sql/all_original/predict-org-proj-ts-commit.sql-tpl",
    )

    result = git_process.ls_files(rev="main")
    assert type(result) is str
    file_tree = result.splitlines()
    assert len(file_tree) == 6

    fp.register(
        ["git", "ls-tree", "--name-only", "-r", "dev"],
        stderr="fatal: Not a valid object name dev",
        returncode=128,
    )
    with pytest.raises(ProcessError):
        result = git_process.ls_files(rev="dev")
