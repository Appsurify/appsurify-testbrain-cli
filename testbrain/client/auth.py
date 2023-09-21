from requests.auth import AuthBase


class HTTPTokenAuth(AuthBase):
    """Attaches HTTP Token Authentication to the given Request object."""
    keyword = 'Token'

    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return all([self.token == getattr(other, 'token', None)])

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers[self.keyword] = self.token
        return r
