import logging

import click

import testbrain
from testbrain.apps.auth.cli import auth
from testbrain.apps.repository.cli import repository
from testbrain.core.command import TestbrainContext, TestbrainGroup

logger = logging.getLogger(__name__)


@click.group(
    name=testbrain.__prog__,
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.version_option(  # TODO: "%(package)s (%(prog)s %(version)s)"
    package_name=testbrain.__name__,
    prog_name=testbrain.__prog__,
    version=testbrain.__version__,
    message="%(package)s (%(version)s) [%(prog)s]",
)
@click.pass_context
def app(ctx: TestbrainContext, **kwargs):
    logger.debug(f"testbrain run with {ctx} {kwargs}")


# TODO: Will be needed refactoring
app.add_command(auth, "auth")
app.add_command(repository, "repository")
