import logging

import click

import testbrain.cli
from testbrain.cli.apps.auth.cli import auth
from testbrain.cli.apps.report.cli import report
from testbrain.cli.apps.repository.cli import repository
from testbrain.cli.core.command import TestbrainContext, TestbrainGroup

logger = logging.getLogger(__name__)


@click.group(
    name=testbrain.cli.__prog__,
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.version_option(  # TODO: "%(package)s (%(prog)s %(version)s)"
    package_name=testbrain.cli.__name__,
    prog_name=testbrain.cli.__prog__,
    version=testbrain.cli.__version__,
    message="%(package)s (%(version)s) [%(prog)s]",
)
@click.pass_context
def app(ctx: TestbrainContext, **kwargs):
    logger.debug(f"testbrain run with {ctx} {kwargs}")


# TODO: Will be needed refactoring
app.add_command(auth, "auth")
app.add_command(repository, "repository")
app.add_command(report, "report")
