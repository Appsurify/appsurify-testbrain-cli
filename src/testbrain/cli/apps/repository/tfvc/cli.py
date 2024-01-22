import logging
import pathlib
import typing as t

import click

import testbrain
from testbrain.cli.core.command import TestbrainCommand, TestbrainGroup
from testbrain.cli.core.context import TestbrainContext

logger = logging.getLogger(__name__)


@click.group(
    name="tfvc",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.pass_context
def tfvc(ctx: TestbrainContext, **kwargs):
    logger.debug(f"TFVC running with {ctx} {kwargs}")


@tfvc.command("push", cls=TestbrainCommand, default=True)
@click.option(
    "--server",
    metavar="<url>",
    required=True,
    type=str,
    envvar="TESTBRAIN_SERVER",
    show_envvar=True,
    help="Enter your testbrain server instance url.",
)
@click.option(
    "--token",
    metavar="<token>",
    required=True,
    type=str,
    envvar="TESTBRAIN_TOKEN",
    show_envvar=True,
    help="Enter your testbrain server instance token.",
)
@click.option(
    "--project",
    metavar="<name>",
    required=True,
    type=str,
    envvar="TESTBRAIN_PROJECT",
    show_envvar=True,
    help="Enter your testbrain project name.",
)
@click.option(
    "--repo-name",
    metavar="<name>",
    type=str,
    envvar="TESTBRAIN_REPO_NAME",
    show_envvar=True,
    help="Define git name. If not specified, it will be "
    "automatically taken from the GitRepository git.",
)
@click.option(
    "--repo-dir",
    metavar="<dir>",
    type=click.Path(dir_okay=True, resolve_path=True),
    default=pathlib.Path("."),
    show_default=True,
    envvar="TESTBRAIN_REPO_DIR",
    show_envvar=True,
    help="Enter the git git directory. If not specified, "
    "the current working directory will be used.",
)
@click.option(
    "--branch",
    metavar="<name>",
    show_default="current",
    type=str,
    required=True,
    envvar="TESTBRAIN_BRANCH",
    show_envvar=True,
    help="Enter the explicit branch to process commits. If not "
    "specified, use current active branch.",
)
@click.pass_context
def push(
    ctx: "TestbrainContext",
    server,
    token,
    project,
    repo_name,
    repo_dir,
    branch,
    **kwargs,
):
    _params = ctx.params.copy()
    _params["server"] = server
    _params["token"] = token
    _params["project"] = project
    _params["repo_name"] = repo_name
    _params["repo_dir"] = repo_dir
    _params["branch"] = branch

    _params["token"] = "*" * len(_params["token"])

    logger.debug(f"Running push with params {_params} {kwargs}")
    logger.info("Running...")
    logger.warning("This will take a while...")
