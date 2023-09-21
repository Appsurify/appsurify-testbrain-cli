import time
from urllib.parse import urljoin

import click
import requests

from testbrain.client.adapter import TCPKeepAliveAdapter
from testbrain.client.auth import HTTPTokenAuth


class APIClient(object):
    user_agent = "Testbrain/2.x (Python 3.x) Requests/2.31.0 urllib3/2.0.4"

    def __init__(self, endpoint, token):
        self.endpoint = endpoint
        self.token = token

    def get_session(self):
        adapter = TCPKeepAliveAdapter()
        auth = HTTPTokenAuth(token=self.token)

        session = requests.Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.auth = auth

        session.headers.update({'User-Agent': self.user_agent})

        return session

    