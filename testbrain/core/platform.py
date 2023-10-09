import platform as _platform
import sys

SYSTEM = _platform.system()
IS_MACOS = SYSTEM == "Darwin"
IS_WINDOWS = SYSTEM == "Windows"
IS_LINUX = SYSTEM == "Linux"


PY_VERSION = sys.version_info
IS_PY2 = PY_VERSION[0] == 2
IS_PY3 = PY_VERSION[0] == 2


def py_implementation():
    """Return string identifying the current Python implementation."""
    if hasattr(_platform, "python_implementation"):
        return _platform.python_implementation()
    elif sys.platform.startswith("java"):
        return "Jython " + sys.platform
    elif hasattr(sys, "pypy_version_info"):
        v = ".".join(str(p) for p in sys.pypy_version_info[:3])
        if sys.pypy_version_info[3:]:
            v += "-" + "".join(str(p) for p in sys.pypy_version_info[3:])
        return "PyPy " + v
    else:
        return "CPython"
