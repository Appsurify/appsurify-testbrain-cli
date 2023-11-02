import logging
import os
import pathlib
import typing as t

import click

from .utils.crasher import inject_excepthook
from .utils.logging import LOG_LEVELS, configure_logging

logger = logging.getLogger(__name__)


class TestbrainContext(click.Context):
    _work_dir: t.Optional[t.Union[pathlib.Path, str]] = pathlib.Path(".").resolve()

    def __init__(self, *args, **kwargs):
        inject_excepthook(
            lambda etype, value, tb, dest: print("Dumped crash report to", dest)
        )
        super().__init__(*args, **kwargs)

    @property
    def work_dir(self):
        return self._work_dir

    @work_dir.setter
    def work_dir(self, value):
        os.chdir(value)
        self._work_dir = value


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

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

    def invoke(self, ctx) -> t.Any:
        configure_logging(
            level=ctx.params.get("loglevel"), file=ctx.params.get("logfile")
        )
        rv = super().invoke(ctx)
        return rv

    def make_context(
        self,
        info_name: t.Optional[str],
        args: t.List[str],
        parent: t.Optional[click.Context] = None,
        **extra: t.Any,
    ) -> click.Context:
        return super().make_context(info_name, args, parent, **extra)


class TestbrainGroup(click.Group):
    default_command = None

    def __init__(
        self,
        name: t.Optional[str] = None,
        commands: t.Optional[
            t.Union[t.MutableMapping[str, click.Command], t.Sequence[click.Command]]
        ] = None,
        **attrs: t.Any,
    ) -> None:
        self.default_command = attrs.pop("default_command", None)
        super().__init__(name, **attrs)

    def parse_args(self, ctx: click.Context, args: t.List[str]) -> t.List[str]:
        help_options = ctx.help_option_names
        parent = ctx.parent
        parent_cmd = None
        if parent:
            parent_cmd = parent.command
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            if self.get_command(ctx, self.default_command) is not None:
                cmd = self.get_command(ctx, self.default_command)
                if hasattr(cmd, "default_command"):
                    sub = cmd.get_command(ctx, cmd.default_command)
                    click.echo(sub.get_help(ctx), color=ctx.color)
                    ctx.exit()
                else:
                    click.echo(cmd.get_help(ctx), color=ctx.color)
                    ctx.exit()
            else:
                click.echo(ctx.get_help(), color=ctx.color)
                ctx.exit()

        elif set(help_options).intersection(args):
            if parent_cmd:
                current_cmd = ctx.command
                cmd = current_cmd
                if self.get_command(ctx, self.default_command) is not None:
                    cmd = self.get_command(ctx, self.default_command)

                if hasattr(cmd, "default_command"):
                    sub = cmd.get_command(ctx, cmd.default_command)
                    click.echo(sub.get_help(ctx), color=ctx.color)
                    ctx.exit()
                    # formatter = ctx.make_formatter()
                    # msg = sub.format_options(ctx, formatter)
                    # msg = formatter.getvalue().rstrip("\n")
                    # click.echo(msg, color=ctx.color)
                else:
                    # click.echo(cmd.get_help(ctx), color=ctx.color)
                    formatter = ctx.make_formatter()
                    cmd.format_usage(ctx, formatter)
                    cmd.format_options(ctx, formatter)
                    cmd.format_epilog(ctx, formatter)

                    msg = formatter.getvalue().rstrip("\n")
                    click.echo(msg, color=ctx.color)

                formatter = ctx.make_formatter()
                current_cmd.format_commands(ctx, formatter)
                msg = formatter.getvalue().rstrip("\n")
                click.echo(msg, color=ctx.color)

                ctx.exit()
            # pa0 = super().parse_args(ctx, args)
            # click.echo(ctx.get_help(), color=ctx.color)
            # ctx.exit()
        pa = super().parse_args(ctx, args)
        return pa
