import pytest
import platform


@pytest.fixture(scope="session", autouse=True)
def setup(request, record_testsuite_property):
    record_testsuite_property("environment", platform.system())
    record_testsuite_property("platform", f"PY-{platform.python_version()}")
    record_testsuite_property("machine", platform.machine())
    yield
