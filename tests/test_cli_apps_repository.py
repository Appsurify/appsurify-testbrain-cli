from click.testing import CliRunner
from testbrain.cli.cli import app
from testbrain.cli.apps.repository.cli import repository


def test_general_repository_push_help():
    runner = CliRunner()
    result = runner.invoke(app, ["repository", "git", "push", "--help"])
    assert result.exit_code == 0
