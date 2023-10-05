import pytest
from unittest.mock import MagicMock, patch

from requests_mock.mocker import Mocker
from urllib.parse import urljoin
from testbrain.client import APIClient, TestbrainAPIClient
from testbrain.client.auth import HTTPAPIAuth
from testbrain.client.utils import default_user_agent
from testbrain.repository.git.models import *
from testbrain.repository.git.utils import *
from testbrain.repository.git.types import *
from testbrain.repository.git.cmd import *
from testbrain.repository.git import Git
from testbrain.repository.git.client import Git2TestbrainClient


class TestRepositoryModel:
    def test_person_parse(self) -> None:
        name = "Artem Demidenko"
        email = "ar.demidenko@gmail.com"
        date = "2023-09-29T12:36:37+03:00"
        person_string = f"{name}\t{email}\t{date}"
        person = parse_person_from_text(person_string)
        assert person.name == name

    def test_commit_parse(self) -> None:
        commit_data = (
            "COMMIT:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n"
            "TREE:\ta2bd09a6cc8a36da7fd43a3b8445967584873e5e\n"
            "DATE:\t2023-09-29T16:13:45+03:00\n"
            "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
            "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
            "MESSAGE:\tMerge branch 'dev'\n"
            "PARENTS:\t27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210 0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd"
        )
        commit_re_match = RE_COMMIT_LIST.finditer(commit_data)
        commit_re_dict = list(commit_re_match)
        commit = parse_single_commit(commit_re_dict[0])
        assert commit.sha == "5355a13f5ba44d23de9a3090ad976d63d1a60e3e"
        assert commit.parents == [
            Commit(sha="27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210"),
            Commit(sha="0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd"),
        ]

    def test_commits_parse(self) -> None:
        commit_data = (
            "COMMIT:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n"
            "TREE:\ta2bd09a6cc8a36da7fd43a3b8445967584873e5e\n"
            "DATE:\t2023-09-29T16:13:45+03:00\n"
            "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
            "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
            "MESSAGE:\tMerge branch 'dev'\n"
            "PARENTS:\t27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210 0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd\n"
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
            "index 7cb38a976dd950aef3eee5e8a63c334100d7044b..7b2014660cadcd1abd84890b72177c7a35402b11 100644\n"
            "--- a/CONTRIB.md\n+++ b/CONTRIB.md\n"
            "@@ -1 +1,2 @@\n--- empty --\n\\ No newline at end of file\n"
            "+-- empty --\n+Another one\n\\ No newline at end of file\n"
            "diff --git a/README.md b/README.md\n"
            "index 52da238091fabcd84e921bb6029d9addf9afd02f..78f497a48b0b909b166245a15c8d8e8ccacc9914 100644\n"
            "--- a/README.md\n+++ b/README.md\n"
            "@@ -1 +1,2 @@\n-# README\n\\ No newline at end of file\n"
            "+# README\n+## New headline\n\\ No newline at end of file"
        )
        commit_list = parse_commits_from_text(commit_data)
        assert len(commit_list) == 4


class TestRepositoryGitCmd:
    def test_git_cmd_get_branch(self, fp):
        fp.register("git branch --show-current", stdout=["master"])
        cmd = GitCmd()
        branch = cmd.execute_branches(show_current=True)
        assert branch == "master"

    def test_git_cmd_log(self, fp):
        fp.register(
            "git log -p -M --abbrev=40 --first-parent --full-diff "
            "--full-index -n 4 --remotes master --reverse --numstat "
            "--pretty=format:'%nCOMMIT:\t%H%nTREE:\t%T%nDATE:\t%aI%nAUTHOR:\t%an\t%ae\t%aI%nCOMMITTER:\t%cn\t%ce\t%cI%nMESSAGE:\t%s%nPARENTS:\t%P%n' "
            "HEAD",
            stdout=[
                (
                    "COMMIT:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n"
                    "TREE:\ta2bd09a6cc8a36da7fd43a3b8445967584873e5e\n"
                    "DATE:\t2023-09-29T16:13:45+03:00\n"
                    "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
                    "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
                    "MESSAGE:\tMerge branch 'dev'\n"
                    "PARENTS:\t27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210 0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd\n"
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
                    "index 7cb38a976dd950aef3eee5e8a63c334100d7044b..7b2014660cadcd1abd84890b72177c7a35402b11 100644\n"
                    "--- a/CONTRIB.md\n+++ b/CONTRIB.md\n"
                    "@@ -1 +1,2 @@\n--- empty --\n\\ No newline at end of file\n"
                    "+-- empty --\n+Another one\n\\ No newline at end of file\n"
                    "diff --git a/README.md b/README.md\n"
                    "index 52da238091fabcd84e921bb6029d9addf9afd02f..78f497a48b0b909b166245a15c8d8e8ccacc9914 100644\n"
                    "--- a/README.md\n+++ b/README.md\n"
                    "@@ -1 +1,2 @@\n-# README\n\\ No newline at end of file\n"
                    "+# README\n+## New headline\n\\ No newline at end of file"
                )
            ],
        )

        cmd = GitCmd()
        branch: T_Branch = "master"
        commits_data = cmd.execute_log(branch=branch, start="HEAD", number=4)

        assert len(commits_data) == 2899


class TestRepositoryGit:
    def test_git_repo_name_defined(self, fp):
        fp.register("git config --get remote.origin.url", stdout=["../../Git/demoRepo"])
        git = Git(repo_name="demoRepo")
        repo_name = git.repo_name
        assert repo_name == "demoRepo"

    def test_git_repo_name_options(self, fp):
        fp.register("git config --get remote.origin.url", stdout=["../../Git/demoRepo"])

        git = Git("../../Git/demoRepo")
        repo_name = git.repo_name
        assert repo_name == "demoRepo"

        fp.register("git config --get remote.origin.url", stdout=["C:/Git/demo Repo"])
        git = Git("./Git/demo Repo")
        repo_name = git.repo_name
        assert repo_name == "demo Repo"

        fp.register(
            "git config --get remote.origin.url",
            stdout=["https://github.com/Appsurify/appsurify-testbrain-cli.git"],
        )
        git = Git(".")
        repo_name = git.repo_name
        assert repo_name == "appsurify-testbrain-cli"

    def test_git_get_current_branch(self, fp):
        fp.register("git branch --show-current", stdout=["master"])
        fp.register(
            "git config --get remote.origin.url",
            stdout=["https://github.com/Appsurify/appsurify-testbrain-cli.git"],
        )
        git = Git()
        current_branch = git._get_current_branch()

        assert current_branch == "master"

    def test_git_get_commits(self, fp):
        fp.register(
            "git config --get remote.origin.url",
            stdout=["https://github.com/Appsurify/appsurify-testbrain-cli.git"],
        )
        fp.register(
            "git log -p -M --abbrev=40 --first-parent --full-diff "
            "--full-index -n 4 --remotes master --reverse --numstat "
            "--pretty=format:'%nCOMMIT:\t%H%nTREE:\t%T%nDATE:\t%aI%nAUTHOR:\t%an\t%ae\t%aI%nCOMMITTER:\t%cn\t%ce\t%cI%nMESSAGE:\t%s%nPARENTS:\t%P%n' "
            "HEAD",
            stdout=[
                (
                    "COMMIT:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n"
                    "TREE:\ta2bd09a6cc8a36da7fd43a3b8445967584873e5e\n"
                    "DATE:\t2023-09-29T16:13:45+03:00\n"
                    "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
                    "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
                    "MESSAGE:\tMerge branch 'dev'\n"
                    "PARENTS:\t27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210 0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd\n"
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
                    "index 7cb38a976dd950aef3eee5e8a63c334100d7044b..7b2014660cadcd1abd84890b72177c7a35402b11 100644\n"
                    "--- a/CONTRIB.md\n+++ b/CONTRIB.md\n"
                    "@@ -1 +1,2 @@\n--- empty --\n\\ No newline at end of file\n"
                    "+-- empty --\n+Another one\n\\ No newline at end of file\n"
                    "diff --git a/README.md b/README.md\n"
                    "index 52da238091fabcd84e921bb6029d9addf9afd02f..78f497a48b0b909b166245a15c8d8e8ccacc9914 100644\n"
                    "--- a/README.md\n+++ b/README.md\n"
                    "@@ -1 +1,2 @@\n-# README\n\\ No newline at end of file\n"
                    "+# README\n+## New headline\n\\ No newline at end of file"
                )
            ],
        )

        git = Git()
        branch: T_Branch = "master"
        commits = git._get_commits(branch=branch, start="HEAD", number=4)

        assert len(commits) == 4
        assert isinstance(commits[0], Commit)


class TestRepositoryClient:
    def test_g2t_client(self, requests_mock):
        requests_mock.get(
            "https://demo.testbrain.cloud/api/ssh_v2/hook/fetch/",
            json={"project_id": "1"},
            status_code=200,
        )
        api_client = Git2TestbrainClient(
            server="https://demo.testbrain.cloud", token="<TOKEN>"
        )

        api_response = api_client.get_project_id(name="test")
        assert api_response == 1

    def test_g2t_client(self, requests_mock):
        with pytest.raises(Exception) as exc_info:
            requests_mock.get(
                "https://demo.testbrain.cloud/api/ssh_v2/hook/fetch/",
                json={},
                status_code=404,
            )
            api_client = Git2TestbrainClient(
                server="https://demo.testbrain.cloud/", token="<TOKEN>"
            )

            api_response = api_client.get_project_id(name="test")
            raise Exception("project_id")
        assert exc_info.value.args[0] == "project_id"
