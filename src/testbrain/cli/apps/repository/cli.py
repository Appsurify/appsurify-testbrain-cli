import logging

import click

from testbrain.cli.core.command import TestbrainGroup
from testbrain.cli.core.context import TestbrainContext

from .git.cli import git
from .tfvc.cli import tfvc

logger = logging.getLogger(__name__)


@click.group(
    name="repository",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.pass_context
def repository(ctx: TestbrainContext, **kwargs):
    logger.debug(f"Git running with {ctx} {kwargs}")


repository.add_command(git, "git")
repository.add_command(tfvc, "tfvc")
