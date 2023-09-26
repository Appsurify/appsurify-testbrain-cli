import os
import time
import click
import pathlib
from typing import Optional, List


cwd = pathlib.Path(".").absolute()

CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    show_default=True
)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--work-dir', '-d',
    required=False,
    type=click.Path(exists=True, dir_okay=True, resolve_path=True),
    envvar='TB_WORK_DIR',
    allow_from_autoenv=True,
    show_envvar=True,
    help="Testbrain CLI Work directory.",
    default=cwd,
    show_default=f"Current dir: {cwd}"
)
@click.option(
    '--url', '-u',
    required=True,
    type=click.STRING,
    envvar='TB_URL',
    allow_from_autoenv=True,
    show_envvar=True,
    help="Testbrain Server URL."
)
@click.option(
    '--token', '-t',
    required=True,
    type=click.STRING,
    envvar='TB_TOKEN',
    allow_from_autoenv=True,
    show_envvar=True,
    help="Testbrain Server Token."
)
@click.option(
    '--project', '-p',
    required=True,
    type=click.STRING,
    envvar='TB_PROJECT',
    allow_from_autoenv=True,
    show_envvar=True,
    help="Testbrain project name."
)
@click.option(
    '--repo-name',
    required=False,
    type=click.STRING,
    envvar='TB_REPO_NAME',
    allow_from_autoenv=True,
    show_envvar=True,
    help="Repository name."
)
@click.option(
    '--repo-dir',
    required=False,
    type=click.Path(exists=True, dir_okay=True, resolve_path=True),
    envvar='TB_REPO_DIR',
    allow_from_autoenv=True,
    show_envvar=True,
    help="Repository directory.",
    default=cwd,
    show_default=f"Current dir: {cwd}"
)
@click.option(
    '--branch', '-b',
    required=True,
    type=click.STRING,
    multiple=True,
    help="Branches."
)
@click.option(
    '--number', '-n',
    required=False,
    type=click.INT,
    help="Enter the number of commits that would be returned.",
    default=100,
    show_default=True
)
@click.option(
    '--start',
    required=False,
    type=click.STRING,
    help="Enter the commit that would be the starter.",
    default='latest',
    show_default=True
)
@click.option(
    '--execution-type',
    required=False,
    type=click.STRING,
    help="Execution modification.",
    default='default',
    show_default=True
)
@click.option(
    '--blame',
    required=False,
    is_flag=True
)
@click.option(
    '--minimize',
    required=False,
    is_flag=True
)
@click.option(
    '--debug',
    required=False,
    is_flag=True
)
@click.pass_context
def main(ctx, **kwargs):
    """First paragraph.

        This is a very long second paragraph and as you
        can see wrapped very early in the source text
        but will be rewrapped to the terminal width in
        the final output.

        \b
        This is
        a paragraph
        without rewrapping.

        And this is a paragraph
        that will be rewrapped again.
    """
    click.echo(f"OK")


if __name__ == '__main__':
    main()
