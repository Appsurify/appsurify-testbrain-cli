import pathlib
import typing as t

import click
from click import Context

from testbrain.core.context import TestbrainContext
from testbrain.core.log import LOG_LEVELS, configure_logging


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
                default="WARNING",
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
        configure_logging(ctx.params.get("loglevel"), ctx.params.get("logfile"))
        return super().invoke(ctx)

    def make_context(
        self,
        info_name: t.Optional[str],
        args: t.List[str],
        parent: t.Optional[Context] = None,
        **extra: t.Any,
    ) -> Context:
        return super().make_context(info_name, args, parent, **extra)


class TestbrainGroup(click.Group):
    command_class = TestbrainCommand

    def command(self, *args, **kwargs):
        """A shortcut decorator for declaring and attaching a command to
        the group.  This takes the same arguments as :func:`command` but
        immediately registers the created command with this instance by
        calling into :meth:`add_command`.
        """
        from click.decorators import command

        kwargs["cls"] = TestbrainCommand

        def decorator(f):
            cmd = command(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator

    def group(self, *args, **kwargs):
        """A shortcut decorator for declaring and attaching a group to
        the group.  This takes the same arguments as :func:`group` but
        immediately registers the created command with this instance by
        calling into :meth:`add_command`.
        """
        from click.decorators import group

        kwargs["cls"] = TestbrainGroup

        def decorator(f):
            cmd = group(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator
