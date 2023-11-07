import logging
import os
import pathlib
import sys
import typing as t

import click
from click import Command, Context

from testbrain import pkg_name, pkg_version
from testbrain.utils.crasher import inject_excepthook
from testbrain.utils.logging import LOG_LEVELS, configure_logging

if t.TYPE_CHECKING:
    import typing_extensions as te


logger = logging.getLogger(__name__)


def work_dir_callback(ctx, param, value):
    logger.debug(f"Set workdir to {value}")
    os.chdir(value)
    return value


class TestbrainContext(click.Context):
    _work_dir: t.Optional[t.Union[pathlib.Path, str]] = pathlib.Path(".").resolve()

    def __init__(self, *args, **kwargs):
        self.inject_excepthook()
        super().__init__(*args, **kwargs)

    def inject_excepthook(self, quiet: bool = False) -> None:
        inject_excepthook(
            lambda etype, value, tb, dest: print("Dumped crash report to", dest)
        )

    @property
    def work_dir(self):
        return self._work_dir

    @work_dir.setter
    def work_dir(self, value):
        os.chdir(value)
        self._work_dir = value

    def exit(self, code: int = 0) -> "te.NoReturn":
        if self.params.get("quiet", False):
            super().exit(0)
        super().exit(code)


class TestbrainCommand(click.Command):
    context_class = TestbrainContext
    default_context_settings = {"help_option_names": ["-h", "--help"]}

    def __init__(self, *args, **kwargs):
        context_settings = kwargs.pop("context_settings", {})
        context_settings.update(self.default_context_settings)
        kwargs["context_settings"] = context_settings
        super(TestbrainCommand, self).__init__(*args, **kwargs)
        self.params.append(
            click.Option(
                ["--work-dir"],
                metavar="<dir>",
                type=click.Path(dir_okay=True, resolve_path=True),
                default=pathlib.Path("."),
                callback=work_dir_callback,
                is_eager=True,
                show_default=True,
                envvar="TESTBRAIN_WORK_DIR",
                show_envvar=True,
                help="Enter the testbrain script working directory. "
                "If not specified, the current working directory "
                "will be used.",
            )
        )
        self.params.append(
            click.Option(
                ["--loglevel", "-l"],
                type=click.Choice(LOG_LEVELS, case_sensitive=False),
                default="INFO",
                show_default=True,
                help="Logging level",
            )
        )
        self.params.append(
            click.Option(
                ["--logfile"],
                type=pathlib.Path,
                required=False,
                default=None,
                show_default="stderr",
                help="Log filename",
            )
        )
        self.params.append(
            click.Option(
                ["--quiet"],
                type=bool,
                default=False,
                show_default=True,
                is_flag=True,
                help="Quiet mode... everytime exit with 0",
            )
        )

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return super().__call__(args, kwargs)

    def invoke(self, ctx: "TestbrainContext") -> t.Any:
        configure_logging(
            level=ctx.params.get("loglevel"), file=ctx.params.get("logfile")
        )
        ctx.inject_excepthook(quiet=ctx.params.get("quiet", False))
        ctx.work_dir = ctx.params.get("work_dir", pathlib.Path("."))
        rv = super().invoke(ctx)
        return rv

    def make_context(
        self,
        info_name: t.Optional[str],
        args: t.List[str],
        parent: t.Optional[click.Context] = None,
        **extra: t.Any,
    ) -> click.Context:
        ctx = super().make_context(info_name, args, parent, **extra)
        return ctx


class TestbrainGroup(click.Group):
    command_class = TestbrainCommand
    context_class = TestbrainContext
    default_context_settings = {"help_option_names": ["-h", "--help"]}

    def __init__(
        self,
        name: t.Optional[str] = None,
        commands: t.Optional[
            t.Union[t.MutableMapping[str, click.Command], t.Sequence[click.Command]]
        ] = None,
        **attrs: t.Any,
    ) -> None:
        self.ignore_unknown_options = attrs.pop("ignore_unknown_options", True)
        self.default_cmd_name = attrs.pop("default", None)
        self.default_if_no_args = attrs.pop("default_if_no_args", False)

        context_settings = attrs.pop("context_settings", {})
        context_settings.update(self.default_context_settings)
        attrs["context_settings"] = context_settings

        super().__init__(name, **attrs)

    def set_default_command(self, command):
        """Sets a command function as the default command."""
        cmd_name = command.name
        self.add_command(command)
        self.default_cmd_name = cmd_name

    def parse_args(self, ctx, args):
        if not args and self.default_if_no_args and self.default_cmd_name is not None:
            args.insert(0, self.default_cmd_name)
        return super().parse_args(ctx, args)

    def get_command(self, ctx, cmd_name):
        if cmd_name not in self.commands:
            # No command name matched.
            ctx.arg0 = cmd_name
            cmd_name = self.default_cmd_name
        return super().get_command(ctx, cmd_name)

    def resolve_command(self, ctx, args):
        base = super()
        cmd_name, cmd, args = base.resolve_command(ctx, args)
        if hasattr(ctx, "arg0"):
            args.insert(0, ctx.arg0)
            cmd_name = cmd.name
        return cmd_name, cmd, args

    def format_commands(self, ctx, formatter):
        formatter = TestbrainCommandFormatter(self, formatter, mark="*")
        return super().format_commands(ctx, formatter)

    def command(self, *args, **kwargs):
        default = kwargs.pop("default", False)
        decorator = super().command(*args, **kwargs)
        if not default:
            return decorator

        def _decorator(f):
            cmd = decorator(f)
            # if self.default_cmd_name is not None:
            self.set_default_command(cmd)
            return cmd

        return _decorator

    def add_command(
        self,
        cmd: t.Union[t.Callable, Command],
        name: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> None:
        default = kwargs.pop("default", False)
        if default:
            self.set_default_command(cmd)
        else:
            super().add_command(cmd, name)


class TestbrainCommandFormatter(click.formatting.HelpFormatter):
    """Wraps a formatter to mark a default command."""

    def __init__(self, group, formatter, mark="*"):
        self.group = group
        self.formatter = formatter
        self.mark = mark
        super().__init__()

    def __getattr__(self, attr):
        return getattr(self.formatter, attr)

    def write_dl(self, rows, *args, **kwargs):
        rows_ = []
        for cmd_name, help in rows:
            if cmd_name == self.group.default_cmd_name:
                rows_.insert(0, (cmd_name + " " + self.mark, help))
            else:
                rows_.append((cmd_name, help))

        rows_.insert(0, ("Commands:", ""))
        return self.formatter.write_dl(rows_, *args, **kwargs)
