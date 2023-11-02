import pathlib
from testbrain.repository.vcs.git import GitVCS


scm = GitVCS("/Users/whenessel/Development/PycharmProjects/appsurify-testbrain-cli")
print(scm.repo_dir)
print(scm.repo_name)
print(scm.current_branch)
print(scm.commits("composition", "HEAD", 2))
