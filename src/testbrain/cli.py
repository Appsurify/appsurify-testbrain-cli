import logging

import click

import testbrain
from testbrain.core import TestbrainContext, TestbrainGroup
from testbrain.repository.cli import app as repository_app

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
    message=testbrain.version_message,
)
@click.pass_context
def app(ctx: TestbrainContext, **kwargs):
    ...


# app.add_command(repository_app, default=True)
app.add_command(repository_app, name="repository")
app.add_command(repository_app, name="git2testbrain")
app.add_command(repository_app, name="git2appsurify")


if __name__ == "__main__":
    app(prog_name="testbrain")
