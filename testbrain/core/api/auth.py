from requests.auth import AuthBase


class HTTPTokenAuth(AuthBase):
    """Attaches HTTP Token Authentication to the given Request object."""

    keyword = "Token"

    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return all([self.token == getattr(other, "token", None)])

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers["Authorization"] = f"{self.keyword} {self.token}"
        return r


class HTTPUserTokenAuth(HTTPTokenAuth):
    """Attaches HTTP Token Authentication to the given Request object."""

    keyword = "Token"


class HTTPCLIAuth(HTTPTokenAuth):
    """Attaches HTTP CLI Authentication to the given Request object."""

    keyword = "CLI"

    def __call__(self, r):
        r.headers["Authorization"] = f"{self.keyword} {self.token}"
        r.headers[self.keyword] = f"{self.token}"
        return r


class HTTPAPIAuth(HTTPTokenAuth):
    """Attaches HTTP Token Authentication to the given Request object."""

    keyword = "Token"

    def __call__(self, r):
        r.headers[self.keyword] = f"{self.token}"
        return r
