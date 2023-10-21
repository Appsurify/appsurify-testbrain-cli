import logging

import click
from testbrain.bin.git2testbrain import cli as _git2testbrain
from testbrain.core.command import TestbrainGroup

logger = logging.getLogger(__name__)


@click.group(name="testbrain", cls=TestbrainGroup, invoke_without_command=True)
@click.pass_context
def cli(ctx, *args, **kwargs):
    logger.info("INFO")


cli.add_command(_git2testbrain)


if __name__ == "__main__":
    logger.name = "testbrain.bin.testbrain"
    cli()
