[![image](https://img.shields.io/pypi/v/appsurify-testbrain-cli?logo=pypi)](https://pypi.org/project/appsurify-testbrain-cli/)
[![image](https://img.shields.io/docker/v/appsurifyinc/appsurify-testbrain-cli?logo=docker)](https://hub.docker.com/repository/docker/appsurifyinc/appsurify-testbrain-cli/general)
[![image](https://img.shields.io/github/v/release/Appsurify/appsurify-testbrain-cli?logo=GitHub)](https://github.com/Appsurify/appsurify-testbrain-cli/releases)
[![image](https://img.shields.io/pypi/pyversions/appsurify-testbrain-cli.svg)](https://pypi.org/project/appsurify-testbrain-cli/)

# Appsurify Script Installation

### Index
- [Installation Instructions](#installation-instructions)
    - [Requirements](#requirements)
    - [Support OS / Python](#support-os--python)
    - [Installation Command](#installation-command)
- [Repository Push / Git2Testbrain (git2appsurify)](#repository-push--git2testbrain-git2appsurify)
    - [Possible params](#possible-params)
    - [Usage Examples](#usage-examples)
- [Repository Checkout](#repository-checkout)
    - [Possible params](#possible-params-1)
    - [Usage Examples](#usage-examples-1)
- [QA2Testbrain (runtestswithappsurify)](#qa2testbrain-runtestswithappsurify)


## Refs
- [Documentation Testbrain CLI](https://appsurify.github.io/appsurify-testbrain-cli/)
- [PyPi](https://pypi.org/project/appsurifyci/)
- [GitHub](https://github.com/Appsurify/appsurifyci)
- [Docker](https://hub.docker.com/r/appsurifyinc/appsurify-testbrain-cli/)
- [README](https://github.com/Appsurify/appsurifyci/blob/master/README.md)


## Installation Instructions

### Requirements

Python 3.7+

> Note: Support for Python 3.7 will be completed soon because
> this version is already considered deprecated


### Support OS / Python


| OS      | Python | Support |
|---------|--------|---------|
| Linux   | 3.7    | 🟢      |
| Linux   | 3.8    | 🟢      |
| Linux   | 3.11   | 🟢      |
| MacOS   | 3.7    | 🟢      |
| MacOS   | 3.8    | 🟢      |
| MacOS   | 3.11   | 🟢      |
| Windows | 3.7    | 🟢      |
| Windows | 3.8    | 🟢      |
| Windows | 3.11   | 🟢      |


### Installation Command

```shell
pip install appsurify-testbrain-cli
```
or
```shell
poetry add appsurify-testbrain-cli
```

> Note: Use **-U** or **--upgrade** for force upgrade to last version


### Docker image "appsurify-testbrain-cli"

**Latest version**
```shell
docker pull appsurifyinc/appsurify-testbrain-cli

```
**Specify version**
```shell
docker pull appsurifyinc/appsurify-testbrain-cli:2023.10.24

```

[Howto usage](#usage-examples)

## Repository Push | Git2Testbrain (git2appsurify)

This module is used to push changes in the repository to the Testbrain
server for further analysis and testing optimization.


> This module can be used as an independent command in the OS or as
> a subcommand of the main CLI application "testbrain"

Alias #1
```shell
testbrain git push --help
```

Alias #2
```shell
git2testbrain push --help
```

Alias #3
```shell
testbrain git2testbrain push --help
```

### Possible params

| Required         | Parameter          | Default       | Env                         | Description                                                                                                 | Example          |
|------------------|--------------------|---------------|-----------------------------|-------------------------------------------------------------------------------------------------------------|------------------|
| yes              | --server           |               | TESTBRAIN_SERVER            | Enter your testbrain server instance url.                                                                   | http://127.0.0.1 |
| yes              | --token            |               | TESTBRAIN_TOKEN             | Enter your testbrain server instance token.                                                                 |                  |
| yes              | --project          |               | TESTBRAIN_PROJECT           | Enter your testbrain project name.                                                                          |                  |
| no               | --work-dir         | current dir   | TESTBRAIN_WORK_DIR          | Enter the testbrain script working directory. If not specified, the current working directory will be used. |                  |
| no               | --repo-name        |               | TESTBRAIN_REPO_NAME         | Define repository name. If not specified, it will be automatically taken from the GitRepository repository. |                  |
| no               | --repo-dir         | current dir   | TESTBRAIN_REPO_DIR          | Enter the git repository directory. If not specified, the current working directory will be used.           |                  |
| no               | --branch           | current       | TESTBRAIN_BRANCH            | Enter the explicit branch to process commits. If not specified, use current active branch.                  |                  |
| no               | --start / --commit | latest (HEAD) | TESTBRAIN_START_COMMIT      | Enter the commit that should be starter. If not specified, it will be used 'latest' commit.                 |                  |
| no               | --number           | 1             | TESTBRAIN_NUMBER_OF_COMMITS | Enter the number of commits to process.                                                                     |                  |
| no (unavailable) | --blame            | false         |                             | Add blame information.                                                                                      |                  |
| no               | --minimize         | false         |                             | Suppress commit changes information. [default: (False)]                                                     |                  |
| no               | --pr-mode          | false         | TESTBRAIN_PR_MODE           | Activate PR mode                                                                                            |                  |
| no               | -l, --loglevel     | INFO          |                             | Possible failities: DEBUG/INFO/WARNING/ERROR                                                                |                  |
| no               | --logfile          | stderr        |                             | Save logs to file                                                                                           |                  |
| no               | --quiet            | false         |                             | Quiet mode... everytime exit with 0                                                                         |                  |

### Usage examples

Push to Testbrain server only one last commit from current branch

```shell
git2testbrain --server https://demo.appsurify.com --token ************************************************************** --project DEMO

```
or

```shell
git2testbrain push --server https://demo.appsurify.com --token ************************************************************** --project DEMO

```

Push to Testbrain server last 100 commits
started from specify commit into specify branch

```shell
git2testbrain --server https://demo.appsurify.com --token ************************************************************** --project DEMO --branch main --start latest --number 100

```

If need more process information - change logging level

```shell
git2testbrain --server https://demo.appsurify.com --token ************************************************************** --project DEMO --branch main --start latest --number 100 --loglevel DEBUG

```

Add log file with full or relative path.

```shell
git2testbrain --server https://demo.appsurify.com --token ************************************************************** --project DEMO --branch main --start latest --number 100 --loglevel INFO --logfile ./git2testbrain.log

```


If any crash errors script will create crash dump file into {WORK_DIR}/.crashdumps/

```shell
git2testbrain --server https://demo.appsurify.com --token ************************************************************** --project DEMO

```
You can see this message
```text
2023-11-05 21:16:03 INFO     testbrain.repository.cli push [repository/cli.py:184] Running...
2023-11-05 21:16:03 DEBUG    testbrain.terminal.process Process.__init__ [terminal/process.py:22] Set up execution working dir ...
Dumped crash report to <path_to_work_dir>/.crashdumps/git2testbrain-2023-10-23-11-27-39.dump

```

Docker version usage

$(pwd) - git repository path

```shell
docker run --rm -it \
-v $(pwd)/:/data \
appsurifyinc/appsurify-testbrain-cli git2testbrain --server https://demo.appsurify.com --token ************************************************************** --project DEMO

```


### CI example (github actions)

`.github/workflows/testbrain-git2testbrain.yml`
```yaml
name: "Testbrain"

on:
    workflow_dispatch:
    pull_request:
        branches:
            - "main"
            - "development"
    push:
        branches:
            - "main"
            - "releases/*.*.*"
            - "development"

jobs:
    push-changes:
        name: "Push changes to server"
        runs-on: ubuntu-latest
        permissions:
            contents: write
            pull-requests: write
            checks: write
        steps:
            - name: "Checkout git"
              uses: actions/checkout@v4
              with:
                  fetch-depth: 0
            - name: "Extract branch name"
              shell: bash
              run: echo "branch=${GITHUB_HEAD_REF:-${GITHUB_REF#refs/heads/}}" >> $GITHUB_OUTPUT
              id: extract_branch
            - name: "Push"
              uses: addnab/docker-run-action@v3
              with:
                  image: appsurifyinc/appsurify-testbrain-cli:latest
                  options: -v ${{ github.workspace }}:/data -e TESTBRAIN_PR_MODE=${{ github.event_name == 'pull_request' }}
                  run: |
                      git2testbrain push --server ${{ vars.TESTBRAIN_SERVER }} --token ${{ secrets.TESTBRAIN_TOKEN }} --project ${{ vars.TESTBRAIN_PROJECT }} --branch ${{ steps.extract_branch.outputs.branch }} --start ${{ github.sha }} --number ${{ vars.TESTBRAIN_NUMBER_OF_COMMITS }} -l DEBUG
            - name: "Upload crash dumps"
              uses: actions/upload-artifact@v3
              if: failure()
              with:
                  name: "crashdumps"
                  path: ${{ github.workspace }}/.crashdumps/
                  retention-days: 1

```


## Repository Checkout

This module is used to checkout branches during
the execution of CI pipelines or manually. **Cloning is not provided.**


Alias #1
```shell
testbrain git checkout --help
```

Alias #2
```shell
git2testbrain checkout --help
```

Alias #3
```shell
testbrain git2testbrain checkout --help
```

### Possible params


| Required         | Parameter       | Default       | Env                         | Description                                                                                                 | Example          |
|------------------|-----------------|---------------|-----------------------------|-------------------------------------------------------------------------------------------------------------|------------------|
| no               | --repo-dir      | current dir   | TESTBRAIN_REPO_DIR          | Enter the git repository directory. If not specified, the current working directory will be used.           |                  |
| no               | --branch        | current       | TESTBRAIN_BRANCH            | Enter the explicit branch to process commits. If not specified, use current active branch.                  |                  |
| no               | --commit        | latest (HEAD) | TESTBRAIN_START_COMMIT      | Enter the commit that should be starter. If not specified, it will be used 'latest' commit.                 |                  |
| no               | --pr-mode       | false         | TESTBRAIN_PR_MODE           | Activate PR mode                                                                                            |                  |
| no               | --work-dir      | current dir   | TESTBRAIN_WORK_DIR          | Enter the testbrain script working directory. If not specified, the current working directory will be used. |                  |
| no               | -l, --loglevel  | INFO          |                             | Possible failities: DEBUG/INFO/WARNING/ERROR                                                                |                  |
| no               | --logfile       | stderr        |                             | Save logs to file                                                                                           |                  |
| no               | --quiet         | false         |                             | Quiet mode... everytime exit with 0                                                                         |                  |

### Usage examples

Checkout using Testbrain CLI

```shell
git2testbrain checkout --branch main -l INFO

```
or
```shell
git2testbrain checkout --branch main --commit 75ec2f061868c33306963a27d5164211553c049b --pr-mode -l INFO

```
or
```shell
git2testbrain checkout --branch main --commit 676c581 --pr-mode -l INFO

```

Docker version usage

$(pwd) - git repository path

```shell
docker run --rm -it \
-v $(pwd)/:/data \
appsurifyinc/appsurify-testbrain-cli git2testbrain checkout --branch main --commit 676c581 --pr-mode -l INFO

```


## QA2Testbrain (runtestswithappsurify)

Coming soon. Currently under development. Use the old 'appsurifyci' package

```shell
pip install appsurifyci --upgrade
```

