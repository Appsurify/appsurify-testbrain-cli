# import logging
# import typing as t
#
# import click
# from click import Context
#
#
# # from git2testbrain.cli import cli as git2testbrain_cli
# #
# # logger = logging.getLogger(__name__)
# #
# #
# # @click.group(name="testbrain", invoke_without_command=True)
# # @click.pass_context
# # def cli(ctx, *args, **kwargs):
# #     logger.info("INFO")
# #     click.echo("HERE")
# #     click.echo(__file__)
# #
# #
# # cli.add_command(git2testbrain_cli)
# #
# #
# # if __name__ == "__main__":
# #     cli()
#
#
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

    def parse_args(self, ctx: Context, args: t.List[str]) -> t.List[str]:
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


#
#
# @click.group(
#     name="testbrain",
#     cls=TestbrainGroup,
#     default_command="git2testbrain",
#     invoke_without_command=True,
#     add_help_option=False,
#     no_args_is_help=True,
#     context_settings=dict(
#         help_option_names=["-h", "--help"],
#         allow_extra_args=True,
#         allow_interspersed_args=True,
#         ignore_unknown_options=True,
#     ),
# )
# @click.pass_context
# def cli(ctx: click.Context, **kwargs) -> None:
#     click.echo("CLI")
#     if ctx.invoked_subcommand is None:
#         click.echo("CLI -> GIT2TESTBRAIN")
#         ctx.invoke(git2testbrain, *ctx.args)
#
#
# @click.group(
#     name="git2testbrain",
#     cls=TestbrainGroup,
#     default_command="bump",
#     invoke_without_command=True,
#     add_help_option=False,
#     no_args_is_help=True,
#     context_settings=dict(
#         help_option_names=["-h", "--help"],
#         allow_extra_args=True,
#         allow_interspersed_args=True,
#         ignore_unknown_options=True,
#     ),
# )
# @click.pass_context
# def git2testbrain(ctx: click.Context, **kwargs):
#     click.echo("git2testbrain")
#     if ctx.invoked_subcommand is None:
#         click.echo("git2testbrain -> BUMP")
#         ctx.invoke(bump, *ctx.args)
#
#
# @git2testbrain.command(
#     name="bump",
#     no_args_is_help=True,
#     context_settings=dict(
#         help_option_names=["-h", "--help"], ignore_unknown_options=True
#     ),
#     add_help_option=True,
# )
# @click.option("--server", type=str, required=True, help="Server")
# @click.pass_context
# def bump(ctx: click.Context, server: str) -> None:
#     click.echo(f"BUMP {server}")
#
#
# git2testbrain.add_command(bump)
#
# cli.add_command(git2testbrain)
