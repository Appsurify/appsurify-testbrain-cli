import logging

from testbrain.client import HttpClient

logger = logging.getLogger(__name__)


class RepositoryClient(HttpClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def version(self) -> str:
        from . import __version__

        return __version__

    @property
    def user_agent(self) -> str:
        base = super().user_agent
        parent_part = self.parent.name + "/" + self.parent.version
        return f"{base} {parent_part}"
