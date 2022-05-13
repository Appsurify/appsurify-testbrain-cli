"""The Void command."""

import click

from testbrain.bin.base import (TestbrainCommand, TestbrainOption, handle_preload_options)


@click.command(cls=TestbrainCommand)
@click.option('-f',
              '--force',
              cls=TestbrainOption,
              is_flag=True,
              help_group='Purging Options',
              help="Don't prompt for verification.")
@click.pass_context
@handle_preload_options
def void(ctx, force):
    """Void for debug.

    Warning:

        There's no undo operation for this command.
    """
    ctx.obj.echo(ctx.obj.OK)
