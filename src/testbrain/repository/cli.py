import logging
import os
import pathlib
import sys

import click

from testbrain.core import TestbrainCommand, TestbrainContext, TestbrainGroup

from testbrain.repository.services import PushService

logger = logging.getLogger(__name__)


@click.group(
    name="repo", cls=TestbrainGroup, default_if_no_args=True, no_args_is_help=True
)
@click.version_option("unknown")
@click.pass_context
def app(ctx: TestbrainContext, **kwargs):
    ...


def work_dir_callback(ctx, param, value):
    logger.debug(f"Set workdir to {value}")
    os.chdir(value)
    return value


@app.command("push", cls=TestbrainCommand, default=True)
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
    "--work-dir",
    metavar="<dir>",
    type=click.Path(dir_okay=True, resolve_path=True),
    default=pathlib.Path("."),
    callback=work_dir_callback,
    is_eager=True,
    show_default=True,
    envvar="TESTBRAIN_WORK_DIR",
    show_envvar=True,
    help="Enter the testbrain script working directory. "
    "If not specified, the current working directory "
    "will be used.",
)
@click.option(
    "--repo-name",
    metavar="<name>",
    type=str,
    envvar="TESTBRAIN_REPO_NAME",
    show_envvar=True,
    help="Define repository name. If not specified, it will be "
    "automatically taken from the GitRepository repository.",
)
@click.option(
    "--repo-dir",
    metavar="<dir>",
    type=click.Path(dir_okay=True, resolve_path=True),
    default=pathlib.Path("."),
    show_default=True,
    envvar="TESTBRAIN_REPO_DIR",
    show_envvar=True,
    help="Enter the git repository directory. If not specified, "
    "the current working directory will be used.",
)
@click.option(
    "--branch",
    metavar="<name>",
    show_default="current",
    type=str,
    envvar="TESTBRAIN_BRANCH",
    show_envvar=True,
    help="Enter the explicit branch to process commits. If not "
    "specified, use current active branch.",
)
@click.option(
    "--number",
    metavar="<number>",
    show_default=True,
    type=int,
    default=1,
    envvar="TESTBRAIN_NUMBER_OF_COMMITS",
    show_envvar=True,
    help="Enter the number of commits to process.",
)
@click.option(
    "--start",
    metavar="<sha>",
    show_default="latest (HEAD)",
    type=str,
    default="latest",
    envvar="TESTBRAIN_START_COMMIT",
    show_envvar=True,
    help="Enter the commit that should be starter. If not "
    "specified, it will be used 'latest' commit.",
)
@click.option(
    "--blame",
    show_default="False",
    type=bool,
    default=False,
    is_flag=True,
    help="Add blame information.",
)
@click.option(
    "--minimize",
    show_default="False",
    type=bool,
    default=False,
    is_flag=True,
    help="Suppress commit changes information.",
)
@click.pass_context
def push(
    ctx: "TestbrainContext",
    server,
    token,
    project,
    work_dir,
    repo_name,
    repo_dir,
    branch: str,
    number: int,
    start: str,
    blame: bool,
    minimize: bool,
    **kwargs,
):
    ctx.work_dir = work_dir
    logger.debug(
        f"Exec with params: "
        f"server='{server}' "
        f"token='{token}' "
        f"project='{project}' "
        f"work_dir='{work_dir}' "
        f"repo_name='{repo_name}' "
        f"repo_dir='{repo_dir}' "
        f"branch='{branch}' "
        f"number='{number}' "
        f"start='{start}' "
        f"blame='{blame}' "
        f"minimize='{minimize}'"
    )
    logger.debug(
        f"Exec with extra params: "
        f"loglevel={ctx.params.get('loglevel')} "
        f"logfile={ctx.params.get('logfile')}"
    )

    commit = start
    if commit == "latest":
        commit = "HEAD"

    logger.warning("WARNUP")
    logger.debug("Initializing git2testbrain controller")
    service = PushService(
        server=server,
        token=token,
        project=project,
        repo_dir=repo_dir,
        repo_name=repo_name,
    )

    logger.info("Preparing delivery payload")
    payload_kwargs = {
        "raw": not minimize,
        "patch": not minimize,
        "blame": not minimize,
        "file_tree": not minimize,
    }
    payload = service.get_changes_payload(
        branch=branch, commit=commit, number=number, **payload_kwargs
    )
    logger.info("Prepared delivery payload")

    logger.info("Delivering payload to server")
    response = service.send_changes_payload(payload=payload)
    logger.debug(f"Send result: [{response.status_code}] {response.content}")
    logger.info("Delivered payload to server")

    logger.info("Done")
    logger.debug("Shutdown...")


git2testbrain = app
git2appsurify = app


if __name__ == "__main__":
    logger.name = "testbrain.repository.cli"
    app(prog_name="repository")
