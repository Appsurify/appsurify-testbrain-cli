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
    name="project",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.pass_context
def project(ctx: TestbrainContext, **kwargs):
    logger.debug(f"Project running with {ctx} {kwargs}")


@project.command("create", cls=TestbrainCommand, default=True)
@click.option(
    "--server",
    metavar="<url>",
    required=True,
    type=str,
    help="Enter your testbrain server instance url.",
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
@click.pass_context
def create(ctx: TestbrainContext, server, email, password, **kwargs):
    logger.info(f"Project create running with {ctx} {kwargs}")
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

    new_project_name = kwargs.get("project")

    # Check project exists
    resp_project_check = http_client.get(
        urljoin(server, "/api/ssh_v2/hook/fetch/"),
        params={"project_name": new_project_name},
        auth=http_auth,
    )
    if resp_project_check.status_code == 200:
        project_data = resp_project_check.json()
        project_id = project_data.get("project_id")
        # error = project_data.get("error")
        if project_id:
            logger.error(f"Project '{new_project_name}' already exists")
            ctx.exit(118)

    resp_create_project = http_client.post(
        urljoin(server, "/api/projects/"),
        json={"name": new_project_name, "is_public": False},
        auth=http_auth,
    )
    if resp_create_project.status_code not in [200, 201]:
        logger.error(
            f"Something went wrong: [{resp_create_project.status_code}] "
            f"{resp_create_project.content[:255]}"
        )
        ctx.exit(118)

    resp_create_project_data = resp_create_project.json()
    logger.debug(f"Project data: {resp_create_project_data}")

    logger.info(
        f"Project '{resp_create_project_data.get('name')}' "
        f"created with id: {resp_create_project_data.get('id')}"
    )
    resp_create_project_integration = http_client.post(
        urljoin(server, "/api/ssh_v2/repository/"),
        json={"project": resp_create_project_data.get("id")},
        auth=http_auth,
    )
    if resp_create_project_integration.status_code not in [200, 201]:
        logger.error(
            f"Something went wrong: [{resp_create_project_integration.status_code}] "
            f"{resp_create_project_integration.content[:255]}"
        )
        resp_delete_project = http_client.request(
            "DELETE",
            urljoin(server, "/api/projects/"),
            json={"name": new_project_name, "is_public": False},
            auth=http_auth,
        )
        logger.info(f"Removing project: [{resp_delete_project.status_code}]")
        ctx.exit(118)

    logger.info("Project Integration created")
    ctx.exit(0)
