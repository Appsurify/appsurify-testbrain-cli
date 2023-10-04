from typing import Any

import pytest
from requests_mock.mocker import Mocker

from testbrain.client import APIClient


class APIClientException(BaseException):
    def __init__(self, endpoint: str, status_code: str, content: str):
        ...


class APIException(BaseException):
    def __init__(self, endpoint: str, status_code: str, content: str):
        ...


class TestbrainAPIClient(APIClient):
    def get_project_id(self, name: str) -> int:
        endpoint = "/api/ssh_v2/hook/fetch/"
        params = {"project": name}
        resp = self.get(url=endpoint, params=params)
        # if resp.status_code == 200:
        json_data = resp.json()
        project_id = json_data["project_id"]
        return project_id

    def push_commits(self, project_id: int, data: dict) -> Any:
        endpoint = f"/api/ssh_v2/hook/{project_id}/"
        data = {}
        resp = self.post(url=endpoint, data=data)
        # if resp.status_code == 200:
        json_data = resp.json()
        return None

@Mocker()
class TestClient:
    def test_get_project_id(self, mocker: Mocker):
        tb_client = TestbrainClient(schema, host, port, token)
        project_id = tb_client.get_project_id(name="Test Project")

        assert project_id == 1

    def test_push_commits(self):
        tb_client = TestbrainClient(schema, host, port, token)
        tb_client.push_commits(project_id=1)
