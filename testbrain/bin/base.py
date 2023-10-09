import json
import numbers
from collections import OrderedDict
from functools import update_wrapper


import click
from click import ParamType

from testbrain._state import get_current_app

from testbrain.signals import user_preload_options
from testbrain.utils import text
from testbrain.utils.log import mlevel
from testbrain.utils.time import maybe_iso8601

class CLIContext:
    """Context Object for the CLI."""

    def __init__(self, app, no_color, workdir, quiet=False):
        """Initialize the CLI context."""
        self.app = app or get_current_app()
        self.no_color = no_color
        self.quiet = quiet
        self.workdir = workdir


def handle_preload_options(f):
    """Extract preload options and return a wrapped callable."""
    def caller(ctx, *args, **kwargs):
        app = ctx.obj.app

        preload_options = [o.name for o in app.user_options.get('preload', [])]

        if preload_options:
            user_options = {
                preload_option: kwargs[preload_option]
                for preload_option in preload_options
            }

            user_preload_options.send(sender=f, app=app, options=user_options)

        return f(ctx, *args, **kwargs)

    return update_wrapper(caller, f)


class TestbrainOption(click.Option):
    """Customized option for Celery."""

    def get_default(self, ctx, *args, **kwargs):
        if self.default_value_from_context:
            self.default = ctx.obj[self.default_value_from_context]
        return super().get_default(ctx, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        """Initialize a Celery option."""
        self.help_group = kwargs.pop('help_group', None)
        self.default_value_from_context = kwargs.pop('default_value_from_context', None)
        super().__init__(*args, **kwargs)


class TestbrainCommand(click.Command):
    """Customized command for Celery."""

    def format_options(self, ctx, formatter):
        """Write all the options into the formatter if they exist."""
        opts = OrderedDict()
        for param in self.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is not None:
                if hasattr(param, 'help_group') and param.help_group:
                    opts.setdefault(str(param.help_group), []).append(rv)
                else:
                    opts.setdefault('Options', []).append(rv)

        for name, opts_group in opts.items():
            with formatter.section(name):
                formatter.write_dl(opts_group)


class TestbrainDaemonCommand(TestbrainCommand):
    """Daemon commands."""

    def __init__(self, *args, **kwargs):
        """Initialize a Celery command with common daemon options."""
        super().__init__(*args, **kwargs)
        self.params.append(TestbrainOption(('-f', '--logfile'), help_group="Daemonization Options",
                           help="Log destination; defaults to stderr"))
        self.params.append(TestbrainOption(('--pidfile',), help_group="Daemonization Options"))
        self.params.append(TestbrainOption(('--uid',), help_group="Daemonization Options"))
        self.params.append(TestbrainOption(('--gid',), help_group="Daemonization Options"))
        self.params.append(TestbrainOption(('--umask',), help_group="Daemonization Options"))
        self.params.append(TestbrainOption(('--executable',), help_group="Daemonization Options"))


class CommaSeparatedList(ParamType):
    """Comma separated list argument."""

    name = "comma separated list"

    def convert(self, value, param, ctx):
        return text.str_to_list(value)


class JsonArray(ParamType):
    """JSON formatted array argument."""

    name = "json array"

    def convert(self, value, param, ctx):
        if isinstance(value, list):
            return value

        try:
            v = json.loads(value)
        except ValueError as e:
            self.fail(str(e))

        if not isinstance(v, list):
            self.fail(f"{value} was not an array")

        return v


class JsonObject(ParamType):
    """JSON formatted object argument."""

    name = "json object"

    def convert(self, value, param, ctx):
        if isinstance(value, dict):
            return value

        try:
            v = json.loads(value)
        except ValueError as e:
            self.fail(str(e))

        if not isinstance(v, dict):
            self.fail(f"{value} was not an object")

        return v


class ISO8601DateTime(ParamType):
    """ISO 8601 Date Time argument."""

    name = "iso-86091"

    def convert(self, value, param, ctx):
        try:
            return maybe_iso8601(value)
        except (TypeError, ValueError) as e:
            self.fail(e)


class ISO8601DateTimeOrFloat(ParamType):
    """ISO 8601 Date Time or float argument."""

    name = "iso-86091 or float"

    def convert(self, value, param, ctx):
        try:
            return float(value)
        except (TypeError, ValueError):
            pass

        try:
            return maybe_iso8601(value)
        except (TypeError, ValueError) as e:
            self.fail(e)


class LogLevel(click.Choice):
    """Log level option."""

    def __init__(self):
        """Initialize the log level option with the relevant choices."""
        super().__init__(('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL'))

    def convert(self, value, param, ctx):
        if isinstance(value, numbers.Integral):
            return value

        value = value.upper()
        value = super().convert(value, param, ctx)
        return mlevel(value)


JSON_ARRAY = JsonArray()
JSON_OBJECT = JsonObject()
ISO8601 = ISO8601DateTime()
ISO8601_OR_FLOAT = ISO8601DateTimeOrFloat()
LOG_LEVEL = LogLevel()
COMMA_SEPARATED_LIST = CommaSeparatedList()