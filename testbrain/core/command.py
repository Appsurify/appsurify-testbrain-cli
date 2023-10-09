import pathlib
import typing as t

import click
from click import Context

from testbrain.core.context import TestbrainContext
from testbrain.core import log


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
                type=click.Choice(log.LOG_LEVELS, case_sensitive=False),
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

    def invoke(self, ctx, *args, **kwargs) -> t.Any:
        log.configure_logging(ctx.params.get("loglevel"), ctx.params.get("logfile"))
        return super().invoke(ctx)

    def make_context(
        self,
        info_name: t.Optional[str],
        args: t.List[str],
        parent: t.Optional[Context] = None,
        **extra: t.Any,
    ) -> Context:
        return super().make_context(info_name, args, parent, **extra)


# _original_except_hook = sys.excepthook
# _typer_developer_exception_attr_name = "__typer_developer_exception__"
#
# def except_hook(
#     exc_type: Type[BaseException], exc_value: BaseException, tb: TracebackType
# ) -> None:
#     exception_config: Union[DeveloperExceptionConfig, None] = getattr(
#         exc_value, _typer_developer_exception_attr_name, None
#     )
#     standard_traceback = os.getenv("_TYPER_STANDARD_TRACEBACK")
#     if (
#         standard_traceback
#         or not exception_config
#         or not exception_config.pretty_exceptions_enable
#     ):
#         _original_except_hook(exc_type, exc_value, tb)
#         return
#     typer_path = os.path.dirname(__file__)
#     click_path = os.path.dirname(click.__file__)
#     supress_internal_dir_names = [typer_path, click_path]
#     exc = exc_value
#     if rich:
#         rich_tb = Traceback.from_exception(
#             type(exc),
#             exc,
#             exc.__traceback__,
#             show_locals=exception_config.pretty_exceptions_show_locals,
#             suppress=supress_internal_dir_names,
#         )
#         console_stderr.print(rich_tb)
#         return
#     tb_exc = traceback.TracebackException.from_exception(exc)
#     stack: List[FrameSummary] = []
#     for frame in tb_exc.stack:
#         if any(
#             [frame.filename.startswith(path) for path in supress_internal_dir_names]
#         ):
#             if not exception_config.pretty_exceptions_short:
#                 # Hide the line for internal libraries, Typer and Click
#                 stack.append(
#                     traceback.FrameSummary(
#                         filename=frame.filename,
#                         lineno=frame.lineno,
#                         name=frame.name,
#                         line="",
#                     )
#                 )
#         else:
#             stack.append(frame)
#     # Type ignore ref: https://github.com/python/typeshed/pull/8244
#     final_stack_summary = StackSummary.from_list(stack)  # type: ignore
#     tb_exc.stack = final_stack_summary
#     for line in tb_exc.format():
#         print(line, file=sys.stderr)
#     return
#
#
#
# class TestbrainCommand(click.Command):
#
#     def __call__(self, *args: Any, **kwargs: Any) -> Any:
#         if sys.excepthook != except_hook:
#             sys.excepthook = except_hook
#         try:
#             return get_command(self)(*args, **kwargs)
#         except Exception as e:
#             # Set a custom attribute to tell the hook to show nice exceptions for user
#             # code. An alternative/first implementation was a custom exception with
#             # raise custom_exc from e
#             # but that means the last error shown is the custom exception, not the
#             # actual error. This trick improves developer experience by showing the
#             # actual error last.
#             setattr(
#                 e,
#                 _typer_developer_exception_attr_name,
#                 DeveloperExceptionConfig(
#                     pretty_exceptions_enable=self.pretty_exceptions_enable,
#                     pretty_exceptions_show_locals=self.pretty_exceptions_show_locals,
#                     pretty_exceptions_short=self.pretty_exceptions_short,
#                 ),
#             )
#             raise e
