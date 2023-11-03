import pathlib

from testbrain.repository.services import PushService
from testbrain.repository.vcs.git import GitVCS

scm = GitVCS("/Users/whenessel/Development/PycharmProjects/appsurify-testbrain-cli")
print(scm.repo_dir)
print(scm.repo_name)
print(scm.current_branch)
print(scm.commits("composition", "HEAD", 2))
print(scm.file_tree())
print(scm.branches())


service = PushService(
    server="https://demo.appsurify.com",
    token="MTU6ZW9FZUxhcXpMZU9CdGZZVmZ4U3BFM3g5MmhVcDl5ZmQzampUWEM1SWRfNA",
    project="001TESTPROJECT",
    repo_dir="/Users/whenessel/Development/PycharmProjects/appsurify-testbrain-cli",
)

p = service.fetch_changes_payload(branch="development", commit="HEAD", number=2)
print(p)
r = service.send_changes_payload(payload=p)
print(r)
