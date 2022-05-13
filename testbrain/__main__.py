"""Entry-point for the :program:`testbrain` umbrella command."""

import sys


__all__ = ('main',)


def main():
    """Entrypoint to the ``testbrain`` umbrella command."""
    from testbrain.bin.testbrain import main as _main
    sys.exit(_main())


if __name__ == '__main__':  # pragma: no cover
    main()
