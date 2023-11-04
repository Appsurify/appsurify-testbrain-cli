from testbrain.client import __version__ as client_version
from testbrain.repository import __version__ as repository_version
from testbrain.terminal import __version__ as terminal_version
from testbrain.tests import __version__ as tests_version

__title__ = "Appsurify Testbrain CLI"
__name__ = "testbrain"
__version__ = "2023.11.4"
__build__ = "undefined"

pkg_name, pkg_version = __name__, __version__

short_version_message = f"{__name__} ({__version__})"

version_message = (
    f"{__name__} ({__version__}) "
    f"[repository/{repository_version}, "
    f"client/{client_version}, "
    f"terminal/{terminal_version}, "
    f"tests/{tests_version}]"
)
