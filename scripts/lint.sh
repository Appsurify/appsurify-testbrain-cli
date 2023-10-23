#!/usr/bin/env bash
poetry run isort testbrain --profile black --check-only
poetry run isort testbrain --profile black
poetry run black testbrain --check
poetry run flake8 testbrain
