"""Internal state.

This is an internal module containing thread state
like the ``current_app``.

This module shouldn't be used directly.
"""

import os
import sys
import threading
import weakref

from testbrain.local import Proxy
from testbrain.utils.threads import LocalStack

__all__ = ('set_default_app', 'get_current_app', 'current_app')

#: Global default app used when no current app.
default_app = None

#: Function returning the app provided or the default app if none.
#:
#: The environment variable :envvar:`TESTBRAIN_TRACE_APP` is used to
#: trace app leaks.  When enabled an exception is raised if there
#: is no active app.
app_or_default = None

#: List of all app instances (weakrefs), mustn't be used directly.
_apps = weakref.WeakSet()

#: Global set of functions to call whenever a new app is finalized.
#: Shared tasks, and built-in tasks are created by adding callbacks here.
_on_app_finalizers = set()

_task_join_will_block = False


def connect_on_app_finalize(callback):
    """Connect callback to be called when any app is finalized."""
    _on_app_finalizers.add(callback)
    return callback


def _announce_app_finalized(app):
    callbacks = set(_on_app_finalizers)
    for callback in callbacks:
        callback(app)


class _TLS(threading.local):
    #: Apps with the :attr:`~testbrain.app.base.BaseApp.set_as_current` attribute
    #: sets this, so it will always contain the last instantiated app,
    #: and is the default app returned by :func:`app_or_default`.
    current_app = None


_tls = _TLS()

_task_stack = LocalStack()


def set_default_app(app):
    """Set default app."""
    global default_app
    default_app = app


def _get_current_app():
    if default_app is None:
        #: creates the global fallback app instance.
        from testbrain.app.base import Testbrain
        set_default_app(Testbrain(
            'default', fixups=[], set_as_current=False,
            loader=os.environ.get('TESTBRAIN_LOADER') or 'default',
        ))
    return _tls.current_app or default_app


def _set_current_app(app):
    _tls.current_app = app


if os.environ.get('C_STRICT_APP'):  # pragma: no cover
    def get_current_app():
        """Return the current app."""
        raise RuntimeError('USES CURRENT APP')
elif os.environ.get('C_WARN_APP'):  # pragma: no cover
    def get_current_app():
        import traceback
        print('-- USES CURRENT_APP', file=sys.stderr)  # +
        traceback.print_stack(file=sys.stderr)
        return _get_current_app()
else:
    get_current_app = _get_current_app


#: Proxy to current app.
current_app = Proxy(get_current_app)


def _register_app(app):
    _apps.add(app)


def _deregister_app(app):
    _apps.discard(app)


def _get_active_apps():
    return _apps


def _app_or_default(app=None):
    if app is None:
        return get_current_app()
    return app


def _app_or_default_trace(app=None):  # pragma: no cover
    from traceback import print_stack
    try:
        from billiard.process import current_process
    except ImportError:
        current_process = None
    if app is None:
        if getattr(_tls, 'current_app', None):
            print('-- RETURNING TO CURRENT APP --')  # +
            print_stack()
            return _tls.current_app
        if not current_process or current_process()._name == 'MainProcess':
            raise Exception('DEFAULT APP')
        print('-- RETURNING TO DEFAULT APP --')      # +
        print_stack()
        return default_app
    return app


def enable_trace():
    """Enable tracing of app instances."""
    global app_or_default
    app_or_default = _app_or_default_trace


def disable_trace():
    """Disable tracing of app instances."""
    global app_or_default
    app_or_default = _app_or_default


if os.environ.get('TESTBRAIN_TRACE_APP'):  # pragma: no cover
    enable_trace()
else:
    disable_trace()
