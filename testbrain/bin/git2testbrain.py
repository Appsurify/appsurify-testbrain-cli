import os
import sys
import pathlib
import logging
import click
from testbrain.core import TestbrainContext, TestbrainCommand
from testbrain.git2testbrain import TB_ART_LINES_STYLED
from testbrain.git2testbrain.controller import Git2TestbrainController


logger = logging.getLogger(__name__)


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    # TODO: MAKE BANNER LIKE CELERY
    VERSION_BANNER = f"Version: 23021302032103021"
    click.echo(VERSION_BANNER)
    ctx.exit(0)


def work_dir_callback(ctx, param, value):
    logger.debug(f"set workdir to {value}")
    os.chdir(value)
    return value


@click.command("git2testbrain", cls=TestbrainCommand)
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
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show version.",
)
@click.pass_context
def cli(
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

    logger.debug(f"Initializing git2testbrain controller.")
    git2testbrain_controller = Git2TestbrainController(
        server=server,
        token=token,
        project=project,
        repo_dir=repo_dir,
        repo_name=repo_name,
    )

    logger.debug(f"Get GIT repository changes.")
    delivery_payload = git2testbrain_controller.get_payload(
        branch=branch, commit=commit, number=number, blame=blame
    )

    logger.debug(f"Send GIT repository changes to server.")
    # print(delivery_payload.model_dump_json(indent=4))
    # delivery_status = git2testbrain_controller.deliver_repository_changes(
    #     timeout=120, max_tries=3
    # )
    # a = 1 / 0
    logger.info("Done")
    logger.debug(f"Shutdown...")


if __name__ == "__main__":
    cli()
