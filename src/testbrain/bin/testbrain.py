import logging

import click

from testbrain.bin.git2testbrain import cli as git2testbrain_cli

logger = logging.getLogger(__name__)


@click.group(name="testbrain", invoke_without_command=True)
@click.pass_context
def cli(ctx, *args, **kwargs):
    logger.info("INFO")
    click.echo("HERE")
    click.echo(__file__)


cli.add_command(git2testbrain_cli)

if __name__ == "__main__":
    cli()
