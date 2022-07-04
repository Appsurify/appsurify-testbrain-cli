import bisect
import importlib
import logging
import logging.config
import logging.handlers
import os
import pathlib
import pyclbr
import sys
from typing import Optional

from testbrain.core.structures import CaseInsensitiveDict

logger = logging.getLogger(__name__)


MODULE_DIR = importlib.import_module("testbrain").__path__[0]

# LOG_FORMAT = "%(asctime)-8s %(levelname)-8s %(name)s.%(funcName)s: %(message)s"
LOG_FORMAT = (
    "%(levelname)-8s %(asctime)-8s %(name)-4s "
    "%(relativePath)s:%(lineno)d "
    "%(module)s %(funcName)s"
)
LOG_FORMAT_MSG = "%(message)s"

LOG_LEVELS: CaseInsensitiveDict = CaseInsensitiveDict(
    {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
)

logging.basicConfig(
    level=logging.WARNING,
    format=f"{LOG_FORMAT}: {LOG_FORMAT_MSG}",
)


def configure_logging(
    loglevel: Optional[str] = "WARNING", logfile: Optional[pathlib.Path] = None
):
    _logger = logging.getLogger()
    _logger.handlers.clear()

    level = LOG_LEVELS.get(loglevel, "WARNING")

    # Configure the logger level
    _logger.setLevel(level)

    fmt = f"{LOG_FORMAT}: {LOG_FORMAT_MSG}"
    # Create a formatter
    formatter = logging.Formatter(fmt)

    # Create a handler for console output
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    if logfile:
        file_handler = logging.handlers.WatchedFileHandler(logfile)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)


_original_log_record_factory = logging.getLogRecordFactory()


def _log_record_factory(module, *args, **kwargs):
    record = _original_log_record_factory(module, *args, **kwargs)
    record.relativePath = None
    record.className = None

    if module == "__main__":
        module = record.module
    try:
        record.className = ClassSearcher(module).lookup_class(
            record.funcName, record.lineno
        )
    except (AttributeError, TypeError, IndexError):
        # logger.exception(exc, exc_info=False)
        ...

    if record.className:
        record.funcName = "{}.{}".format(record.className, record.funcName)

    relative_path = None

    if not pathlib.Path(record.pathname).is_absolute():
        cwd = os.getcwd()
        record.pathname = str(pathlib.Path(cwd).joinpath(record.pathname))

    if record.pathname.startswith(MODULE_DIR):
        relative_path = os.path.relpath(record.pathname, MODULE_DIR)

    if relative_path is None:
        relative_path = record.filename

    record.relativePath = relative_path
    return record


logging.setLogRecordFactory(_log_record_factory)


class ClassSearcher:
    def __init__(self, module):
        mod = pyclbr.readmodule_ex(module)
        line2func = []

        for classname, cls in mod.items():
            if isinstance(cls, pyclbr.Function):
                line2func.append((cls.lineno, None, cls.name))
            else:
                for methodname, start in cls.methods.items():
                    line2func.append((start, classname, methodname))

        line2func.sort()
        keys = [item[0] for item in line2func]
        self.line2func = line2func
        self.keys = keys

    def line_to_class(self, lineno):
        index = bisect.bisect(self.keys, lineno) - 1
        return self.line2func[index][1]

    def lookup_class(self, funcname, lineno):
        if funcname == "<module>":
            return None

        return self.line_to_class(lineno)
