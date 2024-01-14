from testbrain.cli.apps.repository.git.client import RepositoryClient, RepositoryAuth


def test_git_client_get_project(requests_mock):
    requests_mock.get(
        "http://demo.testbrain.cloud/api/ssh_v2/hook/fetch/",
        json={"project_id": 1},
        status_code=200,
    )

    api_client = RepositoryClient(server="http://demo.testbrain.cloud", token="<TOKEN>")
    api_response = api_client.get_project_id(name="appsurify-testbrain-cli")
    assert api_response.status_code == 200
    assert api_response.json() == {"project_id": 1}

    requests_mock.get(
        "http://demo.testbrain.cloud/api/ssh_v2/hook/fetch/",
        json={"error": "Project didn't exist, check project name and try again!"},
        status_code=200,
    )

    api_client = RepositoryClient(server="http://demo.testbrain.cloud", token="<TOKEN>")
    api_response = api_client.get_project_id(name="appsurify-testbrain-cli")
    assert api_response.status_code == 200
    assert api_response.json() == {
        "error": "Project didn't exist, check project name and try again!"
    }


def test_git_client_header_auth(requests_mock):
    requests_mock.get(
        "http://demo.testbrain.cloud/api/ssh_v2/hook/fetch/",
        json={"project_id": 1},
        status_code=200,
    )

    api_client = RepositoryClient(server="http://demo.testbrain.cloud", token="<TOKEN>")
    api_response = api_client.get_project_id(name="appsurify-testbrain-cli")

    api_origin_req = api_response.request

    header_keyword = RepositoryAuth.keyword

    assert header_keyword in api_origin_req.headers

    assert api_origin_req.headers[header_keyword] == "<TOKEN>"
