import logging
import socket
import sys
import typing as t
import warnings

import requests
from requests import adapters

from testbrain.contrib.client.compat import connection, poolmanager
from testbrain.contrib.client.exceptions import RequestsVersionTooOld
from testbrain.core import platform

logger = logging.getLogger(__name__)


class SocketOptionsAdapter(adapters.HTTPAdapter):
    """An adapter for requests that allows users to specify socket options.

    Since version 2.4.0 of requests, it is possible to specify a custom list
    of socket options that need to be set before establishing the connection.

    Example usage::

        >>> import socket
        >>> import requests
        >>> from testbrain.client.adapters import SocketOptionsAdapter
        >>> s = requests.Session()
        >>> opts = [(socket.IPPROTO_TCP, socket.TCP_NODELAY, 0)]
        >>> adapter = SocketOptionsAdapter(socket_options=opts)
        >>> s.mount('http://', adapter)

    You can also take advantage of the list of default options on this class
    to keep using the original options in addition to your custom options. In
    that case, ``opts`` might look like::

        >>> opts = SocketOptionsAdapter.default_options + opts

    """

    if connection is not None:
        default_options = getattr(
            connection.HTTPConnection,
            "default_socket_options",
            [(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)],
        )
    else:
        default_options = []
        warnings.warn(
            "This version of Requests is only compatible with a "
            "version of urllib3 which is too old to support setting options "
            "on a socket. This adapter is functionally useless.",
            RequestsVersionTooOld,
        )

    def __init__(self, **kwargs):
        self.socket_options = kwargs.pop("socket_options", self.default_options)

        super(SocketOptionsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        if requests.__build__ >= 0x020400:
            # NOTE(Ian): Perhaps we should raise a warning
            self.poolmanager = poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                socket_options=self.socket_options,
                **pool_kwargs,
            )
        else:
            super(SocketOptionsAdapter, self).init_poolmanager(
                connections, maxsize, block, **pool_kwargs
            )


class TCPKeepAliveAdapter(SocketOptionsAdapter):
    def __init__(self, idle: int = 60, interval: int = 20, count: int = 5, **kwargs):
        socket_options = kwargs.pop(
            "socket_options", SocketOptionsAdapter.default_options
        )
        socket_options = socket_options + [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]

        # TCP Keep Alive Probes for Linux
        if (
            platform.IS_LINUX
            and hasattr(socket, "TCP_KEEPIDLE")
            and hasattr(socket, "TCP_KEEPINTVL")
            and hasattr(socket, "TCP_KEEPCNT")
        ):
            socket_options += [
                (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, idle),
                (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval),
                (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, count),
            ]

        # TCP Keep Alive Probes for Windows OS
        elif platform.IS_WINDOWS and hasattr(socket, "TCP_KEEPIDLE"):
            socket_options += [
                (socket.SOL_TCP, socket.TCP_KEEPIDLE, idle),
                (socket.SOL_TCP, socket.TCP_KEEPINTVL, interval),
                (socket.SOL_TCP, socket.TCP_KEEPCNT, count),
            ]

        # TCP Keep Alive Probes for macOS
        elif platform.IS_MACOS:
            # On OSX, TCP_KEEPALIVE from netinet/tcp.h is not exported
            # by python's socket module
            tcp_keepalive = getattr(socket, "TCP_KEEPALIVE", 0x10)
            socket_options += [
                (socket.IPPROTO_TCP, tcp_keepalive, idle),
                (socket.SOL_TCP, socket.TCP_KEEPINTVL, interval),
                (socket.SOL_TCP, socket.TCP_KEEPCNT, count),
            ]

        super(TCPKeepAliveAdapter, self).__init__(
            socket_options=socket_options, **kwargs
        )
