import typing as t

import pytest

from testbrain.contrib.scm.base import AbstractVCS


def test_custom_vcs_class():
    class CustomVCS(AbstractVCS):
        ...

    with pytest.raises(TypeError):
        vcs = CustomVCS()

    class NewCustomVCS(AbstractVCS):
        def checkout(
            self,
            branch: str,
            commit: str,
            detach: t.Optional[bool] = False,
            remote: t.Optional[bool] = False,
        ) -> bool:
            ...

        def commits(
            self,
            commit: str = "HEAD",
            number: int = 1,
            reverse: t.Optional[bool] = True,
            numstat: t.Optional[bool] = True,
            raw: t.Optional[bool] = True,
            patch: t.Optional[bool] = True,
        ) -> t.List[t.Dict]:
            ...

        def fetch(self, branch: t.Optional[str] = None) -> bool:
            ...

        def file_tree(self, branch: t.Optional[str] = None) -> t.Optional[t.List[str]]:
            ...

        def get_branch(self, branch_name: str) -> str:
            ...

        def get_current_branch(self) -> str:
            ...

        def process(self):
            ...

        def validate_commit(self, branch: str, commit: str) -> bool:
            ...

        def _get_repo_name(self) -> str:
            ...

    vcs = NewCustomVCS()

    assert isinstance(vcs, AbstractVCS)
