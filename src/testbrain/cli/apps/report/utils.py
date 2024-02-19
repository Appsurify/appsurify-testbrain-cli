import pathlib
import typing as t

from testbrain.contrib.report.converters import (
    JUnit2TestbrainReportConverter,
    MSTest2JUnitReportConverter,
    MSTest2TestbrainReportConverter,
)
from testbrain.contrib.report.mergers.junit import JUnitReportMerger
from testbrain.contrib.report.models.junit import JUnitTestSuites
from testbrain.contrib.report.models.testbrain import TestbrainTestSuite
from testbrain.contrib.report.parsers import JUnitReportParser, MSTestReportParser


def merge_junit_reports(reports: t.List[JUnitTestSuites]) -> JUnitTestSuites:
    junit_report_merger = JUnitReportMerger.from_reports(reports=reports)
    junit_report_merger.merge()
    junit_report = junit_report_merger.result
    return junit_report


def merge_junit_files(directory: pathlib.Path) -> JUnitTestSuites:
    junit_report_merger = JUnitReportMerger.from_directory(directory=directory)
    junit_report_merger.merge()
    junit_report = junit_report_merger.result
    return junit_report


def convert_mstest_to_junit(infile: pathlib.Path) -> JUnitTestSuites:
    mstest_parser = MSTestReportParser.fromfile(filename=infile)
    mstest_parser.parse()
    mstest_report = mstest_parser.result
    mstest_to_junit_converter = MSTest2JUnitReportConverter(source=mstest_report)
    mstest_to_junit_converter.convert()
    junit_report = mstest_to_junit_converter.result
    return junit_report


def convert_mstest_to_testbrain(infile: pathlib.Path) -> TestbrainTestSuite:
    mstest_parser = MSTestReportParser.fromfile(filename=infile)
    mstest_parser.parse()
    mstest_report = mstest_parser.result
    mstest_to_testbrain_converter = MSTest2TestbrainReportConverter(
        source=mstest_report
    )
    mstest_to_testbrain_converter.convert()
    testbrain_report = mstest_to_testbrain_converter.result
    return testbrain_report


def convert_junit_to_testbrain(infile: pathlib.Path) -> TestbrainTestSuite:
    junit_parser = JUnitReportParser.fromfile(filename=infile)
    junit_parser.parse()
    junit_report = junit_parser.result
    junit_to_testbrain_converter = JUnit2TestbrainReportConverter(source=junit_report)
    junit_to_testbrain_converter.convert()
    testbrain_report = junit_to_testbrain_converter.result
    return testbrain_report
