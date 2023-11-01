import abc

from testbrain import platform, __name__, __version__

from testbrain.client import HttpClient


print(
    f"{__name__}/{__version__} "
    f"({platform.os()}/{platform.version()}; {platform.system()}/{platform.release()}; "
    f"{platform.processor()}-{platform.machine()}) "
    f"Python/{platform.python_version()} ({platform.python_implementation()}; {platform.PY_COMPILER_NAME}/{platform.PY_COMPILER_VERSION}) "
    f"Testbrain/2023.11.1"
)

print(
    f"{__name__}/{__version__} "
    f"({platform.os()}/{platform.version()}; {platform.system()}/{platform.release()}; "
    f"{platform.processor()}-{platform.machine()}) "
    f"Python/{platform.python_version()} ({platform.python_implementation()}; {platform.PY_COMPILER_NAME}/{platform.PY_COMPILER_VERSION}) "
    f"testbrain/2023.11.1 Repository/2023.10.31"
)


print(
    f"\n"
    f"OS: {platform.os()}\n"
    f"VERSION: {platform.version()}\n"
    f"SYSTEM: {platform.system()}\n"
    f"RELEASE: {platform.release()}\n"
    f"MACHINE: {platform.machine()}\n"
    f"PROCESSOR: {platform.processor()}\n"
)

# c = HttpClient()
# print(c.user_agent)

from testbrain.repository.client import RepositoryClient

r = RepositoryClient()

print(r.user_agent)
