import logging
import os
import pathlib
import sys
import typing as t

import click
from click import Command, Context

import testbrain.cli
from testbrain.cli.core.logging import LOG_LEVELS, configure_logging
from testbrain.contrib.system.crashdump import inject_excepthook

if t.TYPE_CHECKING:
    import typing_extensions as te


logger = logging.getLogger(__name__)


def work_dir_callback(ctx, param, value):  # noqa
    logger.debug(f"Set workdir to {value}")
    os.chdir(value)
    return value


class TestbrainContext(click.Context):
    _work_dir: t.Optional[t.Union[pathlib.Path, str]] = pathlib.Path(".").resolve()

    def __init__(self, *args, **kwargs):
        self.inject_excepthook()
        super().__init__(*args, **kwargs)

    @staticmethod
    def inject_excepthook(
        prog_name: t.Optional[str] = None, quiet: t.Optional[bool] = False
    ) -> None:
        inject_excepthook(
            lambda etype, value, tb, dest: print("Dumped crash report to", dest),
            prog_name=prog_name,
            quiet=quiet,
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
