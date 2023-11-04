[![image](https://img.shields.io/github/v/release/Appsurify/appsurify-testbrain-cli?label=github)](https://github.com/Appsurify/appsurify-testbrain-cli/releases)
[![image](https://img.shields.io/pypi/v/appsurify-testbrain-cli.svg)](https://pypi.org/project/appsurify-testbrain-cli/)
[![image](https://img.shields.io/pypi/l/appsurify-testbrain-cli.svg)](https://pypi.org/project/appsurify-testbrain-cli/)
[![image](https://img.shields.io/pypi/pyversions/appsurify-testbrain-cli.svg)](https://pypi.org/project/appsurify-testbrain-cli/)


# Appsurify Script Installation

### Index
- [Installation Instructions](#installation-instructions)
    - [Requirements](#requirements)
    - [Support OS / Python](#support-os--python)
    - [Installation Command](#installation-command)
- [Git2Testbrain (git2appsurify)](#git2testbrain-git2appsurify)
    - [Possible params](#possible-params)
    - [Usage Examples](#usage-examples)
- [QA2Testbrain (runtestswithappsurify)](#qa2testbrain-runtestswithappsurify)


## Installation Instructions

### Requirements

Python 3.7+

> Note: Support for Python 3.7 will be completed soon because
> this version is already considered depricated


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

## Git2Testbrain (git2appsurify)

This module is used to push changes in the repository to the Testbrain
server for further analysis and testing optimization.


> This module can be used as an independent command in the OS or as
> a subcommand of the main CLI application "testbrain"

```shell
testbrain repository push --help
```

```shell
git2testbrain push --help
```

```shell
testbrain git2testbrain push --help
```

### Possible params

| Required         | Parameter      | Default       | Env                         | Description                                                                                                 | Example          |
|------------------|----------------|---------------|-----------------------------|-------------------------------------------------------------------------------------------------------------|------------------|
| yes              | --server       |               | TESTBRAIN_SERVER            | Enter your testbrain server instance url.                                                                   | http://127.0.0.1 |
| yes              | --token        |               | TESTBRAIN_TOKEN             | Enter your testbrain server instance token.                                                                 |                  |
| yes              | --project      |               | TESTBRAIN_PROJECT           | Enter your testbrain project name.                                                                          |                  |
| no               | --work-dir     | current dir   | TESTBRAIN_WORK_DIR          | Enter the testbrain script working directory. If not specified, the current working directory will be used. |                  |
| no               | --repo-name    |               | TESTBRAIN_REPO_NAME         | Define repository name. If not specified, it will be automatically taken from the GitRepository repository. |                  |
| no               | --repo-dir     | current dir   | TESTBRAIN_REPO_DIR          | Enter the git repository directory. If not specified, the current working directory will be used.           |                  |
| no               | --branch       | current       | TESTBRAIN_BRANCH            | Enter the explicit branch to process commits. If not specified, use current active branch.                  |                  |
| no               | --number       | 1             | TESTBRAIN_NUMBER_OF_COMMITS | Enter the number of commits to process.                                                                     |                  |
| no               | --start        | latest (HEAD) | TESTBRAIN_START_COMMIT      | Enter the commit that should be starter. If not specified, it will be used 'latest' commit.                 |                  |
| no (unavailable) | --blame        | false         |                             | Add blame information.                                                                                      |                  |
| no               | -l, --loglevel | INFO          |                             | Possible failities: DEBUG/INFO/WARNING/ERROR                                                                |                  |
| no               | --logfile      | stderr        |                             | Save logs to file                                                                                           |                  |


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
ERROR    2023-10-23 11:27:39,697 testbrain.git2testbrain.controller git2testbrain/controller.py:39 controller Git2TestbrainController.get_project_id: Project didn't exist, check project name and try again!
Dumped crash report to <path_to_work_dir>/.crashdumps/git2testbrain-2023-10-23-11-27-39.dump

```

Docker version usage

$(pwd) - git repository path

```shell
docker run --rm -it \
-v $(pwd)/:/data \
appsurifyinc/appsurify-testbrain-cli git2testbrain --server https://demo.appsurify.com --token ************************************************************** --project DEMO

```


## QA2Testbrain (runtestswithappsurify)

Coming soon. Currently under development. Use the old 'appsurifyci' package

```shell
pip install appsurifyci --upgrade
```

- [PyPi](https://pypi.org/project/appsurifyci/)
- [GitHub](https://github.com/Appsurify/appsurifyci)
- [README](https://github.com/Appsurify/appsurifyci/blob/master/README.md)




