import pathlib
import typing as t

import click


class TestbrainContext(click.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TestbrainCommand(click.Command):
    context_class = TestbrainContext
    default_context_settings = {"help_option_names": ["-h", "--help"]}

    def __init__(self, *args, **kwargs):
        context_settings = kwargs.pop("context_settings", {})
        context_settings.update(self.default_context_settings)
        kwargs["context_settings"] = context_settings
        super(TestbrainCommand, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

    def invoke(self, ctx) -> t.Any:
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
