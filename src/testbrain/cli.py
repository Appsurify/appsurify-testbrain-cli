import logging

import click

# from testbrain import TestbrainContext, TestbrainCommand
# from testbrain.client import HTTPClient


logger = logging.getLogger(__name__)


# @click.group(name="testbrain", invoke_without_command=True)
# @click.pass_context
# def main(ctx: TestbrainContext):
#     # configure_logging(level="DEBUG", file=".crashdumps/testbrain.log")
#     # named_logger.debug("named_logger: Hello DEBUG")
#     # named_logger.info("named_logger: Hello INFO")
#     # named_logger.warning("named_logger: Hello WARNING")
#     if ctx.invoked_subcommand is None:
#         logger.debug("logger: Hello DEBUG")
#         logger.info("logger: Hello INFO")
#         logger.warning("logger: Hello WARNING")
#
#         click.echo("CLICK ECHO: Hello")
#
#
@click.command(name="test")
@click.pass_context
def test(ctx):
    logger.debug("logger: Test DEBUG")
    logger.info("logger: Test INFO")
    logger.warning("logger: Test WARNING")

    click.echo("CLICK ECHO: Test")


def callback(*args, **kwargs):
    logger.debug("logger: Hello DEBUG")
    logger.info("logger: Hello INFO")
    logger.warning("logger: Hello WARNING")


@click.group(
    name="testbrain",
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.pass_context
def application(ctx, *args, **kwargs):
    from testbrain.utils.logging import configure_logging

    configure_logging(level="DEBUG")
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()

    logger.debug("logger: Hello DEBUG")
    logger.info("logger: Hello INFO")
    logger.warning("logger: Hello WARNING")


if __name__ == "__main__":
    application(prog_name="testbrain")
