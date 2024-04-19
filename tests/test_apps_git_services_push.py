import time
import random

from testbrain.cli.apps.repository.git.models import Commit
from testbrain.cli.apps.repository.git.services import PushService


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
)
FAKE_LOG_PARENT_OUTPUT = (
    "COMMIT:\t2c5ebc4c21b8db4917c9a30173e3f5307f8552f9\n"
    "TREE:\t60fc93ce6ab91eb56d3f3f06a3abb77b1e5b3e22\n"
    "DATE:\t2023-10-02T20:01:48+03:00\n"
    "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T20:01:48+03:00\n"
    "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T20:01:48+03:00\n"
    "MESSAGE:\tChanges\nPARENTS:\tceff1b9d2d403e83b9c7c39e5baa47eff61a3524"
    "\n\n"
)


def register_limits(fp):
    limit = 999999

    fp.register(["git", "config", "--global", "merge.renameLimit", str(limit)])
    fp.register(["git", "config", "--global", "diff.renameLimit", str(limit)])
    fp.register(["git", "config", "--global", "diff.renames", "0"])

    fp.register(["git", "config", "merge.renameLimit", str(limit)])
    fp.register(["git", "config", "diff.renameLimit", str(limit)])
    fp.register(["git", "config", "diff.renames", "0"])


def test_apps_git_service(fp):
    register_limits(fp)

    server = "https://demo.testbrain.cloud"
    token = "<TOKEN>"
    repo_dir = "."
    repo_name = None
    project = "appsurify-testbrain-cli"
    pr_mode = False

    service = PushService(
        server=server,
        token=token,
        repo_dir=repo_dir,
        repo_name=repo_name,
        project=project,
        pr_mode=pr_mode,
    )

    assert service is not None


def test_apps_git_service(fp):
    register_limits(fp)

    server = "https://demo.testbrain.cloud"
    token = "<TOKEN>"
    repo_dir = "."
    repo_name = None
    project = "appsurify-testbrain-cli"
    pr_mode = False

    service = PushService(
        server=server,
        token=token,
        repo_dir=repo_dir,
        repo_name=repo_name,
        project=project,
        pr_mode=pr_mode,
    )

    assert service is not None

    fp.register(
        ["git", "branch", "--show-current"],
        stdout="main",
    )

    branch = service.validate_branch(branch="main")

    assert branch == "fake-main"

    fp.register(
        [
            "git",
            "log",
            "-n",
            "2",
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
            "5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        ],
        stdout=FAKE_LOG_OUTPUT,
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "1",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210",
        ],
        stdout=FAKE_LOG_PARENT_OUTPUT,
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "1",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd",
        ],
        stdout=FAKE_LOG_PARENT_OUTPUT,
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "1",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        ],
        stdout=FAKE_LOG_PARENT_OUTPUT,
    )

    kwargs = {
        "raw": True,
        "patch": True,
        "blame": False,  # not minimize,
    }

    commits = service.get_commits(
        commit="5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        number=2,
        **kwargs,
    )

    assert len(commits) == 2


def test_apps_git_service_get_commits(fp):
    register_limits(fp)

    server = "https://demo.testbrain.cloud"
    token = "<TOKEN>"
    repo_dir = "."
    repo_name = None
    project = "appsurify-testbrain-cli"
    pr_mode = False

    service = PushService(
        server=server,
        token=token,
        repo_dir=repo_dir,
        repo_name=repo_name,
        project=project,
        pr_mode=pr_mode,
    )

    fp.register(
        ["git", "branch", "--show-current"],
        stdout="main",
    )

    fp.register(
        [
            "git",
            "log",
            "-n",
            "2",
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
            "5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        ],
        stdout=FAKE_LOG_OUTPUT,
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "1",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210",
        ],
        stdout=FAKE_LOG_PARENT_OUTPUT,
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "1",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd",
        ],
        stdout=FAKE_LOG_PARENT_OUTPUT,
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "1",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        ],
        stdout=FAKE_LOG_PARENT_OUTPUT,
    )

    kwargs = {
        "raw": True,
        "patch": True,
        "blame": False,  # not minimize,
    }

    commits = service.get_commits(
        commit="5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        number=2,
        **kwargs,
    )

    assert len(commits) == 2


def test_apps_git_service_get_file_tree(fp):
    register_limits(fp)

    server = "https://demo.testbrain.cloud"
    token = "<TOKEN>"
    repo_dir = "."
    repo_name = None
    project = "appsurify-testbrain-cli"
    pr_mode = False

    service = PushService(
        server=server,
        token=token,
        repo_dir=repo_dir,
        repo_name=repo_name,
        project=project,
        pr_mode=pr_mode,
    )

    fp.register(
        ["git", "branch", "--show-current"],
        stdout="main",
    )

    fp.register(
        ["git", "ls-tree", "--name-only", "-r", "main"],
        stdout="usage/network.py\n"
        "usage/sql/all_original/dataset-org-proj-ts.sql\n"
        "usage/sql/all_original/dataset-org-proj-ts.sql-tpl\n"
        "usage/sql/all_original/dataset-organization-all.sql\n"
        "usage/sql/all_original/predict-org-proj-ts-commit.sql\n"
        "usage/sql/all_original/predict-org-proj-ts-commit.sql-tpl",
    )

    file_tree = service.get_file_tree(
        branch="main" if not pr_mode else "5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        minimize=False,
    )

    assert len(file_tree) == 6


def test_apps_git_service_make_payload(fp):
    register_limits(fp)

    server = "https://demo.testbrain.cloud"
    token = "<TOKEN>"
    repo_dir = "."
    repo_name = None
    project = "appsurify-testbrain-cli"
    pr_mode = False

    service = PushService(
        server=server,
        token=token,
        repo_dir=repo_dir,
        repo_name=repo_name,
        project=project,
        pr_mode=pr_mode,
    )

    fp.register(
        ["git", "branch", "--show-current"],
        stdout="main",
    )
    fp.register(
        ["git", "config", "--get", "remote.origin.url"],
        stdout="https://github.com/Appsurify/appsurify-testbrain-cli.git",
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "2",
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
            "5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        ],
        stdout=FAKE_LOG_OUTPUT,
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "1",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210",
        ],
        stdout=FAKE_LOG_PARENT_OUTPUT,
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "1",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd",
        ],
        stdout=FAKE_LOG_PARENT_OUTPUT,
    )
    fp.register(
        [
            "git",
            "log",
            "-n",
            "1",
            "--abbrev=40",
            "--full-diff",
            "--full-index",
            "--reverse",
            '--pretty=format:"%n'
            "COMMIT:%x09%H%n"
            "TREE:%x09%T%n"
            "DATE:%x09%aI%n"
            "AUTHOR:%x09%an%x09%ae%x09%aI%n"
            "COMMITTER:%x09%cn%x09%ce%x09%cI%n"
            'MESSAGE:%x09%s%nPARENTS:%x09%P%n"',
            "5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        ],
        stdout=FAKE_LOG_PARENT_OUTPUT,
    )

    kwargs = {
        "raw": True,
        "patch": True,
        "blame": False,  # not minimize,
    }

    commits = service.get_commits(
        commit="5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        number=2,
        **kwargs,
    )

    assert len(commits) == 2

    fp.register(
        ["git", "ls-tree", "--name-only", "-r", "main"],
        stdout="usage/network.py\n"
        "usage/sql/all_original/dataset-org-proj-ts.sql\n"
        "usage/sql/all_original/dataset-org-proj-ts.sql-tpl\n"
        "usage/sql/all_original/dataset-organization-all.sql\n"
        "usage/sql/all_original/predict-org-proj-ts-commit.sql\n"
        "usage/sql/all_original/predict-org-proj-ts-commit.sql-tpl",
    )

    file_tree = service.get_file_tree(
        branch="main" if not pr_mode else "5355a13f5ba44d23de9a3090ad976d63d1a60e3e",
        minimize=False,
    )

    assert len(file_tree) == 6

    payload = service.make_changes_payload(
        branch="main", commits=commits, file_tree=file_tree
    )

    assert len(payload.file_tree) == 6
    assert len(payload.commits) == 2
