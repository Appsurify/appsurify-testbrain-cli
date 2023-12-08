import logging

import click

import testbrain
from testbrain.core.command import TestbrainContext, TestbrainGroup

from testbrain.contrib.repository.cli import repository


logger = logging.getLogger(__name__)


@click.group(
    name="testbrain",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.version_option(
    package_name="appsurify-testbrain-cli",
    prog_name="testbrain",
    message=testbrain.short_version_message,
)
@click.pass_context
def app(ctx: TestbrainContext, **kwargs):
    logger.debug(f"testbrain run with {ctx} {kwargs}")


app.add_command(repository, name="repository")
