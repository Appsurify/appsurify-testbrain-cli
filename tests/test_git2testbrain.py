from click.testing import CliRunner
from testbrain.git2testbrain import main


def test_main_help():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0


def test_main_no_args():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 2
    assert """Error: Missing option '--url' / '-u'.\n""" in result.output


def test_main_simple():
    runner = CliRunner()
    result = runner.invoke(main, ['--url', 'demo'])
    assert result.exit_code == 2
    result = runner.invoke(main, [
        '--url', 'demo',
        '--token', ' XXXX',
        '--project', ' QA',
        '--branch', ' main',
        '--branch', ' dev',
    ])
    assert result.exit_code == 0
