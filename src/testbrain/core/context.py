import os
import pathlib
from typing import Optional, Union

import click

from testbrain.core.crashreporter import inject_excepthook


class TestbrainContext(click.Context):
    _work_dir: Optional[Union[pathlib.Path, str]] = pathlib.Path(".").resolve()

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
