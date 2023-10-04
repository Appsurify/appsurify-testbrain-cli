

from testbrain.__version__ import __version__

def default_user_agent(name="python-requests"):
    """
    Return a string representing the default user agent.

    :rtype: str
    """
    return f"{name}/{__version__}"


def default_headers():
    """
    :rtype: requests.structures.CaseInsensitiveDict
    """
    return {
            "User-Agent": default_user_agent(),
            "Connection": "keep-alive",
        }