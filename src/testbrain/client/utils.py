import typing as t
from re import split
from testbrain import platform, pkg_name, pkg_version


def from_camel_case(name: str) -> str:
    words = [word for word in split(r"(?=[A-Z])", name) if word]
    return "-".join(words).lower()


pkg_platform = (
    f"({platform.os()}/{platform.version()}; "
    f"{platform.system()}/{platform.release()}; "
    f"{platform.processor()}-{platform.machine()}) "
    f"Python/{platform.python_version()} ({platform.python_implementation()}; "
    f"{platform.PY_COMPILER_NAME}/{platform.PY_COMPILER_VERSION})"
)


def get_user_agent(
    name: t.Optional[str] = None, version: t.Optional[str] = None
) -> str:
    user_agent = f"{pkg_name}/{pkg_version} {pkg_platform}"
    if name and version:
        user_agent += f" {name}/{version}"
    return user_agent
