import logging

from requests.auth import AuthBase

logger = logging.getLogger(__name__)


class HTTPTokenAuth(AuthBase):
    """Attaches HTTP Token Authentication to the given Request object."""

    keyword: str = "Token"

    def __init__(self, token: str):
        self.token = token

    def __eq__(self, other):
        return all([self.token == getattr(other, "token", None)])

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers["Authorization"] = f"{self.keyword} {self.token}"
        return r

    def __str__(self):
        return f"{self.__class__.__name__}:{self.keyword}"


class HTTPUserTokenAuth(HTTPTokenAuth):
    """Attaches HTTP Token Authentication to the given Request object."""

    keyword: str = "Token"


class HTTPCLIAuth(HTTPTokenAuth):
    """Attaches HTTP CLI Authentication to the given Request object."""

    keyword: str = "CLI"

    def __call__(self, r):
        r.headers["Authorization"] = f"{self.keyword} {self.token}"
        r.headers[self.keyword] = f"{self.token}"
        return r


class HTTPAPIAuth(HTTPTokenAuth):
    """Attaches HTTP Token Authentication to the given Request object."""

    keyword: str = "Token"

    def __call__(self, r):
        r.headers[self.keyword] = f"{self.token}"
        return r
