FROM python:3.11.6-slim-bullseye
MAINTAINER Artem Demidenko <ar.demidenko@gmail.com>

ARG RELEASE

ENV PIP_DEFAULT_TIMEOUT=100 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    GIT_PYTHON_REFRESH='quiet' \
    GIT_DISCOVERY_ACROSS_FILESYSTEM=1

RUN set -ex \
    # Create a non-root user
    && addgroup --system --gid 1001 testbrain \
    && adduser --system --uid 1001 --gid 1001 --no-create-home testbrain \
    # Upgrade the package index and install security upgrades
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install git -y \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data  \
    && chown -R testbrain:testbrain /data

RUN pip install --upgrade appsurify-testbrain-cli==$RELEASE

WORKDIR /data
ENTRYPOINT ["testbrain"]
