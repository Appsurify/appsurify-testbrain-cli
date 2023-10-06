import os
import time
import typing
import typer
import pathlib
from typing import Optional, List
from typing_extensions import Annotated
from testbrain.git2testbrain import Git2TestBrainController


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], show_default=True)


app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command(name="push")
def push(
    ctx: typer.Context,
    server: Annotated[
        str,
        typer.Option(
            envvar="TESTBRAIN_SERVER", help="Enter your testbrain server instance url."
        ),
    ],
    token: Annotated[
        str,
        typer.Option(
            envvar="TESTBRAIN_TOKEN", help="Enter your testbrain server instance token."
        ),
    ],
    project: Annotated[
        str,
        typer.Option(
            envvar="TESTBRAIN_PROJECT", help="Enter your testbrain project name."
        ),
    ],
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
            envvar="TESTBRAIN_WORK_DIR",
            help="Enter the testbrain-cli script working directory. If not specified, the current working directory will be used.",
        ),
    ] = pathlib.Path("."),
    repo_name: Annotated[
        str,
        typer.Option(
            envvar="TESTBRAIN_REPO_NAME",
            help="Define repository name. If not specified, it will be automatically taken from the GitRepository repository.",
        ),
    ] = None,
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
            envvar="TESTBRAIN_REPO_DIR",
            help="Enter the git repository directory. If not specified, the current working directory will be used.",
        ),
    ] = pathlib.Path("."),
    branch: Annotated[
        str,
        typer.Option(
            envvar="TESTBRAIN_BRANCH",
            help="Enter the explicit branch to process commits. If not specified, use current active branch.",
        ),
    ] = None,
    number: Annotated[
        int,
        typer.Option(
            envvar="TESTBRAIN_NUMBER_OF_COMMITS",
            help="Enter the number of commits to process.",
        ),
    ] = 1,
    start: Annotated[
        str,
        typer.Option(
            envvar="TESTBRAIN_START_COMMIT",
            help="Enter the commit that should be starter. If not specified, it will be used 'latest' commit.",
        ),
    ] = "latest",
    blame: Annotated[
        bool,
        typer.Option(
            is_flag=True, help="Choose to commit revision of each line or not."
        ),
    ] = False,
    minimize: Annotated[bool, typer.Option(is_flag=True)] = False,
    debug: Annotated[bool, typer.Option(is_flag=True)] = False,
    verbose: Annotated[
        Optional[int],
        typer.Option("--verbose", "-v", show_choices=True, count=True, min=0, max=3),
    ] = 0,
):
    # client = Git2TestbrainAPIClient(server=server, token=token)
    # repository = GitRepository(repo_dir=repo_dir)
    # service = Git2TestbrainService(repository=repository, client=client)
    # git.send_hook(branch=branch, start=start, number=number, blame=blame)

    app = Git2TestBrainController(
        server=server,
        token=token,
        project=project,
        repo_dir=repo_dir,
        repo_name=repo_name,
    )
    changes_result = app.capture_changes(
        branch=branch, commit=start, number=number, blame=blame
    )
    delivery_result = app.deliver_changes()
    print("OK")


if __name__ == "__main__":
    app()
