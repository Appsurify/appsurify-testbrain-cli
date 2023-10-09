import os
import pathlib
import sys
import traceback

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points

import click
import click.exceptions
from click.types import ParamType
from testbrain import VERSION_BANNER
from testbrain.app.utils import find_app
from testbrain.bin.base import TestbrainCommand, TestbrainOption, CLIContext
from testbrain.bin.result import result


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


if sys.version_info >= (3, 10):
    _PLUGINS = entry_points(group='celery.commands')
else:
    try:
        _PLUGINS = entry_points().get('celery.commands', [])
    except AttributeError:
        _PLUGINS = entry_points().select(group='celery.commands')