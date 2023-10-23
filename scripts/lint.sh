#!/usr/bin/env bash
poetry run isort src --profile black
poetry run isort src --profile black --check-only
poetry run black src --check
poetry run flake8 src
