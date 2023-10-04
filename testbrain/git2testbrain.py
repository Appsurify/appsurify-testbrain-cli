import os
import time
import typing
import typer
import pathlib
from typing import Optional, List
from typing_extensions import Annotated
from urllib.parse import urlparse


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], show_default=True)


app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command(name="push")
def push(
    ctx: typer.Context,
    url: Annotated[str, typer.Option()] = None,
    token: Annotated[str, typer.Option()] = None,
    project: Annotated[str, typer.Option()] = None,
    work_dir: Annotated[
        Optional[pathlib.Path],
        typer.Option(
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            resolve_path=True,
            is_eager=True,
        ),
    ] = pathlib.Path(".").absolute(),
    repo_name: Annotated[str, typer.Option()] = None,
    repo_dir: Annotated[
        Optional[pathlib.Path],
        typer.Option(
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            resolve_path=True,
            is_eager=True,
        ),
    ] = pathlib.Path(".").resolve(),
    # branches: Annotated[
    #     Optional[List[str]], typer.Option(
    #         '--branch', '-b'
    #     )
    # ] = ('main', ),
    branch: Annotated[str, typer.Option()] = None,
    number: Annotated[int, typer.Option(min=1)] = 1,
    start: Annotated[str, typer.Option()] = "latest",
    blame: Annotated[bool, typer.Option(is_flag=True)] = False,
    minimize: Annotated[bool, typer.Option(is_flag=True)] = False,
    debug: Annotated[bool, typer.Option(is_flag=True)] = False,
):
    # print(f"OK")
    # for k, v in ctx.params.items():
    #     print(f"\t{k.upper()}: {v}")
    from testbrain.repository.git import Git

    git = Git(repo_dir=repo_dir)
    git.send_hook(branch=branch, start=start, number=number, blame=blame)
    print("OK")


if __name__ == "__main__":
    app()
