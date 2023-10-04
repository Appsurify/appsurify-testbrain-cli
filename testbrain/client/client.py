import requests

from testbrain.client.adapter import TCPKeepAliveAdapter
from testbrain.client.auth import HTTPTokenAuth


class APIClient(object):
    user_agent: str = "TestbrainCLI/1.x"

    def __init__(self, endpoint: str, token: str):
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


class TestbrainClient(APIClient):

    def get_project_id(self, project_name: str) -> int:

        api_url = self.endpoint + "/api/ssh_v2/hook/fetch/"
        params = {"project_name": project_name}

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TestbrainCLI/1.x"
        }