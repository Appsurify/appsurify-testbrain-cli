import bisect
import logging
import logging.handlers
import logging.config
import pathlib
import pyclbr
import sys
from typing import Dict, List, Any, Optional
from collections import OrderedDict
from collections.abc import Callable, Mapping, MutableMapping


class CaseInsensitiveDict(MutableMapping):
    """A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        self._store = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s"

LOG_FORMAT_VERBOSITY = {0: "", 1: "", 2: ""}

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
    format=LOG_FORMAT,
)


def mlevel(level: str) -> int:
    """Convert level name to log level."""
    if level and not isinstance(level, int):
        return LOG_LEVELS[level.upper()]
    return level


class Module:
    def __init__(self, module):
        mod = pyclbr.readmodule_ex(module)
        line2func = []

        for classname, cls in mod.items():
            if isinstance(cls, pyclbr.Function):
                line2func.append((cls.lineno, "__main__", cls.name))
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
            return "__main__"

        return self.line_to_class(lineno)


_former_log_record_factory = logging.getLogRecordFactory()


def _log_record_class_name_injector(module, *args, **kwargs):
    record = _former_log_record_factory(module, *args, **kwargs)
    # record.className = lookup_class(record.module, record.funcName, record.lineno)
    if module == "__main__":
        module = record.module
    record.className = Module(module).lookup_class(record.funcName, record.lineno)
    if record.className != "__main__":
        record.funcName = "{}.{}".format(record.className, record.funcName)
    return record


logging.setLogRecordFactory(_log_record_class_name_injector)


def configure_logging(
    loglevel: Optional[str] = "WARNING", logfile: Optional[pathlib.Path] = None
):
    # library, _, _ = __name__.partition(".")
    # logger = logging.getLogger(library)
    logger = logging.getLogger()
    logger.handlers.clear()

    level = mlevel(loglevel)

    # Configure the logger level
    logger.setLevel(level)

    # Create a formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Create a handler for console output
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if logfile:
        file_handler = logging.handlers.WatchedFileHandler(logfile)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
