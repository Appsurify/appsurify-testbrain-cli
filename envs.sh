#!/usr/bin/env bash

# Bumpversion
bump2version --current-version 2023.9.6 --new-version 2023.9.9 patch --allow-dirty

poetry env use /Users/whenessel/Library/Caches/pypoetry/virtualenvs/appsurify-testbrain-cli-V5MLWMnE-py3.7/bin/python
poetry install
poetry run pytest
poetry env use /Users/whenessel/Library/Caches/pypoetry/virtualenvs/appsurify-testbrain-cli-V5MLWMnE-py3.8/bin/python
poetry install
poetry run pytest
poetry env use /Users/whenessel/Library/Caches/pypoetry/virtualenvs/appsurify-testbrain-cli-V5MLWMnE-py3.11/bin/python
poetry install
poetry run pytest



# --server https://demo.appsurify.com --token MTU6ZW9FZUxhcXpMZU9CdGZZVmZ4U3BFM3g5MmhVcDl5ZmQzampUWEM1SWRfNA --project 00TESTMULTI --repo-dir /Users/whenessel/Development/Git/demoRepo --branch main --start latest --number 4