import bisect
import importlib
import logging
import logging.config
import logging.handlers
import os
import pathlib
import pyclbr
import sys
import typing as t

logger = logging.getLogger("testbrain")

MODULE_DIR = pathlib.Path(__file__).parent.parent


LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

LOG_LEVELS.setdefault("INFO", logging.INFO)

LOG_FORMAT_DATE = "%Y-%m-%d %H:%M:%S"


LOG_FORMATS = {
    "DEBUG": (
        "%(asctime)-8s %(levelname)-8s %(name)s %(funcName)s "
        "[%(relativePath)s:%(lineno)d] %(message)s"
    ),
    # "INFO": f"{LOG_FORMAT_BASE} {LOG_FORMAT_MSG}",
    "INFO": "%(asctime)-8s %(levelname)-8s %(message)s",
    "WARNING": "%(asctime)-8s %(levelname)-8s %(message)s",
    "ERROR": "%(asctime)-8s %(levelname)-8s %(message)s",
}

LOG_FORMATS.setdefault("INFO", "%(asctime)-8s %(levelname)-8s %(message)s")


logging.basicConfig(
    level=logging.WARNING,
    format=LOG_FORMATS["WARNING"],
)


def configure_logging(
    level: t.Optional[str] = "INFO",
    file: t.Optional[pathlib.Path] = None,
):
    # LogLevel
    log_level = LOG_LEVELS[level]

    # LogFormat
    log_fmt = LOG_FORMATS[level]

    # Create a formatter
    formatter = logging.Formatter(log_fmt, datefmt=LOG_FORMAT_DATE)

    # Set up 'root' logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove all attached handlers, in case there was
    # a logger with using the name 'root'
    del root_logger.handlers[:]

    if file:
        file_handler = logging.handlers.WatchedFileHandler(file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Create a handler for console output
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


_original_log_record_factory = logging.getLogRecordFactory()


def _log_record_factory(module, *args, **kwargs):
    record = _original_log_record_factory(module, *args, **kwargs)
    record.relativePath = None
    record.className = None

    if module == "__main__":
        module = record.module
    try:
        class_searcher = ClassSearcher(module)
        record.className = class_searcher.lookup_class(record.funcName, record.lineno)
    except (AttributeError, TypeError, IndexError) as exc:
        # logger.exception(exc, exc_info=False)
        print(exc)
        ...

    if record.className:
        record.funcName = "{}.{}".format(record.className, record.funcName)

    relative_path = None

    if not pathlib.Path(record.pathname).is_absolute():
        cwd = os.getcwd()
        record.pathname = str(pathlib.Path(cwd).joinpath(record.pathname))

    mod_dir = MODULE_DIR
    if isinstance(mod_dir, pathlib.Path):
        mod_dir = str(mod_dir)

    if record.pathname.startswith(mod_dir):
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
