import logging

import click

import testbrain
from testbrain.core import TestbrainContext, TestbrainCommand, TestbrainGroup
from testbrain.repository.cli import app as repository_app

logger = logging.getLogger(__name__)


@click.group(
    name="testbrain", cls=TestbrainGroup, default_if_no_args=True, no_args_is_help=True
)
@click.version_option(testbrain.pkg_version)
@click.pass_context
def app(ctx: TestbrainContext, **kwargs):
    ...


app.add_command(repository_app, "repo", defalut=True)


if __name__ == "__main__":
    app(prog_name="testbrain")
