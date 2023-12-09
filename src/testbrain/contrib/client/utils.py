import typing as t
from re import split

import testbrain
from testbrain.core import platform

pkg_platform = (
    f"({platform.os()}/{platform.version()}; "
    f"{platform.system()}/{platform.release()}; "
    f"{platform.processor()}-{platform.machine()}) "
    f"Python/{platform.python_version()} ({platform.python_implementation()}; "
    f"{platform.PY_COMPILER_NAME}/{platform.PY_COMPILER_VERSION})"
)


def from_camel_case(name: str) -> str:
    words = [word for word in split(r"(?=[A-Z])", name) if word]
    return "-".join(words).lower()


def to_camel_case(name: str) -> str:
    words = [word.capitalize() for word in name.split("-") if word != ""]
    return "".join(words)


def get_user_agent(
    name: t.Optional[str] = None, version: t.Optional[str] = None
) -> str:
    user_agent = (
        f"{to_camel_case(testbrain.__prog__)}/{testbrain.__version__} {pkg_platform}"
    )
    if name and version:
        user_agent += f" {name}/{version}"

    user_agent += f" (pkg: {testbrain.__name__}/{testbrain.__version__})"
    return user_agent
