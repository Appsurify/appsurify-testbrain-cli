import time
import random
from testbrain.contrib.client.client import HttpClient
from testbrain.contrib.client.auth import HTTPAPIAuth
from testbrain.contrib.client.utils import get_user_agent


def test_get_request(requests_mock):
    requests_mock.get("http://demo.testbrain.cloud", status_code=200)

    api_client = HttpClient()
    api_response = api_client.get("http://demo.testbrain.cloud")

    time.sleep(random.uniform(0.2, 0.9))
    assert api_response.status_code == 200


def test_post_request(requests_mock):
    requests_mock.post("http://demo.testbrain.cloud", status_code=201)

    api_client = HttpClient()

    api_response = api_client.post("http://demo.testbrain.cloud")
    time.sleep(random.uniform(0.2, 0.9))
    assert api_response.status_code == 201


def test_client_session_configuration(requests_mock):
    requests_mock.get(
        "http://demo.testbrain.cloud",
        status_code=200,
        json={"status": "ok"},
    )

    api_client = HttpClient()
    api_response = api_client.get("http://demo.testbrain.cloud")
    api_origin_req = api_response.request
    assert api_origin_req


def test_header_ua(requests_mock):
    requests_mock.get(
        "http://demo.testbrain.cloud",
        status_code=200,
        json={"status": "ok"},
    )

    api_client = HttpClient()
    api_response = api_client.get("http://demo.testbrain.cloud")
    api_origin_req = api_response.request

    user_agent = get_user_agent(api_client.name, api_client.version)
    time.sleep(random.uniform(0.2, 0.9))
    assert api_origin_req.headers["User-Agent"] == user_agent

    user_agent = "python-requests/2.31.0"
    headers = {"User-Agent": user_agent}
    api_response = api_client.get("http://demo.testbrain.cloud", headers=headers)
    api_origin_req = api_response.request
    time.sleep(random.uniform(0.2, 0.9))
    assert api_origin_req.headers["User-Agent"] != user_agent


def test_header_auth(requests_mock):
    requests_mock.get(
        "http://demo.testbrain.cloud",
        status_code=200,
        json={"status": "ok"},
    )

    api_auth = HTTPAPIAuth(token="<TOKEN>")

    api_client = HttpClient()
    api_response = api_client.get("http://demo.testbrain.cloud", auth=api_auth)
    api_origin_req = api_response.request

    header_keyword = HTTPAPIAuth.keyword
    time.sleep(random.uniform(0.2, 0.9))
    assert header_keyword in api_origin_req.headers

    assert api_origin_req.headers[header_keyword] == "<TOKEN>"
