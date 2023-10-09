import typer

from testbrain.bin.git2testbrain import git2testbrain


APP_NAME = "testbrain-cli"
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], show_default=True)


app = typer.Typer(
    name=APP_NAME, context_settings=CONTEXT_SETTINGS, no_args_is_help=True
)

app.command()(git2testbrain)


if __name__ == "__main__":
    app()
