import sys

from . import maybe_patch_concurrency


__all__ = ('main',)


def main() -> None:
    """Entrypoint to the ``celery`` umbrella command."""
    if 'multi' not in sys.argv:
        maybe_patch_concurrency()
    from testbrain.bin.testbrain import main as _main
    sys.exit(_main())


if __name__ == '__main__':  # pragma: no cover
    main()
