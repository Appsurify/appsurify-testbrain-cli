from typing import Any

import pytest
from requests_mock.mocker import Mocker
from urllib.parse import urljoin
from testbrain.client.client import APIClient, TestbrainAPIClient
from testbrain.client.auth import HTTPAPIAuth
from testbrain.client.utils import default_user_agent


class TestClient:
    def test_get_request(self, requests_mock):
        requests_mock.get("http://demo.testbrain.cloud", status_code=200)
        api_client = APIClient()
        api_response = api_client.get("http://demo.testbrain.cloud")
        assert api_response.status_code == 200

    def test_post_request(self, requests_mock):
        requests_mock.post("http://demo.testbrain.cloud", status_code=201)
        api_client = APIClient()
        api_response = api_client.post("http://demo.testbrain.cloud")
        assert api_response.status_code == 201

    def test_header_ua(self, requests_mock):
        requests_mock.get(
            "http://demo.testbrain.cloud", status_code=200, json={"status": "ok"}
        )
        api_client = APIClient()
        api_response = api_client.get("http://demo.testbrain.cloud")
        api_origin_req = api_response.request
        assert api_origin_req.headers["User-Agent"] == default_user_agent()

        user_agent = default_user_agent("TestAgent/0")
        headers = {"User-Agent": user_agent}
        api_response = api_client.get("http://demo.testbrain.cloud", headers=headers)
        api_origin_req = api_response.request
        assert api_origin_req.headers["User-Agent"] == user_agent

    def test_testbrain_client(self, requests_mock):
        requests_mock.get(
            "http://demo.testbrain.cloud/api/test",
            status_code=200,
            json={"status": "ok"},
        )
        api_client = TestbrainAPIClient(server="demo.testbrain.cloud", token="<TOKEN>")
        api_response = api_client.get("http://demo.testbrain.cloud/api/test")
        api_origin_req = api_response.request

        header_keyword = HTTPAPIAuth.keyword

        assert header_keyword in api_origin_req.headers

        assert api_origin_req.headers[header_keyword] == "<TOKEN>"

    def test_testbrain_client_url_merged(self, requests_mock):
        requests_mock.get(
            "http://demo.testbrain.cloud/api/test",
            status_code=200,
            json={"status": "ok"},
        )

        server = "http://demo.testbrain.cloud"
        api_client = TestbrainAPIClient(server=server, token="<TOKEN>")
        api_response = api_client.get(urljoin(server, "/api/test"))

        assert api_response.url == "http://demo.testbrain.cloud/api/test"

        requests_mock.get(
            "http://demo.testbrain.cloud/api/test",
            status_code=200,
            json={"status": "ok"},
        )

        server = "http://demo.testbrain.cloud/"
        api_client = TestbrainAPIClient(server=server, token="<TOKEN>")
        api_response = api_client.get(urljoin(server, "/api/test"))

        assert api_response.url == "http://demo.testbrain.cloud/api/test"

    # def test_g2t_client(self, requests_mock):
    #     requests_mock.get(
    #         "https://demo.testbrain.cloud/api/ssh_v2/hook/fetch/",
    #         json={"project_id": "1"},
    #         status_code=200,
    #     )
    #     api_client = Git2TestbrainAPIClient(
    #         server="https://demo.testbrain.cloud", token="<TOKEN>"
    #     )
    #
    #     api_response = api_client.get_project_id(name="test")
    #     assert api_response == 1
    #
    # def test_g2t_client(self, requests_mock):
    #     with pytest.raises(Exception) as exc_info:
    #         requests_mock.get(
    #             "https://demo.testbrain.cloud/api/ssh_v2/hook/fetch/",
    #             json={},
    #             status_code=404,
    #         )
    #         api_client = Git2TestbrainAPIClient(
    #             server="https://demo.testbrain.cloud/", token="<TOKEN>"
    #         )
    #
    #         api_response = api_client.get_project_id(name="test")
    #         raise Exception("project_id")
    #     assert exc_info.value.args[0] == "project_id"
