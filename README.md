# Appsurify Script Installation

### Index
- [Installation Instructions](#install)
- [Available Arguments](#available_arguments)
    - [Required Arguments](#required_arguments)
    - [Recommended Arguments](#recommended_arguments)
- [Tests To Run](#teststorun)
- [Example Usage](#example_usage)
- [Additional Arguments](#additional_arguments)
    - [Build Failure Arguments](#build_failure_arguments)


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


## Git2Testbrain (git2appsurify)

This module is used to push changes in the repository to the Testbrain
server for further analysis and testing optimization.


> This module can be used as an independent command in the OS or as
> a subcommand of the main CLI application "testbrain"


```shell
git2testbrain --help
```
```shell
testbrain git2testbrain --help
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
| no               | -l, --loglevel | WARNING       |                             | Possible failities: DEBUG/INFO/WARNING/ERROR                                                                |                  |
| no               | --logfile      | stderr        |                             | Save logs to file                                                                                           |                  |





