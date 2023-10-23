FROM python:3.11-slim-bullseye
MAINTAINER Artem Demidenko <ar.demidenko@gmail.com>

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
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
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data \
    && git config --global --add safe.directory /data

COPY dist/ /tmp

RUN pip install /tmp/*.whl && rm -rf /tmp/*.whl

WORKDIR /data
ENTRYPOINT ["testbrain"]
