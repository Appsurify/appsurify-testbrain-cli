import logging
import click
import testbrain

from testbrain.core.command import TestbrainContext, TestbrainGroup
from testbrain.apps.git import cli as git_cli
from testbrain.apps.tfvc import cli as tfvc_cli


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
    message="%(prog)s (%(version)s) [%(package)s]",
)
@click.pass_context
def app(ctx: TestbrainContext, **kwargs):
    logger.debug(f"testbrain run with {ctx} {kwargs}")


app.add_command(tfvc_cli.tfvc, "tfvc")

app.add_command(git_cli.git, "git")
app.add_command(git_cli.git, "repository")
app.add_command(git_cli.push, "git2appsurify")
app.add_command(git_cli.push, "git2testbrain")
