import abc
import logging
import typing as t

import requests
from requests.adapters import BaseAdapter
from requests.auth import AuthBase
from urllib3.util import Retry
from testbrain.client import TCPKeepAliveAdapter, HTTPTokenAuth
from testbrain.client.utils import get_user_agent, from_camel_case

logger = logging.getLogger(__name__)

T_MAX_RETRIES = t.TypeVar("T_MAX_RETRIES", bound=t.Union[int, Retry])

DEFAULT_MAX_RETRIES: T_MAX_RETRIES = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods={"GET", "POST"},
    raise_on_status=False,
)

DEFAULT_TIMEOUT: float = 120.0

DEFAULT_HEADERS: t.Dict[str, t.Any] = {"Connection": "keep-alive"}


DEFAULT_USER_AGENT: t.Optional[str] = get_user_agent()


class HttpClient(abc.ABC):
    _session: t.Optional[requests.Session] = None
    _user_agent: t.Optional[str] = None
    __parent = None

    def __init__(self, *args, **kwargs):
        self._user_agent = get_user_agent(name=self.name, version=self.version)

    def __new__(cls, *args, **kwargs):
        new = object.__new__(cls)
        parent = None
        for klass in cls.__mro__:
            if klass == new.__class__:
                continue
            parent = object.__new__(klass)
            break

        if new.__parent is None:
            cls.__parent = parent
        return new

    @property
    def parent(self) -> t.Optional["HttpClient"]:
        return self.__parent

    @property
    def name(self) -> str:
        # return from_camel_case(self.__class__.__name__).capitalize()
        return self.__class__.__name__

    @property
    def version(self) -> str:
        try:
            from . import __version__
        except ImportError:
            __version__ = "unknown"
        return __version__

    @property
    def user_agent(self) -> str:
        if not self._user_agent:
            self._user_agent = DEFAULT_USER_AGENT
        return self._user_agent

    def get_session(
        self,
        auth: t.Optional[HTTPTokenAuth] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        max_retries: t.Optional[T_MAX_RETRIES] = None,
    ) -> requests.Session:
        if headers is None:
            headers = {}

        headers["user-agent"] = self.user_agent

        if isinstance(max_retries, int):
            DEFAULT_MAX_RETRIES.total = max_retries
            max_retries = DEFAULT_MAX_RETRIES

        if self._session is None:
            self._session = requests.Session()

        self._session.auth = auth
        self._session.headers = headers

        self._session.mount(
            "http://",
            TCPKeepAliveAdapter(idle=60, interval=20, count=5, max_retries=max_retries),
        )
        self._session.mount(
            "https://",
            TCPKeepAliveAdapter(idle=60, interval=20, count=5, max_retries=max_retries),
        )
        return self._session

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        auth: HTTPTokenAuth = kwargs.pop("auth", None)
        headers: t.Optional[dict] = kwargs.pop("headers", DEFAULT_HEADERS)
        max_retries: t.Optional[T_MAX_RETRIES] = kwargs.pop(
            "max_retries", DEFAULT_MAX_RETRIES
        )
        timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT)

        if isinstance(timeout, int) or isinstance(timeout, float):
            timeout = (timeout, timeout)

        session = self.get_session(auth=auth, headers=headers, max_retries=max_retries)
        response = session.request(method, url, timeout=timeout, **kwargs)

        return response

    def get(
        self, url: str, params: t.Optional[dict] = None, **kwargs
    ) -> requests.Response:
        response = self.request("GET", url, params=params, **kwargs)
        return response

    def post(
        self,
        url: str,
        data: t.Optional[dict] = None,
        json: t.Optional[dict] = None,
        **kwargs,
    ) -> requests.Response:
        response = self.request("POST", url, data=data, json=json, **kwargs)
        return response
