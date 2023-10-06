from typing import Optional

import abc
import requests
from urllib.parse import urljoin
from testbrain.client.adapter import TCPKeepAliveAdapter
from testbrain.client.auth import AuthBase, HTTPAPIAuth
from testbrain.client.utils import default_headers


class APIClient(abc.ABC):
    default_adapter = TCPKeepAliveAdapter(idle=60, interval=20, count=5)
    default_headers = default_headers()

    def __init__(self, *args, **kwargs):
        self.session = requests.Session()

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", self.default_headers)
        auth = kwargs.pop("auth", None)
        self.session.auth = auth
        self.session.mount("http://", self.default_adapter)
        self.session.mount("https://", self.default_adapter)
        return self.session.request(method, url, headers=headers, **kwargs)

    def get(
        self, url: str, params: Optional[dict] = None, **kwargs
    ) -> requests.Response:
        req = self.request("get", url, params=params, **kwargs)
        return req

    def post(
        self, url: str, data: Optional[dict] = None, **kwargs
    ) -> requests.Response:
        req = self.request("post", url, data=data, **kwargs)
        return req


class TestbrainAPIClient(APIClient):
    def __init__(self, server: str, token: str, **kwargs):
        self.base_url = server
        self.token = token
        self.auth = HTTPAPIAuth(token=token)
        super(TestbrainAPIClient, self).__init__(**kwargs)

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        return super(TestbrainAPIClient, self).request(
            method, url, auth=self.auth, **kwargs
        )
