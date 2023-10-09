import logging
from urllib.parse import urljoin

from testbrain.client.client import TestbrainAPIClient


logger = logging.getLogger(__name__)


class Git2TestbrainAPIClient(TestbrainAPIClient):
    def __init__(self, server, token, **kwargs):
        super().__init__(server=server, token=token, **kwargs)
        logger.debug(
            f"Initialized Testbrain API client for: {server} ({'*' * len(token)})"
        )

    def get_project_id(self, name: str) -> int:
        endpoint = "/api/ssh_v2/hook/fetch/"
        params = {"project_name": name}

        logger.info(f"request for convert project {name} to ID.")
        resp = self.get(url=urljoin(self.base_url, endpoint), params=params)
        json_data = resp.json()
        project_id = json_data.get("project_id")
        if isinstance(project_id, str):
            project_id = int(project_id)
        return project_id

    def post_hook(self, project_id: int, json: dict):
        endpoint = f"/api/ssh_v2/hook/{project_id}/"
        resp = self.post(url=urljoin(self.base_url, endpoint), json=json)
        return resp
