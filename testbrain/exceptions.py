"""Testbrain error types.

Error Hierarchy
===============

- :exc:`Exception`
    - :exc:`testbrain.exceptions.TestbrainError`
        - :exc:`~testbrain.exceptions.ImproperlyConfigured`
        - :exc:`~testbrain.exceptions.SecurityError`
        - :exc:`~testbrain.exceptions.TaskPredicate`
            - :exc:`~testbrain.exceptions.Ignore`
            - :exc:`~testbrain.exceptions.Reject`
            - :exc:`~testbrain.exceptions.Retry`
        - :exc:`~testbrain.exceptions.TaskError`
            - :exc:`~testbrain.exceptions.QueueNotFound`
            - :exc:`~testbrain.exceptions.IncompleteStream`
            - :exc:`~testbrain.exceptions.NotRegistered`
            - :exc:`~testbrain.exceptions.AlreadyRegistered`
            - :exc:`~testbrain.exceptions.TimeoutError`
            - :exc:`~testbrain.exceptions.MaxRetriesExceededError`
            - :exc:`~testbrain.exceptions.TaskRevokedError`
            - :exc:`~testbrain.exceptions.InvalidTaskError`
            - :exc:`~testbrain.exceptions.ChordError`
        - :exc:`~testbrain.exceptions.BackendError`
            - :exc:`~testbrain.exceptions.BackendGetMetaError`
            - :exc:`~testbrain.exceptions.BackendStoreError`
    - :class:`kombu.exceptions.KombuError`
        - :exc:`~testbrain.exceptions.OperationalError`

            Raised when a transport connection error occurs while
            sending a message (be it a task, remote control command error).

            .. note::
                This exception does not inherit from
                :exc:`~testbrain.exceptions.TestbrainError`.
    - **billiard errors** (prefork pool)
        - :exc:`~testbrain.exceptions.SoftTimeLimitExceeded`
        - :exc:`~testbrain.exceptions.TimeLimitExceeded`
        - :exc:`~testbrain.exceptions.WorkerLostError`
        - :exc:`~testbrain.exceptions.Terminated`
- :class:`UserWarning`
    - :class:`~testbrain.exceptions.TestbrainWarning`
        - :class:`~testbrain.exceptions.AlwaysEagerIgnored`
        - :class:`~testbrain.exceptions.DuplicateNodenameWarning`
        - :class:`~testbrain.exceptions.FixupWarning`
        - :class:`~testbrain.exceptions.NotConfigured`
        - :class:`~testbrain.exceptions.SecurityWarning`
- :exc:`BaseException`
    - :exc:`SystemExit`
        - :exc:`~testbrain.exceptions.WorkerTerminate`
        - :exc:`~testbrain.exceptions.WorkerShutdown`
"""

import numbers

from billiard.exceptions import (SoftTimeLimitExceeded, Terminated,
                                 TimeLimitExceeded)
from click import ClickException
from kombu.exceptions import OperationalError

__all__ = (
    'reraise',
    # Warnings
    'TestbrainWarning',
    'AlwaysEagerIgnored', 'DuplicateNodenameWarning',
    'FixupWarning', 'NotConfigured', 'SecurityWarning',

    # Core errors
    'TestbrainError',
    'ImproperlyConfigured', 'SecurityError',

    # Kombu (messaging) errors.
    'OperationalError',

    # Task semi-predicates
    'TaskPredicate', 'Ignore', 'Reject', 'Retry',

    # Task related errors.
    'TaskError', 'QueueNotFound', 'IncompleteStream',
    'NotRegistered', 'AlreadyRegistered', 'TimeoutError',
    'MaxRetriesExceededError', 'TaskRevokedError',
    'InvalidTaskError', 'ChordError',

    # Backend related errors.
    'BackendError', 'BackendGetMetaError', 'BackendStoreError',

    # Billiard task errors.
    'SoftTimeLimitExceeded', 'TimeLimitExceeded', 'Terminated',

    # Deprecation warnings (forcing Python to emit them).
    'CPendingDeprecationWarning', 'CDeprecationWarning',

    # Worker shutdown semi-predicates (inherits from SystemExit).
    'WorkerShutdown', 'WorkerTerminate',

    'TestbrainCommandException',
)

UNREGISTERED_FMT = """\
Task of kind {0} never registered, please make sure it's imported.\
"""


def reraise(tp, value, tb=None):
    """Reraise exception."""
    if value.__traceback__ is not tb:
        raise value.with_traceback(tb)
    raise value


class TestbrainWarning(UserWarning):
    """Base class for all Testbrain warnings."""


class AlwaysEagerIgnored(TestbrainWarning):
    """send_task ignores :setting:`task_always_eager` option."""


class DuplicateNodenameWarning(TestbrainWarning):
    """Multiple workers are using the same nodename."""


class FixupWarning(TestbrainWarning):
    """Fixup related warning."""


class NotConfigured(TestbrainWarning):
    """Testbrain hasn't been configured, as no config module has been found."""


class SecurityWarning(TestbrainWarning):
    """Potential security issue found."""


class TestbrainError(Exception):
    """Base class for all Testbrain errors."""


class TaskPredicate(TestbrainError):
    """Base class for task-related semi-predicates."""


class Retry(TaskPredicate):
    """The task is to be retried later."""

    #: Optional message describing context of retry.
    message = None

    #: Exception (if any) that caused the retry to happen.
    exc = None

    #: Time of retry (ETA), either :class:`numbers.Real` or
    #: :class:`~datetime.datetime`.
    when = None

    def __init__(self, message=None, exc=None, when=None, is_eager=False,
                 sig=None, **kwargs):
        from kombu.utils.encoding import safe_repr
        self.message = message
        if isinstance(exc, str):
            self.exc, self.excs = None, exc
        else:
            self.exc, self.excs = exc, safe_repr(exc) if exc else None
        self.when = when
        self.is_eager = is_eager
        self.sig = sig
        super().__init__(self, exc, when, **kwargs)

    def humanize(self):
        if isinstance(self.when, numbers.Number):
            return f'in {self.when}s'
        return f'at {self.when}'

    def __str__(self):
        if self.message:
            return self.message
        if self.excs:
            return f'Retry {self.humanize()}: {self.excs}'
        return f'Retry {self.humanize()}'

    def __reduce__(self):
        return self.__class__, (self.message, self.exc, self.when)


RetryTaskError = Retry  # XXX compat


class Ignore(TaskPredicate):
    """A task can raise this to ignore doing state updates."""


class Reject(TaskPredicate):
    """A task can raise this if it wants to reject/re-queue the message."""

    def __init__(self, reason=None, requeue=False):
        self.reason = reason
        self.requeue = requeue
        super().__init__(reason, requeue)

    def __repr__(self):
        return f'reject requeue={self.requeue}: {self.reason}'


class ImproperlyConfigured(TestbrainError):
    """Testbrain is somehow improperly configured."""


class SecurityError(TestbrainError):
    """Security related exception."""


class TaskError(TestbrainError):
    """Task related errors."""


class QueueNotFound(KeyError, TaskError):
    """Task routed to a queue not in ``conf.queues``."""


class IncompleteStream(TaskError):
    """Found the end of a stream of data, but the data isn't complete."""


class NotRegistered(KeyError, TaskError):
    """The task is not registered."""

    def __repr__(self):
        return UNREGISTERED_FMT.format(self)


class AlreadyRegistered(TaskError):
    """The task is already registered."""
    # XXX Unused


class TimeoutError(TaskError):
    """The operation timed out."""


class MaxRetriesExceededError(TaskError):
    """The tasks max restart limit has been exceeded."""

    def __init__(self, *args, **kwargs):
        self.task_args = kwargs.pop("task_args", [])
        self.task_kwargs = kwargs.pop("task_kwargs", dict())
        super().__init__(*args, **kwargs)


class TaskRevokedError(TaskError):
    """The task has been revoked, so no result available."""


class InvalidTaskError(TaskError):
    """The task has invalid data or ain't properly constructed."""


class ChordError(TaskError):
    """A task part of the chord raised an exception."""


class CPendingDeprecationWarning(PendingDeprecationWarning):
    """Warning of pending deprecation."""


class CDeprecationWarning(DeprecationWarning):
    """Warning of deprecation."""


class WorkerTerminate(SystemExit):
    """Signals that the worker should terminate immediately."""


SystemTerminate = WorkerTerminate  # XXX compat


class WorkerShutdown(SystemExit):
    """Signals that the worker should perform a warm shutdown."""


class BackendError(Exception):
    """An issue writing or reading to/from the backend."""


class BackendGetMetaError(BackendError):
    """An issue reading from the backend."""

    def __init__(self, *args, **kwargs):
        self.task_id = kwargs.get('task_id', "")

    def __repr__(self):
        return super().__repr__() + " task_id:" + self.task_id


class BackendStoreError(BackendError):
    """An issue writing to the backend."""

    def __init__(self, *args, **kwargs):
        self.state = kwargs.get('state', "")
        self.task_id = kwargs.get('task_id', "")

    def __repr__(self):
        return super().__repr__() + " state:" + self.state + " task_id:" + self.task_id


class TestbrainCommandException(ClickException):
    """A general command exception which stores an exit code."""

    def __init__(self, message, exit_code):
        super().__init__(message=message)
        self.exit_code = exit_code
