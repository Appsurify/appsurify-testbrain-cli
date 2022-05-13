"""Testbrain Application."""
from testbrain import _state
from testbrain._state import app_or_default
from testbrain.local import Proxy

from .base import Testbrain
from .utils import AppPickler

__all__ = (
    'Testbrain', 'AppPickler', 'app_or_default', 'default_app')

#: Proxy always returning the app set as default.
default_app = Proxy(lambda: _state.default_app)
