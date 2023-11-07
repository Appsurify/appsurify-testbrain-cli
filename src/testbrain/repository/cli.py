import logging
import os
import pathlib
import sys
import typing as t

import click

from testbrain import version_message
from testbrain.core import TestbrainCommand, TestbrainContext, TestbrainGroup
from testbrain.repository.exceptions import ProjectNotFound, VCSError
from testbrain.repository.models import Commit
from testbrain.repository.services import PushService, CheckoutService
from testbrain.repository.types import T_File

logger = logging.getLogger(__name__)


@click.group(
    name="repository",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.version_option(
    package_name="appsurify-testbrain-cli",
    prog_name="repository",
    message=version_message,
)
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
@click.option(
    "--pr-mode",
    show_default="False",
    type=bool,
    default=False,
    envvar="TESTBRAIN_PR_MODE",
    show_envvar=True,
    is_flag=True,
    help="Activate PR mode.",
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
    branch,
    number,
    start,
    blame,
    minimize,
    pr_mode,
    **kwargs,
):
    _params = ctx.params.copy()
    _params["token"] = "*" * len(_params["token"])

    logger.debug(f"Running push with params {_params}")

    ctx.work_dir = work_dir

    logger.info("Running...")

    commit = start
    if commit == "latest" or not commit:
        commit = "HEAD"

    service = PushService(
        server=server,
        token=token,
        project=project,
        repo_dir=repo_dir,
        repo_name=repo_name,
    )

    # if branch is None:
    #     branch = service.get_current_branch()
    #     logger.debug(f"Branch was not specified. Use current active branch: {branch}")

    kwargs = {
        "raw": not minimize,
        "patch": not minimize,
        "blame": blame,  # not minimize,
    }

    try:
        logger.info(f"Stating get commits from repository - {service.repo_name}")
        commits: t.List[Commit] = service.get_repository_commits(
            branch=branch if not pr_mode else commit,
            commit=commit,
            number=number,
            **kwargs,
        )
        logger.info(f"Finished get commits from repository - {len(commits)} commits(s)")

        logger.info(f"Stating get file_tree from repository - {service.repo_name}")
        file_tree: t.List[T_File] = service.get_repository_file_tree(
            branch=branch if not pr_mode else commit, minimize=minimize
        )
        logger.info(
            f"Finished get file_tree from repository - {len(file_tree)} file(s)"
        )

        payload = service.make_changes_payload(
            branch=branch, commits=commits, file_tree=file_tree
        )

        logger.info(f"Sending changes payload to server - {server}")
        _ = service.send_changes_payload(payload=payload)
        logger.info(f"Sent changes payload to server - {server}")
    except (ProjectNotFound, VCSError):
        ctx.exit(127)

    logger.info("Done")


@app.command("checkout", cls=TestbrainCommand, default=True)
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
    "--commit",
    "--start",
    metavar="<sha>",
    show_default="latest (HEAD)",
    type=str,
    default="HEAD",
    envvar="TESTBRAIN_START_COMMIT",
    show_envvar=True,
    help="Enter the commit that should be starter. If not "
    "specified, it will be used 'latest' commit.",
)
@click.option(
    "--pr-mode",
    show_default="False",
    type=bool,
    default=False,
    envvar="TESTBRAIN_PR_MODE",
    show_envvar=True,
    is_flag=True,
    help="Activate PR mode.",
)
@click.pass_context
def checkout(
    ctx: TestbrainContext, work_dir, repo_dir, branch, commit, pr_mode, **Kwargs
):
    _params = ctx.params.copy()

    logger.debug(f"Running checkout with params {_params}")

    ctx.work_dir = work_dir

    logger.info("Running checkout...")

    if commit == "latest" or not commit:
        commit = "HEAD"

    try:
        service = CheckoutService(repo_dir=repo_dir, pr_mode=pr_mode)
        service.checkout(branch=branch, commit=commit)
    except VCSError:
        ctx.exit(127)

    logger.info("Done")


git2testbrain = app
git2appsurify = app


if __name__ == "__main__":
    logger.name = "testbrain.repository.cli"
    app(prog_name="repository")
