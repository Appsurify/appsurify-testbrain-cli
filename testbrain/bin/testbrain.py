import click
import click.exceptions


@click.group(invoke_without_command=True)
@click.pass_context
def testbrain(ctx):
    ...


# testbrain.add_command(logtool)


def main() -> int:
    """Start testbrain umbrella command.

    This function is the main entrypoint for the CLI.

    :return: The exit code of the CLI.
    """
    return testbrain(auto_envvar_prefix="TESTBRAIN")
