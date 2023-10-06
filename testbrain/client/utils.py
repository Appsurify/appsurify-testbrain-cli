from testbrain.__version__ import __version__


def default_user_agent(name: str = "testbrain-cli") -> str:
    return f"{name}/{__version__}"


def default_headers() -> dict:
    return {"User-Agent": default_user_agent(), "Connection": "keep-alive"}
