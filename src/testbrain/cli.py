import click


@click.command()
@click.pass_context
def main(ctx):
    click.echo("Hello")


if __name__ == "__main__":
    main(prog_name="testbrain")
