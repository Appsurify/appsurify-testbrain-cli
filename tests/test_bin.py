import pytest
from click.testing import CliRunner
from testbrain.bin.git2testbrain import cli as git2testbrain
from testbrain import __version__


class TestGit2TestbrainBin:
    def test_show_version(self):
        runner = CliRunner()
        result = runner.invoke(git2testbrain, ["--version"])
        assert result.exit_code == 0
        assert f"Appsurify-testbrain-cli ({__version__})" in result.output

    def test_show_help(self):
        runner = CliRunner()
        result = runner.invoke(git2testbrain, ["--help"])
        assert result.exit_code == 0
        assert (
            "  -h, --help                      Show this message and exit."
            in result.output
        )


#     def test_send_hook_simple(self, fp, tmp_path):
#         tmppath = tmp_path.mkdir(777, "demoRepo", exist_ok=True)
#
#         fp.register(
#             "git config --get remote.origin.url",
#             stdout=["https://github.com/Appsurify/appsurify-testbrain-cli.git"],
#         )
#         fp.register(
#             "git log -p -M --abbrev=40 --first-parent --full-diff "
#             "--full-index -n 4 --remotes master --reverse --numstat "
#             "--pretty=format:'%nCOMMIT:\t%H%nTREE:\t%T%nDATE:\t%aI%nAUTHOR:\t%an\t%ae\t%aI%nCOMMITTER:\t%cn\t%ce\t%cI%nMESSAGE:\t%s%nPARENTS:\t%P%n' "
#             "HEAD",
#             stdout=[
#                 (
#                     "COMMIT:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n"
#                     "TREE:\ta2bd09a6cc8a36da7fd43a3b8445967584873e5e\n"
#                     "DATE:\t2023-09-29T16:13:45+03:00\n"
#                     "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
#                     "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-09-29T16:13:45+03:00\n"
#                     "MESSAGE:\tMerge branch 'dev'\n"
#                     "PARENTS:\t27d9aaff69ac8db9d19918c4d5efb6b3ed2c3210 0cd26c4deaebd98ff26b8cf20bda15553ef5bdcd\n"
#                     "\n\n"
#                     "COMMIT:\t39c54991d3cd7f4bae68d6b58549e7e2ab084a23\n"
#                     "TREE:\t5c86012497523e000b3ddfd9a95967da58d77fe9\n"
#                     "DATE:\t2023-10-02T13:23:02+03:00\n"
#                     "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T13:23:02+03:00\n"
#                     "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T13:23:02+03:00\n"
#                     "MESSAGE:\tRenamed files\n"
#                     "PARENTS:\t5355a13f5ba44d23de9a3090ad976d63d1a60e3e\n\n"
#                     "1\t1\tCONTRIB.txt\n"
#                     "1\t0\tREADME.md\n"
#                     "0\t1\tREADME.txt"
#                     "\n\n"
#                     "diff --git a/CONTRIB.txt b/CONTRIB.txt\n"
#                     "index 01ea8a03269d7d23931cd2a7aa8940b14f850257..7cb38a976dd950aef3eee5e8a63c334100d7044b 100644\n"
#                     "--- a/CONTRIB.txt\n+++ b/CONTRIB.txt\n"
#                     "@@ -1 +1 @@\n-Other\n+-- empty --\n\\ No newline at end of file\n"
#                     "diff --git a/README.md b/README.md\n"
#                     "new file mode 100644\n"
#                     "index 0000000000000000000000000000000000000000..52da238091fabcd84e921bb6029d9addf9afd02f\n"
#                     "--- /dev/null\n+++ b/README.md\n"
#                     "@@ -0,0 +1 @@\n+# README\n\\ No newline at end of file\n"
#                     "diff --git a/README.txt b/README.txt\n"
#                     "deleted file mode 100644\n"
#                     "index 8038dd2b0751f5c895754871bdc6daa400008c08..0000000000000000000000000000000000000000\n"
#                     "--- a/README.txt\n+++ /dev/null\n@@ -1 +0,0 @@\n-QA works\n\\ No newline at end of file\n"
#                     "\n\n"
#                     "COMMIT:\tceff1b9d2d403e83b9c7c39e5baa47eff61a3524\n"
#                     "TREE:\tb6f23611cb888a619940c71582de2dad6e04cd42\n"
#                     "DATE:\t2023-10-02T13:44:07+03:00\n"
#                     "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T13:44:07+03:00\n"
#                     "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T13:44:07+03:00\n"
#                     "MESSAGE:\tCONTRIB rename\nPARENTS:\t39c54991d3cd7f4bae68d6b58549e7e2ab084a23\n\n"
#                     "0\t0\tCONTRIB.txt => CONTRIB.md"
#                     "\n\n"
#                     "diff --git a/CONTRIB.txt b/CONTRIB.md\n"
#                     "similarity index 100%\nrename from CONTRIB.txt\nrename to CONTRIB.md"
#                     "\n\n\n"
#                     "COMMIT:\t2c5ebc4c21b8db4917c9a30173e3f5307f8552f9\n"
#                     "TREE:\t60fc93ce6ab91eb56d3f3f06a3abb77b1e5b3e22\n"
#                     "DATE:\t2023-10-02T20:01:48+03:00\n"
#                     "AUTHOR:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T20:01:48+03:00\n"
#                     "COMMITTER:\tArtem Demidenko\tar.demidenko@gmail.com\t2023-10-02T20:01:48+03:00\n"
#                     "MESSAGE:\tChanges\nPARENTS:\tceff1b9d2d403e83b9c7c39e5baa47eff61a3524"
#                     "\n\n"
#                     "2\t1\tCONTRIB.md\n"
#                     "2\t1\tREADME.md"
#                     "\n\n"
#                     "diff --git a/CONTRIB.md b/CONTRIB.md\n"
#                     "index 7cb38a976dd950aef3eee5e8a63c334100d7044b..7b2014660cadcd1abd84890b72177c7a35402b11 100644\n"
#                     "--- a/CONTRIB.md\n+++ b/CONTRIB.md\n"
#                     "@@ -1 +1,2 @@\n--- empty --\n\\ No newline at end of file\n"
#                     "+-- empty --\n+Another one\n\\ No newline at end of file\n"
#                     "diff --git a/README.md b/README.md\n"
#                     "index 52da238091fabcd84e921bb6029d9addf9afd02f..78f497a48b0b909b166245a15c8d8e8ccacc9914 100644\n"
#                     "--- a/README.md\n+++ b/README.md\n"
#                     "@@ -1 +1,2 @@\n-# README\n\\ No newline at end of file\n"
#                     "+# README\n+## New headline\n\\ No newline at end of file"
#                 )
#             ],
#         )
#
#         result = runner.invoke(
#             app,
#             [
#                 # "push",
#                 "--server",
#                 "https://demo.testbrain.cloud",
#                 "--token",
#                 "<TOKEN>",
#                 "--project",
#                 "test",
#                 "--repo-dir",
#                 tmppath,
#                 "--repo-name",
#                 "test",
#                 "--number",
#                 "4",
#                 "--branch",
#                 "master",
#                 "--start",
#                 "latest",
#             ],
#         )
#
#         assert result.exit_code == 0
