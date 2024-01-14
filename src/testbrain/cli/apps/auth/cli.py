import logging
import pathlib
import typing as t

import click

import testbrain.cli
from testbrain.cli.core.command import TestbrainCommand, TestbrainGroup
from testbrain.cli.core.context import TestbrainContext
from testbrain.contrib.client import client

logger = logging.getLogger(__name__)


@click.group(
    name="auth",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.pass_context
def auth(ctx: TestbrainContext, **kwargs):
    logger.debug(f"Auth running with {ctx} {kwargs}")


@auth.command("token", cls=TestbrainCommand, default=True)
@click.option(
    "--server",
    metavar="<url>",
    required=True,
    type=str,
    envvar="TESTBRAIN_SERVER",
    show_envvar=True,
    help="Enter your testbrain server instance url.",
)
@click.option("--email", prompt="Email", help="Enter your e-mail.")
@click.option(
    "--password", prompt="Password", hide_input=True, help="Enter your password."
)
@click.pass_context
def token(ctx: TestbrainContext, server, email, password, **kwargs):
    logger.debug(f"Token running with {ctx} {kwargs}")
    http_client = client.HttpClient()
    resp_login = http_client.post(
        f"{server}/api/account/login/",
        json={"email": email, "password": password},
    )
    if resp_login.status_code != 200:
        logger.critical(f"Invalid email or password: {resp_login.content}")
        ctx.exit(118)

    resp_profile = http_client.get(f"{server}/api/account/profile/")
    if resp_profile.status_code != 200:
        logger.critical("Invalid request API key")
        ctx.exit(119)

    profile_data = resp_profile.json()
    try:
        click.echo(f"API_KEY: {profile_data['api_key']}")
    except KeyError:
        logger.exception("Invalid API Key")
        ctx.exit(119)
