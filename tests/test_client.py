from urllib.parse import urljoin

from testbrain.core.api.client import APIClient
from testbrain.core.api.auth import HTTPAPIAuth
from testbrain.git2testbrain.client import Git2TestbrainAPIClient


class TestClient:
    def test_get_request(self, requests_mock):
        requests_mock.get("http://demo.testbrain.cloud", status_code=200)

        class TestClass(APIClient):
            name = "TestClass"

        api_client = TestClass()
        api_response = api_client.get("http://demo.testbrain.cloud")
        assert api_response.status_code == 200

    def test_post_request(self, requests_mock):
        requests_mock.post("http://demo.testbrain.cloud", status_code=201)

        class TestClass(APIClient):
            name = "TestClass"

        api_client = TestClass()
        api_response = api_client.post("http://demo.testbrain.cloud")
        assert api_response.status_code == 201

    def test_client_session_configuration(self, requests_mock):
        requests_mock.get(
            "http://demo.testbrain.cloud",
            status_code=200,
            json={"status": "ok"},
        )

        class TestClass(APIClient):
            name = "TestClass"

        api_client = TestClass()
        api_response = api_client.get("http://demo.testbrain.cloud")
        api_origin_req = api_response.request
        assert api_origin_req

    # def test_header_ua(self, requests_mock):
    #     requests_mock.get(
    #         "http://demo.testbrain.cloud",
    #         status_code=200,
    #         json={"status": "ok"},
    #     )
    #
    #     class TestClass(APIClient):
    #         name = "TestClass"
    #
    #     api_client = TestClass()
    #     api_response = api_client.get("http://demo.testbrain.cloud")
    #     api_origin_req = api_response.request
    #     assert api_origin_req.headers["User-Agent"] == (
    #         "TestClass/2023.9.9 "
    #         "(Darwin/23.0.0; CPython/3.7.2; "
    #         "x86_64) Build/undefined "
    #         "(included: appsurify-testbrain-cli/2023.9.9)"
    #     )
    #
    #     user_agent = "python-requests/2.31.0"
    #     headers = {"User-Agent": user_agent}
    #     api_response = api_client.get("http://demo.testbrain.cloud", headers=headers)
    #     api_origin_req = api_response.request
    #     assert api_origin_req.headers["User-Agent"] == user_agent

    def test_testbrain_client(self, requests_mock):
        requests_mock.get(
            "http://demo.testbrain.cloud/api/test",
            status_code=200,
            json={"status": "ok"},
        )
        api_client = Git2TestbrainAPIClient(
            server="demo.testbrain.cloud", token="<TOKEN>"
        )
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
        api_client = Git2TestbrainAPIClient(server=server, token="<TOKEN>")
        api_response = api_client.get(urljoin(server, "/api/test"))

        assert api_response.url == "http://demo.testbrain.cloud/api/test"

        requests_mock.get(
            "http://demo.testbrain.cloud/api/test",
            status_code=200,
            json={"status": "ok"},
        )

        server = "http://demo.testbrain.cloud/"
        api_client = Git2TestbrainAPIClient(server=server, token="<TOKEN>")
        api_response = api_client.get(urljoin(server, "/api/test"))

        assert api_response.url == "http://demo.testbrain.cloud/api/test"

    # def test_g2t_client(self, requests_mock):
    #     requests_mock.get(
    #         "https://demo.testbrain.cloud/api/ssh_v2/hook/fetch/",
    #         json={"project_id": "1"},
    #         status_code=200,
    #     )
    #     api_client = Git2TestbrainAPIv1Client(
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
    #         api_client = Git2TestbrainAPIv1Client(
    #             server="https://demo.testbrain.cloud/", token="<TOKEN>"
    #         )
    #
    #         api_response = api_client.get_project_id(name="test")
    #         raise Exception("project_id")
    #     assert exc_info.value.args[0] == "project_id"
