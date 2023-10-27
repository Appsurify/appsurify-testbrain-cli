import platform


OS_RELEASE = platform.release()
OS_MACHINE = platform.machine()
OS_VERSION = platform.version()

OS_SYSTEM = platform.system()
IS_OS_MACOS = OS_SYSTEM == "Darwin"
IS_OS_WINDOWS = OS_SYSTEM == "Windows"
IS_OS_LINUX = OS_SYSTEM == "Linux"

PY_COMPILER = platform.python_compiler()
PY_VERSION = platform.python_version()
PY_IMPLEMENTATION = platform.python_implementation()

IS_PY2 = PY_VERSION[0] == 2
IS_PY3 = PY_VERSION[0] == 2
