import logging
import pathlib
import typing as t

import click

from testbrain.cli.core.command import TestbrainCommand, TestbrainGroup
from testbrain.cli.core.context import TestbrainContext
from testbrain.contrib.scm.exceptions import SCMError

from .exceptions import ProjectNotFound
from .models import Commit
from .services import CheckoutService, PushService

logger = logging.getLogger(__name__)


@click.group(
    name="git",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.pass_context
def git(ctx: TestbrainContext, **kwargs):
    logger.debug(f"Git running with {ctx} {kwargs}")


@git.command("push", cls=TestbrainCommand, default=True)
@click.option(
    "--server",
    "--url",
    metavar="<url>",
    required=True,
    type=str,
    envvar="TESTBRAIN_SERVER",
    show_envvar=True,
    help="Enter your testbrain server instance url.",
)
@click.option(
    "--token",
    "--apikey",
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
@click.option(
    "--commit",
    "--start",
    metavar="<sha>",
    show_default="latest (HEAD)",
    type=str,
    default="latest",
    required=True,
    envvar="TESTBRAIN_START_COMMIT",
    show_envvar=True,
    help="Enter the commit that should be starter. If not "
    "specified, it will be used 'latest' commit.",
)
@click.option(
    "--number",
    metavar="<number>",
    show_default=True,
    type=int,
    default=100,
    envvar="TESTBRAIN_NUMBER_OF_COMMITS",
    show_envvar=True,
    help="Enter the number of commits to process.",
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
    repo_name,
    repo_dir,
    branch,
    commit,
    number,
    blame,
    minimize,
    pr_mode,
    **kwargs,
):
    _params = ctx.params.copy()
    _params["token"] = "*" * len(_params["token"])

    logger.debug(f"Running push with params {_params} {kwargs}")

    logger.info("Running...")

    if commit == "latest" or not commit:
        commit = "HEAD"

    service = PushService(
        server=server,
        token=token,
        repo_dir=repo_dir,
        repo_name=repo_name,
        project=project,
        pr_mode=pr_mode,
    )

    branch = service.validate_branch(branch=branch)

    kwargs = {
        "raw": not minimize,
        "patch": not minimize,
        "blame": blame,  # not minimize,
    }

    try:
        logger.info("Stating get commits from git")
        commits: t.List[Commit] = service.get_commits(
            commit=commit,
            number=number,
            **kwargs,
        )
        logger.info(f"Finished get commits from git - {len(commits)} commits(s)")

        logger.info(f"Stating get file_tree from git - {service.vcs.repo_name}")
        file_tree: t.List[str] = service.get_file_tree(
            branch=branch if not pr_mode else commit, minimize=minimize
        )
        logger.info(f"Finished get file_tree from git - {len(file_tree)} file(s)")

        payload = service.make_changes_payload(
            branch=branch, commits=commits, file_tree=file_tree
        )

        logger.info(f"Sending changes payload to server - {server}")
        _ = service.send_changes_payload(payload=payload)
        logger.info(f"Sent changes payload to server - {server}")
    except (ProjectNotFound, SCMError):
        ctx.exit(127)

    logger.info("Done")


@git.command("checkout", cls=TestbrainCommand)
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
def checkout(ctx: TestbrainContext, repo_dir, branch, commit, pr_mode, **kwargs):
    _params = ctx.params.copy()

    logger.debug(f"Running checkout with params {_params} {kwargs}")

    logger.info("Running checkout...")

    if commit == "latest" or not commit:
        commit = "HEAD"

    try:
        service = CheckoutService(repo_dir=repo_dir, pr_mode=pr_mode)
        service.checkout(branch=branch, commit=commit)
    except SCMError:
        ctx.exit(127)

    logger.info("Done")
