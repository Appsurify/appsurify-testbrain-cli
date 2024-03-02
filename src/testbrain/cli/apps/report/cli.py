import enum
import logging
import pathlib

import click

from testbrain.cli.apps.report.client import ReportClient
from testbrain.cli.apps.report.utils import (
    convert_mstest_to_junit,
    merge_junit_files,
    merge_junit_reports,
)
from testbrain.cli.core.command import TestbrainCommand, TestbrainGroup
from testbrain.cli.core.context import TestbrainContext
from testbrain.contrib.report.utils import string_to_fileobject

logger = logging.getLogger(__name__)


REPORT_FORMATS = {"JUNIT": "JUNIT", "MSTEST": "MSTEST", "TESTBRAIN": "TESTBRAIN"}
REPORT_FORMATS.setdefault("JUNIT", "JUNIT")


@click.group(
    name="report",
    cls=TestbrainGroup,
    default_if_no_args=True,
    no_args_is_help=True,
)
@click.pass_context
def report(ctx: TestbrainContext, **kwargs):
    logger.debug(f"Report running with {ctx} {kwargs}")


@report.command("mstest2junit", cls=TestbrainCommand)
@click.option(
    "--in-path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True),
    default=pathlib.Path(".").resolve(),
    show_default=True,
    required=True,
)
@click.option(
    "--out-path",
    type=click.Path(exists=False, file_okay=True, dir_okay=True, readable=True),
    default=None,
    show_default=True,
    required=False,
)
@click.option(
    "--merge",
    show_default="False",
    type=bool,
    default=False,
    is_flag=True,
    help="Merge all report files into a single?",
)
@click.pass_context
def mstest_to_junit(ctx: TestbrainContext, in_path, out_path, merge):
    if in_path == out_path:
        logger.warning(
            "Input path and output path equal... may be conflict and overwrite issue."
        )

    in_path = pathlib.Path(in_path).resolve()

    if out_path is None:
        out_path = in_path if in_path.is_dir() else in_path.parent
        out_path = out_path.joinpath("out")

    out_path = pathlib.Path(out_path).resolve()

    in_filename = None

    out_filename = None

    if in_path.exists():
        # if in_path.is_dir():
        #     in_directory = in_path
        # else:
        #     in_filename = in_path.name
        #     in_directory = in_path.parent
        if not in_path.is_dir():
            in_filename = in_path.name
    else:
        logger.error(f"Input path {in_path} does not exists")
        ctx.exit(127)

    if out_path.exists():
        if out_path.is_dir():
            out_directory = out_path
        else:
            out_filename = out_path.name
            out_directory = out_path.parent
    else:
        if not out_path.suffix:
            out_directory = out_path
            out_directory.mkdir(parents=True, exist_ok=True)
        else:
            out_filename = out_path.name
            out_directory = out_path.parent
            out_directory.mkdir(parents=True, exist_ok=True)

    if not out_filename and merge:
        out_filename = "junit-merged-report.xml"

    if (not in_filename and out_filename) and not merge:
        logger.error("Output path is not a directory. Use --merge or set directory.")
        ctx.exit(127)

    if in_path.is_file():
        if not out_filename:
            out_path = out_directory.joinpath(in_filename).with_suffix(".xml")
        try:
            junit_report = convert_mstest_to_junit(in_path)
            out_path.write_text(junit_report.model_dump_xml())
            logger.info(f"Saved junit report to {out_path}")
            ctx.exit(0)
        except ValueError:
            logger.critical(f"Could not parse {in_path}")
            ctx.exit(127)

    elif in_path.is_dir():
        reports = []
        for infile in in_path.iterdir():
            if not infile.is_file():
                continue
            if not out_filename:
                out_path = out_directory.joinpath(infile.name).with_suffix(".xml")
            try:
                junit_report = convert_mstest_to_junit(infile)
                if merge:
                    reports.append(junit_report)
                    continue
                out_path.write_text(junit_report.model_dump_xml())
                logger.info(f"Saved junit report to {out_path}")
            except ValueError:
                logger.critical(f"Could not parse {infile}")
                continue

        if merge:
            junit_report = merge_junit_reports(reports=reports)

            out_path = out_directory.joinpath(out_filename).with_suffix(".xml")
            out_path.write_text(junit_report.model_dump_xml())

            logger.info(f"Saved junit report to {out_path}")

        ctx.exit(0)


@report.command("merge-junit", cls=TestbrainCommand)
@click.option(
    "--in-dir",
    type=click.Path(exists=True, dir_okay=True, readable=True),
    default=None,
    show_default=False,
    required=True,
)
@click.option(
    "--out-file",
    type=click.Path(exists=False),
    default=None,
    show_default=False,
    required=False,
)
@click.pass_context
def merge_junit(ctx: TestbrainContext, in_dir, out_file):
    in_dir = pathlib.Path(in_dir).resolve()

    if not in_dir.is_dir():
        logger.error("Please enter path to a directory with reports")
        ctx.exit(127)

    out_dir = in_dir.joinpath("out")

    if out_file is None:
        out_file = out_dir.joinpath("junit-merged-report.xml")
    else:
        out_file = pathlib.Path(out_file).resolve()
        if out_file.suffix:
            out_dir = out_file.parent
        else:
            out_dir = out_file
            out_file = out_dir.joinpath("junit-merged-report.xml")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_file.with_suffix(".xml")

    junit_report = merge_junit_files(directory=in_dir)
    out_file.write_text(junit_report.model_dump_xml())
    logger.info(f"Saved junit report to {out_file}")
    ctx.exit(0)


@report.command("push", cls=TestbrainCommand, default=True)
@click.option(
    "--server",
    "--url",
    metavar="<url>",
    required=True,
    type=str,
    envvar="TESTBRAIN_SERVER",
    show_envvar=True,
    help="Enter your testbrain server instance url.",
)
@click.option(
    "--token",
    "--apikey",
    metavar="<token>",
    required=True,
    type=str,
    envvar="TESTBRAIN_TOKEN",
    show_envvar=True,
    help="Enter your testbrain server instance token.",
)
@click.option(
    "--project",
    metavar="<name>",
    required=True,
    type=str,
    envvar="TESTBRAIN_PROJECT",
    show_envvar=True,
    help="Enter your testbrain project name.",
)
@click.option(
    "--testsuite",
    metavar="<name>",
    required=True,
    type=str,
    envvar="TESTBRAIN_TESTSUITE",
    show_envvar=True,
    help="Enter your testbrain testsuite name.",
)
@click.option(
    "--branch",
    metavar="<name>",
    show_default="",
    type=str,
    required=False,
    envvar="TESTBRAIN_BRANCH",
    show_envvar=True,
    help="Enter the explicit branch to process commits. If not "
    "specified, use empty.",
)
@click.option(
    "--commit",
    metavar="<sha>",
    show_default="latest (HEAD)",
    type=str,
    required=True,
    envvar="TESTBRAIN_COMMIT",
    show_envvar=True,
    help="Enter the commit sha.",
)
@click.option(
    "--report-type",
    type=click.Choice(REPORT_FORMATS, case_sensitive=False),
    default="junit",
    show_default=True,
    required=True,
    help="Enter the report type.",
)
@click.option(
    "--import-type",
    metavar="<type>",
    show_default="prioritized",
    type=str,
    required=True,
    help="Enter the import type. (default: prioritized)",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True),
    default=pathlib.Path("."),
    show_default=True,
)
@click.option(
    "--merge",
    show_default="False",
    type=bool,
    default=False,
    is_flag=True,
    help="Merge all report files into a single?",
)
@click.option(
    "--multi",
    show_default="False",
    type=bool,
    default=False,
    is_flag=True,
    help="All report files into a single request",
)
@click.pass_context
def push(
    ctx: TestbrainContext,
    server,
    token,
    project,
    testsuite,
    branch,
    commit,
    report_type,
    import_type,
    path,
    merge,
    multi,
    **kwargs,
):
    path = pathlib.Path(path).resolve()

    _params = ctx.params.copy()

    logger.debug(f"Running report push with params {_params} {kwargs}")

    if report_type != "JUNIT" and merge:
        logger.critical("Only JUNIT report supported merging")
        ctx.exit(127)

    reports = []

    if path.is_dir() and not merge:
        for filename in path.iterdir():
            if not filename.is_file():
                continue
            report = string_to_fileobject(filename.read_text(), filename=filename.name)
            reports.append(report)
    elif path.is_dir() and merge:
        if report_type != "JUNIT":
            logger.warning("Merge supported only for JUNIT reports")
            ctx.exit(127)
        report_content = merge_junit_files(path)
        report = string_to_fileobject(
            report_content.model_dump_xml(), filename="merged-junit-report.xml"
        )
        reports.append(report)
    elif path.is_file():
        report = string_to_fileobject(path.read_text(), filename=path.name)
        reports.append(report)

    logger.info(f"Start pushing report(s) [{len(reports)}] ... ")
    client = ReportClient(server=server, token=token)
    if not multi:
        for report in reports:
            logger.info(f"Pushing report {report.name}")
            response = client.push_report(
                project=project,
                testsuite=testsuite,
                branch=branch,
                commit=commit,
                report_type=report_type,
                import_type=import_type,
                report=report,
            )
            if response:
                logger.info(f"Pushed report successfully: {response}")
            else:
                logger.error(f"Something wrong... {report.name}")
    else:
        response = client.push_report(
            project=project,
            testsuite=testsuite,
            branch=branch,
            commit=commit,
            report_type=report_type,
            import_type=import_type,
            reports=reports,
        )
        if response:
            logger.info(f"Pushed report successfully: {response}")
        else:
            logger.error("Something wrong... check logs or crashdump")
            ctx.exit(127)
