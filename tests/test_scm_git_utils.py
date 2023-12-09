from contextlib import contextmanager

import pytest

from testbrain.contrib.scm.git import utils as git_utils
from testbrain.contrib.scm.git import patterns as git_patterns


def test_parse_commits():
    commit_raw = (
        "COMMIT:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n"
        "TREE:\ta2bd09a6cc8a36da7fd43a3b8445967584873e5e\n"
        "DATE:\t2023-09-29T16:13:45+03:00\n"
        "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
        "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com"
        "\t2023-09-29T16:13:45+03:00\n"
        "MESSAGE:\tMerge branch 'dev'\n"
        "PARENTS:\t27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210 "
        "0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd\n"
        "\n\n"
        "COMMIT:\t39c54991d3cd7f4bae68d6b58549e7e2ab084a23\n"
        "TREE:\t5c86012497523e000b3ddfd9a95967da58d77fe9\n"
        "DATE:\t2023-10-02T13:23:02+03:00\n"
        "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T13:23:02+03:00\n"
        "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com"
        "\t2023-10-02T13:23:02+03:00\n"
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
        "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com"
        "\t2023-10-02T13:44:07+03:00\n"
        "MESSAGE:\tCONTRIB rename\nPARENTS:\t"
        "39c54991d3cd7f4bae68d6b58549e7e2ab084a23\n\n"
        "0\t0\tCONTRIB.txt => CONTRIB.md"
        "\n\n"
        "diff --git a/CONTRIB.txt b/CONTRIB.md\n"
        "similarity index 100%\nrename from CONTRIB.txt\nrename to CONTRIB.md"
        "\n\n\n"
        "COMMIT:\t2c5ebc4c21b8db4917c9a30173e3f5307f8552f9\n"
        "TREE:\t60fc93ce6ab91eb56d3f3f06a3abb77b1e5b3e22\n"
        "DATE:\t2023-10-02T20:01:48+03:00\n"
        "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T20:01:48+03:00\n"
        "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com"
        "\t2023-10-02T20:01:48+03:00\n"
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
        "+# README\n+## New headline\n\\ No newline at end of file\n"
        "\n\n"
    )

    result = git_utils.parse_commits_from_text(text=commit_raw)

    assert len(result) == 4


def test_parse_single_commit():
    commit1_raw = (
        "COMMIT:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n"
        "TREE:\ta2bd09a6cc8a36da7fd43a3b8445967584873e5e\n"
        "DATE:\t2023-09-29T16:13:45+03:00\n"
        "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
        "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com"
        "\t2023-09-29T16:13:45+03:00\n"
        "MESSAGE:\tMerge branch 'dev'\n"
        "PARENTS:\t27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210 "
        "0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd\n"
        "\n\n"
    )
    commit2_raw = (
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
        "index 01ea8a03269d7d23931cd2a7aa8940b14f850257..7cb38a976dd950aef3eee5e8a63c334100d7044b 100644\n"
        "--- a/CONTRIB.txt\n+++ b/CONTRIB.txt\n"
        "@@ -1 +1 @@\n-Other\n+-- empty --\n\\ No newline at end of file\n"
        "diff --git a/README.md b/README.md\n"
        "new file mode 100644\n"
        "index 0000000000000000000000000000000000000000..52da238091fabcd84e921bb6029d9addf9afd02f\n"
        "--- /dev/null\n+++ b/README.md\n"
        "@@ -0,0 +1 @@\n+# README\n\\ No newline at end of file\n"
        "diff --git a/README.txt b/README.txt\n"
        "deleted file mode 100644\n"
        "index 8038dd2b0751f5c895754871bdc6daa400008c08..0000000000000000000000000000000000000000\n"
        "--- a/README.txt\n+++ /dev/null\n@@ -1 +0,0 @@\n-QA works\n\\ No newline at end of file\n"
        "\n\n"
    )

    for commit1_match in git_patterns.RE_COMMIT_LIST.finditer(commit1_raw):
        commit1 = git_utils.parse_single_commit(commit1_match)
        assert commit1 is not None
        assert commit1["sha"] == "5355a13f5ba44d23de9a3090ad976d63d1a60e3e"
        assert commit1["tree"] == "a2bd09a6cc8a36da7fd43a3b8445967584873e5e"
        assert commit1["date"] == "2023-09-29T16:13:45+03:00"
        assert commit1["author"] == {
            "name": "Artem Demidenko",
            "email": "ar.demidenko@gmail.com",
            "date": "2023-09-29T16:13:45+03:00",
        }
        assert commit1["parents"] == [
            {"sha": "27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210"},
            {"sha": "0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd"},
        ]

    for commit2_match in git_patterns.RE_COMMIT_LIST.finditer(commit2_raw):
        commit2 = git_utils.parse_single_commit(commit2_match)
        assert commit2 is not None
        assert commit2["sha"] == "39c54991d3cd7f4bae68d6b58549e7e2ab084a23"
        assert commit2["tree"] == "5c86012497523e000b3ddfd9a95967da58d77fe9"
        assert commit2["date"] == "2023-10-02T13:23:02+03:00"
        assert commit2["author"] == {
            "name": "Artem Demidenko",
            "email": "ar.demidenko@gmail.com",
            "date": "2023-10-02T13:23:02+03:00",
        }
        assert commit2["parents"] == [
            {"sha": "5355a13f5ba44d23de9a3090ad976d63d1a60e3e"}
        ]
        assert commit2["files"] == [
            {
                "filename": "CONTRIB.txt",
                "sha": "7cb38a976dd950aef3eee5e8a63c334100d7044b",
                "additions": 1,
                "insertions": 1,
                "deletions": 1,
                "changes": 2,
                "lines": 2,
                "status": "modified",
                "previous_filename": "",
                "patch": (
                    "@@ -1 +1 @@\n-Other\n+-- empty --\n\\ No newline at end of file\n"
                ),
                "blame": "",
            },
            {
                "filename": "README.md",
                "sha": "52da238091fabcd84e921bb6029d9addf9afd02f",
                "additions": 1,
                "insertions": 1,
                "deletions": 0,
                "changes": 1,
                "lines": 1,
                "status": "added",
                "previous_filename": "",
                "patch": "@@ -0,0 +1 @@\n+# README\n\\ No newline at end of file\n",
                "blame": "",
            },
            {
                "filename": "README.txt",
                "sha": "0000000000000000000000000000000000000000",
                "additions": 0,
                "insertions": 0,
                "deletions": 1,
                "changes": 1,
                "lines": 1,
                "status": "deleted",
                "previous_filename": "",
                "patch": "@@ -1 +0,0 @@\n-QA works\n\\ No newline at end of file\n",
                "blame": "",
            },
        ]
