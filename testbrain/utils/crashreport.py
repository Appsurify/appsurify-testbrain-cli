import os
import sys
import click
from types import TracebackType


def except_hook(
    exc_type: BaseException, exc_value: BaseException, tb: TracebackType
) -> None:
    print(f"============== HERE ==============")
    typer_path = os.path.dirname(__file__)
    click_path = os.path.dirname(click.__file__)
    supress_internal_dir_names = [typer_path, click_path]
    print(supress_internal_dir_names)
    exc = exc_value
    print(exc)
    return