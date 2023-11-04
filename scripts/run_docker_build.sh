#!/usr/bin/env bash
poetry build
docker build -f compose/Dockerfile -t appsurifyinc/appsurify-testbrain-cli:dev . --load

docker buildx build --platform linux/arm64 -f compose/Dockerfile -t appsurifyinc/appsurify-testbrain-cli:dev . --load
docker buildx build --platform linux/amd64 -f compose/Dockerfile -t appsurifyinc/appsurify-testbrain-cli:dev . --load
