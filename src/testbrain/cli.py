import logging

import click

import testbrain
from testbrain.core import TestbrainCommand, TestbrainContext, TestbrainGroup
from testbrain.repository.cli import app as repository_app
from testbrain.tests.cli import app as tests_app

logger = logging.getLogger(__name__)


@click.group(
    name="testbrain",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.version_option(
    version=testbrain.pkg_version,
    package_name=testbrain.pkg_name,
    prog_name="testbrain",
    message="%(package)s, %(prog)s/%(version)s",
)
@click.pass_context
def app(ctx: TestbrainContext, **kwargs):
    ...


# app.add_command(repository_app, default=True)
app.add_command(repository_app, name="vcs")
app.add_command(tests_app, name="tests")


if __name__ == "__main__":
    app(prog_name="testbrain")
