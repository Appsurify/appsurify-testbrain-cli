import platform as _platform
import sys

RELEASE = _platform.release()
MACHINE = _platform.machine()
VERSION = _platform.version()

SYSTEM = _platform.system()
IS_MACOS = SYSTEM == "Darwin"
IS_WINDOWS = SYSTEM == "Windows"
IS_LINUX = SYSTEM == "Linux"

PY_VERSION = _platform.python_version()
PY_IMPLEMENTATION = _platform.python_implementation()


SYS_VER = sys.version_info
IS_PY2 = SYS_VER[0] == 2
IS_PY3 = SYS_VER[0] == 2
