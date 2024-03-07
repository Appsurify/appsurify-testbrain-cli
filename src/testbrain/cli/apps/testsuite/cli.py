import logging
import pathlib
import typing as t
from urllib.parse import urljoin

import click

import testbrain.cli
from testbrain.cli.core.command import TestbrainCommand, TestbrainGroup
from testbrain.cli.core.context import TestbrainContext
from testbrain.contrib.client import auth, client

logger = logging.getLogger(__name__)


@click.group(
    name="testsuite",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.pass_context
def testsuite(ctx: TestbrainContext, **kwargs):
    logger.debug(f"Testsuite running with {ctx} {kwargs}")


@testsuite.command("create", cls=TestbrainCommand, default=True)
@click.option(
    "--server",
    metavar="<url>",
    required=True,
    type=str,
    help="Enter your testbrain server instance url.",
)
@click.option(
    "--token",
    "--apikey",
    metavar="<token>",
    type=str,
    help="Enter your testbrain server instance token.",
)
@click.option("--email", prompt="Email", help="Enter your e-mail.")
@click.option(
    "--password", prompt="Password", hide_input=True, help="Enter your password."
)
@click.option(
    "--project",
    metavar="<name>",
    required=True,
    type=str,
    help="Enter your testbrain project name.",
)
@click.option(
    "--testsuite",
    metavar="<name>",
    required=True,
    type=str,
    help="Enter your testbrain testsuite name.",
)
@click.pass_context
def create(ctx: TestbrainContext, server, email, password, **kwargs):
    logger.info(f"Testsuite create running with {ctx} {kwargs}")
    logger.info(f"Params with {server}, {email}, {password}")

    http_client = client.HttpClient()

    logger.info(f"Authenticating with {email}, {'*' * len(password)}")
    resp_login = http_client.post(
        urljoin(server, "/api/account/login/"),
        json={"email": email, "password": password},
    )
    if resp_login.status_code != 200:
        logger.critical(f"Invalid email or password: {resp_login.content}")
        ctx.exit(119)

    login_data = resp_login.json()
    token = login_data.get("key")
    logger.info("User logged in successfully")

    http_auth = auth.HTTPTokenAuth(token=token)

    project_id = None
    project_name = kwargs.get("project")
    testsuite_name = kwargs.get("testsuite")

    # Check project exists
    resp_project_check = http_client.get(
        urljoin(server, "/api/ssh_v2/hook/fetch/"),
        params={"project_name": project_name},
        auth=http_auth,
    )
    if resp_project_check.status_code == 200:
        project_data = resp_project_check.json()
        project_id = project_data.get("project_id")
        error = project_data.get("error")
        if not project_id:
            logger.debug(f"Response from server: {project_name} > {error}")
            logger.critical(f"Project '{project_name}' not found on server.")
            ctx.exit(118)

        if isinstance(project_id, str):
            project_id = int(project_id)
    else:
        logger.critical(
            f"Something went wrong: [{resp_project_check.status_code}] "
            f"{resp_project_check.content[:255]}"
        )
        ctx.exit(118)

    if not project_id:
        logger.critical(f"Can't get project ID from server: {project_name}")
        ctx.exit(118)

    resp_create_testsuite = http_client.post(
        urljoin(server, "/api/test-suites/"),
        json={
            "name": testsuite_name,
            "project": project_id,
        },
        auth=http_auth,
    )
    if resp_create_testsuite.status_code not in [200, 201]:
        logger.error(
            f"Something went wrong: [{resp_create_testsuite.status_code}] "
            f"{resp_create_testsuite.content[:255]}"
        )
        ctx.exit(118)

    testsuite_data = resp_create_testsuite.json()

    logger.info(f"Test suite created successfully: {testsuite_data.get('name')}")

    ctx.exit(0)


if __name__ == "__main__":
    testsuite()
