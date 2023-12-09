import abc
import logging
import typing as t

import requests
from requests.adapters import BaseAdapter
from requests.auth import AuthBase
from urllib3.util import Retry

from testbrain.contrib.client.adapters import TCPKeepAliveAdapter
from testbrain.contrib.client.auth import HTTPTokenAuth
from testbrain.contrib.client.utils import from_camel_case, get_user_agent

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

DEFAULT_HEADERS: t.Dict[t.AnyStr, t.Any] = {
    "Connection": "keep-alive",
    "Content-Type": "application/json",
}


DEFAULT_USER_AGENT: t.Optional[str] = get_user_agent()


class HttpClient(abc.ABC):
    _session: t.Optional[requests.Session] = None
    _user_agent: t.Optional[str] = None
    __parent = None

    def __init__(self, *args, **kwargs):
        logger.debug(f"Initial variables with {args} {kwargs}")
        self._user_agent = get_user_agent(name=self.name, version=self.version)

    def __new__(cls, *args, **kwargs):
        new = object.__new__(cls)
        parent = None
        if new.__parent is None and not isinstance(cls, HttpClient):
            parent = object.__new__(HttpClient)
        new.__parent = parent
        return new

    @property
    def parent(self) -> t.Optional["HttpClient"]:
        return self.__parent

    @property
    def name(self) -> str:
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
        logger.debug(f"Session configuring with: {str(auth)} {headers} {max_retries}")
        if headers is None:
            headers = {}

        headers["user-agent"] = self.user_agent
        headers.update(DEFAULT_HEADERS)

        if isinstance(max_retries, int):
            DEFAULT_MAX_RETRIES.total = max_retries
            max_retries = DEFAULT_MAX_RETRIES

        if self._session is None:
            self._session = requests.Session()

        self._session.auth = auth
        self._session.headers = headers

        logger.debug(
            "Session set up HTTP adapter with socket options "
            "(TCPKeepAlive: idle=60, interval=20, count=5)"
        )
        self._session.mount(
            "http://",
            TCPKeepAliveAdapter(idle=60, interval=20, count=5, max_retries=max_retries),
        )
        self._session.mount(
            "https://",
            TCPKeepAliveAdapter(idle=60, interval=20, count=5, max_retries=max_retries),
        )
        logger.debug("Session prepared")
        return self._session

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        logger.debug("Request configuring")
        auth: HTTPTokenAuth = kwargs.pop("auth", None)
        headers: t.Optional[dict] = kwargs.pop("headers", DEFAULT_HEADERS)
        max_retries: t.Optional[T_MAX_RETRIES] = kwargs.pop(
            "max_retries", DEFAULT_MAX_RETRIES
        )
        timeout = kwargs.pop("timeout", DEFAULT_TIMEOUT)

        if isinstance(timeout, int) or isinstance(timeout, float):
            timeout = (timeout, timeout)

        logger.debug("Request get connection session")
        session = self.get_session(auth=auth, headers=headers, max_retries=max_retries)
        logger.debug(f"Request settings: {timeout} {max_retries}")
        logger.debug(f"Request starting: [{method}] {url} {session.headers}")
        response = session.request(method, url, timeout=timeout, **kwargs)
        logger.debug(f"Request finished: [{response.status_code}] {response.content}")
        return response

    def get(
        self, url: str, params: t.Optional[dict] = None, **kwargs
    ) -> requests.Response:
        response = self.request("GET", url, params=params, **kwargs)
        return response

    def post(
        self,
        url: str,
        data: t.Optional[t.Union[dict, str, bytes]] = None,
        json: t.Optional[dict] = None,
        **kwargs,
    ) -> requests.Response:
        response = self.request("POST", url, data=data, json=json, **kwargs)
        return response
