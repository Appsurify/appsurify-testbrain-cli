FROM python:3.11.6-alpine as builder
MAINTAINER Artem Demidenko <ar.demidenko@gmail.com>

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYTHONUNBUFFERED=1 \
    GIT_PYTHON_REFRESH='quiet' \
    GIT_DISCOVERY_ACROSS_FILESYSTEM=1

RUN pip install poetry==1.6.1


WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without=dev,test


FROM python:3.11.6-alpine as runtime
MAINTAINER Artem Demidenko <ar.demidenko@gmail.com>

RUN set -ex \
    && apk add --update --no-cache git \
    && git config --global --add safe.directory /data \
    && git config --global merge.renameLimit 999999 \
    && git config --global diff.renameLimit 999999 \
    && git config --global diff.renames 0

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY src /app/src

WORKDIR /data

ENTRYPOINT ["testbrain"]
