"""Testbrain Command Line Interface."""
import os
import pathlib
import traceback


try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points

import click
import click.exceptions
from click.types import ParamType
from click_didyoumean import DYMGroup
from click_plugins import with_plugins

from testbrain import VERSION_BANNER
from testbrain.app.utils import find_app
from testbrain.bin.base import TestbrainOption, CLIContext
from testbrain.bin.logtool import logtool
from testbrain.bin.shell import shell
from testbrain.bin.void import void


UNABLE_TO_LOAD_APP_MODULE_NOT_FOUND = click.style("""
Unable to load testbrain application.
The module {0} was not found.""", fg='red')

UNABLE_TO_LOAD_APP_ERROR_OCCURRED = click.style("""
Unable to load testbrain application.
While trying to load the module {0} the following error occurred:
{1}""", fg='red')

UNABLE_TO_LOAD_APP_APP_MISSING = click.style("""
Unable to load testbrain application.
{0}""")


class App(ParamType):
    """Application option."""

    name = "application"

    def convert(self, value, param, ctx):
        try:
            return find_app(value)
        except ModuleNotFoundError as e:
            if e.name != value:
                exc = traceback.format_exc()
                self.fail(
                    UNABLE_TO_LOAD_APP_ERROR_OCCURRED.format(value, exc)
                )
            self.fail(UNABLE_TO_LOAD_APP_MODULE_NOT_FOUND.format(e.name))
        except AttributeError as e:
            attribute_name = e.args[0].capitalize()
            self.fail(UNABLE_TO_LOAD_APP_APP_MISSING.format(attribute_name))
        except Exception:
            exc = traceback.format_exc()
            self.fail(
                UNABLE_TO_LOAD_APP_ERROR_OCCURRED.format(value, exc)
            )


APP = App()


@with_plugins(entry_points().get('testbrain.commands', []))
@click.group(cls=DYMGroup, invoke_without_command=True)
@click.option('-A',
              '--app',
              envvar='APP',
              cls=TestbrainOption,
              type=APP,
              help_group="Global Options")
@click.option('--loader',
              envvar='LOADER',
              cls=TestbrainOption,
              help_group="Global Options")
@click.option('--config',
              envvar='CONFIG_MODULE',
              cls=TestbrainOption,
              help_group="Global Options")
@click.option('--workdir',
              cls=TestbrainOption,
              type=pathlib.Path,
              callback=lambda _, __, wd: os.chdir(wd) if wd else None,
              is_eager=True,
              help_group="Global Options")
@click.option('-C',
              '--no-color',
              envvar='NO_COLOR',
              is_flag=True,
              cls=TestbrainOption,
              help_group="Global Options")
@click.option('-q',
              '--quiet',
              is_flag=True,
              cls=TestbrainOption,
              help_group="Global Options")
@click.option('--version',
              cls=TestbrainOption,
              is_flag=True,
              help_group="Global Options")
@click.pass_context
def testbrain(ctx, app, loader, config, workdir, no_color, quiet, version):
    """Testbrain command entrypoint."""
    if version:
        click.echo(VERSION_BANNER)
        ctx.exit()
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()

    if loader:
        # Default app takes loader from this env (Issue #1066).
        os.environ['TESTBRAIN_LOADER'] = loader
    if config:
        os.environ['TESTBRAIN_CONFIG_MODULE'] = config
    ctx.obj = CLIContext(app=app, no_color=no_color, workdir=workdir, quiet=quiet)

    # User options
    for command in testbrain.commands.values():
        command.params.extend(ctx.obj.app.user_options.get('preload', []))


testbrain.add_command(logtool)
testbrain.add_command(shell)
testbrain.add_command(void)


# Monkey-patch click to display a custom error
# when -A or --app are used as sub-command options instead of as options
# of the global command.

previous_show_implementation = click.exceptions.NoSuchOption.show


WRONG_APP_OPTION_USAGE_MESSAGE = """You are using `{option_name}` as an option of the {info_name} sub-command:
testbrain {info_name} {option_name} testbrainapp <...>

The support for this usage was removed in Testbrain 5.0. Instead you should use `{option_name}` as a global option:
testbrain {option_name} testbrainapp {info_name} <...>"""


def _show(self, file=None):
    if self.option_name in ('-A', '--app'):
        self.ctx.obj.error(
            WRONG_APP_OPTION_USAGE_MESSAGE.format(
                option_name=self.option_name,
                info_name=self.ctx.info_name),
            fg='red'
        )
    previous_show_implementation(self, file=file)


click.exceptions.NoSuchOption.show = _show


def main() -> int:
    """Start testbrain umbrella command.

    This function is the main entrypoint for the CLI.

    :return: The exit code of the CLI.
    """
    return testbrain(auto_envvar_prefix="TESTBRAIN")
