import logging
import typing as t
from urllib.parse import urljoin

import requests

from testbrain.client import HTTPAPIAuth, HttpClient

logger = logging.getLogger(__name__)


class RepositoryClient(HttpClient):
    def __init__(self, server: str, token: str, **kwargs):
        self.base_url = server
        self.token = token
        self.auth = HTTPAPIAuth(token=token)
        super().__init__(**kwargs)
        logger.debug(
            f"Initialized Testbrain API client for: {server} ({'*' * len(token)})"
        )

    @property
    def version(self) -> str:
        from . import __version__

        return __version__

    @property
    def user_agent(self) -> str:
        base = super().user_agent
        parent_part = self.parent.name + "/" + self.parent.version
        return f"{base} {parent_part}"

    def request(self, method: str, url: str, **kwargs):
        return super().request(method, url, auth=self.auth, **kwargs)

    def get_project_id(self, name: str):
        endpoint = "/api/ssh_v2/hook/fetch/"
        params = {"project_name": name}
        try:
            response = self.get(url=urljoin(self.base_url, endpoint), params=params)
            return response
        except requests.exceptions.ConnectionError:
            logger.exception("Failed to connect to Testbrain server.", exc_info=False)
            ...

    def send_changes_payload(
        self,
        project_id: int,
        data: t.Union[dict, str, bytes],
        timeout: t.Optional[int] = None,
        max_retries: t.Optional[int] = None,
    ):
        endpoint = f"/api/ssh_v2/hook/{project_id}/"

        headers = {"X-Git-Event": "push"}

        response = self.post(
            url=urljoin(self.base_url, endpoint),
            data=data,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
        )
        return response