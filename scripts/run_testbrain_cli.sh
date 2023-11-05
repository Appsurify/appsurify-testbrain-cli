#!/usr/bin/env bash
git2testbrain \
--server https://demo.appsurify.com \
--token $TESTBRAIN_TOKEN \
--project 001TESTPROJECT --branch development --start latest --number 100 -l INFO

