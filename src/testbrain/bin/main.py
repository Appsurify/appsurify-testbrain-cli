import logging

import click

from testbrain.bin.git2testbrain import cli as git2testbrain_cli
from testbrain.core.command import TestbrainCommand

logger = logging.getLogger(__name__)


# @click.group(name="testbrain", cls=TestbrainGroup)
@click.command("git2testbrain", cls=TestbrainCommand)
@click.pass_context
def cli(ctx, *args, **kwargs):
    logger.info("INFO")


cli.add_command(git2testbrain_cli)


if __name__ == "__main__":
    logger.name = "testbrain.bin.testbrain"
    cli()
