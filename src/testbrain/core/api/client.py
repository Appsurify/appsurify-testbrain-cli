import abc
import logging
from typing import Dict, List, Optional, TypeVar, Union

import requests
from requests.adapters import BaseAdapter
from urllib3.util import Retry

from testbrain import __build__, __name__, __version__
from testbrain.core import platform
from testbrain.core.api.adapter import TCPKeepAliveAdapter
from testbrain.core.api.auth import AuthBase

logger = logging.getLogger(__name__)


T_TIMEOUT = TypeVar(
    "T_TIMEOUT", bound=Union[Union[float, int], List[Union[float, int]]]
)

T_MAX_RETRIES = TypeVar("T_MAX_RETRIES", bound=Union[int, Retry])


class APIClient(abc.ABC):
    default_adapter: BaseAdapter = TCPKeepAliveAdapter
    default_headers: Dict[str, str] = {"Connection": "keep-alive"}
    default_timeout: T_TIMEOUT = (30.0, 120.0)
    default_max_retries: T_MAX_RETRIES = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods={"GET", "POST"},
        raise_on_status=False,
    )

    @property
    @abc.abstractmethod
    def name(self) -> str:
        return self.__class__.__name__

    def __init__(self, *args, **kwargs):
        ...

    def get_user_agent(self) -> str:
        client_name = self.name or self.__class__.__name__
        app_name = __name__
        app_version = __version__
        app_build = __build__
        ua = (
            f"{client_name}/{app_version} ({platform.SYSTEM}/{platform.RELEASE}; "
            f"{platform.PY_IMPLEMENTATION}/{platform.PY_VERSION}; {platform.MACHINE}) "
            f"Build/{app_build} (included: {app_name}/{app_version})"
        )
        return ua

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

        session.mount("api://", adapter)
        session.mount("https://", adapter)

        session.headers["user-agent"] = self.get_user_agent()
        return session

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        headers = kwargs.pop("headers", self.default_headers)
        headers["user-agent"] = self.get_user_agent()

        auth = kwargs.pop("auth", None)
        timeout = kwargs.pop("timeout", self.default_timeout)
        max_retries = kwargs.pop("max_retries", self.default_max_retries)

        session = self.get_session(max_retries=max_retries, auth=auth, **kwargs)

        logger.debug(f"Requesting {method} {url} {session.headers}")
        response = session.request(
            method, url, headers=headers, timeout=timeout, **kwargs
        )
        logger.debug(f"Response {response.status_code} {response.content}")
        return response

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
