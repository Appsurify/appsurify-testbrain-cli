#!/usr/bin/env bash
docker run --rm -it \
-v $(pwd)/:/data \
appsurifyinc/appsurify-testbrain-cli:dev git2testbrain --server https://demo.appsurify.com --token $TESTBRAIN_TOKEN --project 001TESTPROJECT --branch development --start latest --number 100
