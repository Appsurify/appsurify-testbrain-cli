import socket

from requests_toolbelt.adapters.socket_options import SocketOptionsAdapter

from testbrain.core import platform


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
