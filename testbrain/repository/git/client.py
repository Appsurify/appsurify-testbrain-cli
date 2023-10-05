from testbrain.client import TestbrainAPIClient
from urllib.parse import urljoin


class Git2TestbrainClient(TestbrainAPIClient):


    def get_project_id(self, name: str) -> int:
        endpoint = "/api/ssh_v2/hook/fetch/"
        params = {"project": name}

        resp = self.get(url=urljoin(self.base_url, endpoint), params=params)
        # if resp.status_code == 200:
        json_data = resp.json()
        project_id = json_data["project_id"]
        if isinstance(project_id, str):
            project_id = int(project_id)
        return project_id

