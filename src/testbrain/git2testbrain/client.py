import logging
from typing import Dict, Optional, Union
from urllib.parse import urljoin

import requests

from testbrain.core.api.auth import HTTPAPIAuth
from testbrain.core.api.client import APIClient

logger = logging.getLogger(__name__)


class Git2TestbrainAPIClient(APIClient):
    default_headers: Dict[str, str] = {
        "Connection": "keep-alive",
        "Content-Type": "application/json",
    }
    name = "git2testbrain"

    def __init__(self, server: str, token: str, **kwargs):
        self.base_url = server
        self.token = token
        self.auth = HTTPAPIAuth(token=token)
        super(Git2TestbrainAPIClient, self).__init__(**kwargs)
        logger.debug(
            f"Initialized Testbrain API client for: {server} ({'*' * len(token)})"
        )

    def request(self, method: str, url: str, **kwargs):
        return super(Git2TestbrainAPIClient, self).request(
            method, url, auth=self.auth, **kwargs
        )

    def get_project_id(self, name: str):
        endpoint = "/api/ssh_v2/hook/fetch/"
        params = {"project_name": name}
        try:
            response = self.get(url=urljoin(self.base_url, endpoint), params=params)
            return response
        except requests.exceptions.ConnectionError:
            logger.exception("Failed to connect to Testbrain server.", exc_info=False)
            ...

    def deliver_hook_payload(
        self,
        project_id: int,
        data: Union[dict, str],
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        endpoint = f"/api/ssh_v2/hook/{project_id}/"
        headers = self.default_headers
        headers.update({"X-Git-Event": "push"})
        response = self.post(
            url=urljoin(self.base_url, endpoint),
            data=data,
            headers=headers,
            timeout=timeout,
            max_retries=max_retries,
        )
        return response
