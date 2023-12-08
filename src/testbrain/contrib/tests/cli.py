import logging
import os
import pathlib
import sys

import click

from testbrain.core import TestbrainCommand, TestbrainContext, TestbrainGroup

logger = logging.getLogger(__name__)


@click.group(
    name="tests",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
    default=True,
)
@click.version_option("unknown")
@click.pass_context
def app(ctx: TestbrainContext, **kwargs):
    logger.debug(f"testbrain.tests run with {ctx} {kwargs}")


runtestswithappsurify = app
testimportappsurify = app


if __name__ == "__main__":
    logger.name = "testbrain.tests.cli"
    app(prog_name="tests")
