from typing import Optional, Union, List, Dict, Any, TypeVar

import abc
import requests
from requests.adapters import BaseAdapter
from urllib3.util import Retry
from testbrain.client.adapter import TCPKeepAliveAdapter
from testbrain.client.auth import AuthBase, HTTPAPIAuth
from testbrain.client.utils import default_headers


T_TIMEOUT = TypeVar(
    "T_TIMEOUT", bound=Union[Union[float, int], List[Union[float, int]]]
)

T_MAX_RETRIES = TypeVar("T_MAX_RETRIES", bound=Union[int, Retry])


class APIClient(abc.ABC):
    default_adapter: BaseAdapter = TCPKeepAliveAdapter
    default_headers: Dict[str, str] = default_headers()
    default_timeout: T_TIMEOUT = (30.0, 120.0)
    default_max_retries: T_MAX_RETRIES = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods={"GET", "POST"},
        raise_on_status=False,
    )

    def __init__(self, *args, **kwargs):
        ...

    def get_session(
        self,
        max_retries: T_MAX_RETRIES,
        auth: Optional[AuthBase] = None,
        **kwargs,
    ) -> requests.Session:
        session = requests.Session()
        session.auth = auth

        if isinstance(max_retries, int):
            self.default_max_retries.total = max_retries

        adapter = self.default_adapter(
            idle=60, interval=20, count=5, max_retries=max_retries
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", self.default_headers)
        timeout = kwargs.pop("timeout", self.default_timeout)
        auth = kwargs.pop("auth", None)
        max_retries = kwargs.pop("max_retries", self.default_max_retries)
        session = self.get_session(max_retries=max_retries, auth=auth, **kwargs)
        return session.request(method, url, headers=headers, timeout=timeout, **kwargs)

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
