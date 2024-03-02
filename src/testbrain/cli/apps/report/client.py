import logging
import typing as t
from io import BytesIO
from urllib.parse import urljoin

import requests

from testbrain.contrib.client.auth import HTTPAPIAuth
from testbrain.contrib.client.client import HttpClient

logger = logging.getLogger(__name__)


class ReportAuth(HTTPAPIAuth):
    ...


class ReportClient(HttpClient):
    def __init__(self, server: str, token: str, **kwargs):
        self.base_url = server
        self.token = token
        self.auth = ReportAuth(token=token)
        super().__init__(**kwargs)

    @property
    def version(self) -> str:
        from . import __version__

        return __version__

    @property
    def user_agent(self) -> str:
        base = super().user_agent
        parent_part = self.parent.name + "/" + self.parent.version
        return f"{base} {parent_part}"

    def request(self, method: str, url: str, **kwargs):
        return super().request(method, url, auth=self.auth, **kwargs)

    def push_report(
        self,
        project: str,
        testsuite: str,
        commit: str,
        report_type: t.Optional[str] = "junit",
        import_type: t.Optional[str] = "prioritized",
        branch: t.Optional[str] = None,
        repo: t.Optional[str] = "git",
        repo_name: t.Optional[str] = None,
        timeout: t.Optional[int] = None,
        max_retries: t.Optional[int] = None,
        report: t.Optional[BytesIO] = None,
        reports: t.Optional[t.List[BytesIO]] = None,
    ):
        endpoint = "/api/external/import/"
        headers = {}
        data = {
            "project_name": project,
            "test_suite_name": testsuite,
            "type": str(report_type).lower(),
            "import_type": import_type,
            "commit": commit,
        }
        if branch is not None:
            data["branch"] = branch

        if repo is not None:
            data["repo"] = repo

        if repo_name is not None:
            data["repo_name"] = repo_name

        file_type = "text/xml"
        if report_type == "testbrain":
            file_type = "application/json"

        files = []

        if report is not None:
            files.append(("file", (report.name, report, file_type)))
        elif reports is not None:
            for report in reports:
                files.append(("files", (report.name, report, file_type)))

        logger.debug(f"Push report request: {endpoint} {data} {files}")

        try:
            response = self.post(
                url=urljoin(self.base_url, endpoint),
                data=data,
                files=files,
                headers=headers,
                timeout=timeout,
                max_retries=max_retries,
            )
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(
                    f"Some problem with push report request: status code: "
                    f"{response.status_code} {response.content[:255]}"
                )
                raise Exception(response.content)
        except requests.exceptions.ConnectionError:
            logger.exception("Problem with server connection", exc_info=False)
            return None
