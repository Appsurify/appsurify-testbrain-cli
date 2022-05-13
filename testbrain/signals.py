"""Testbrain Signals.

This module defines the signals (Observer pattern) sent by
both workers and clients.

Functions can be connected to these signals, and connected
functions are called whenever a signal is called.

.. seealso::

    :ref:`signals` for more information.
"""

from .utils.dispatch import Signal

__all__ = (
    'testbraind_init', 'testbraind_after_setup',
    'setup_logging', 'after_setup_logger',
    'eventlet_pool_started', 'eventlet_pool_preshutdown',
    'eventlet_pool_postshutdown', 'eventlet_pool_apply',
)

import_modules = Signal(name='import_modules')

# - Program: `testbrain daemon`
testbraind_init = Signal(
    name='testbraind_init',
    providing_args={'instance', 'conf', 'options'},
)
testbraind_after_setup = Signal(
    name='testbraind_after_setup',
    providing_args={'instance', 'conf'},
)

# - Logging
setup_logging = Signal(
    name='setup_logging',
    providing_args={
        'loglevel', 'logfile', 'format', 'colorize',
    },
)
after_setup_logger = Signal(
    name='after_setup_logger',
    providing_args={
        'logger', 'loglevel', 'logfile', 'format', 'colorize',
    },
)

# - Eventlet
eventlet_pool_started = Signal(name='eventlet_pool_started')
eventlet_pool_preshutdown = Signal(name='eventlet_pool_preshutdown')
eventlet_pool_postshutdown = Signal(name='eventlet_pool_postshutdown')
eventlet_pool_apply = Signal(
    name='eventlet_pool_apply',
    providing_args={'target', 'args', 'kwargs'},
)

# - Programs
user_preload_options = Signal(
    name='user_preload_options',
    providing_args={'app', 'options'},
)
