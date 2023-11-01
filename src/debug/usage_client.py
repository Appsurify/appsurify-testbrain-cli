# from testbrain import client
#
#
# c = client.HTTPClient()
#
# resp = c.request('GET', 'http://example.com/')
#
# resp = c.get("http://example.com/")
#
# resp = c.post("http://example/")
#
#
# repo_client = client.RepositoryClient("http://example.com", token="<PASSWORD>")
#
# project = repo_client.get_project()

import requests
import typing as t
from testbrain import platform
from testbrain import __app__, __name__, __version__, __build__
from testbrain.client import TCPKeepAliveAdapter, HTTPTokenAuth, HTTPClient


ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
ua2 = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
ua_win = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76"
ua_win2 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
ua_linux = "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"


ua_tb = "Appsurify-testbrain-cli/2023.10.26 (Macintosh; Intel Mac OS X)"
class RepositoryClient(HTTPClient):

    def __init__(self, url="http://example.com", token="<TOKEN>", **kwargs):
        super().__init__(**kwargs)



c = HTTPClient()
h = RepositoryClient()

print("C: ", c.get("http://httpbin.org/user-agent").json()["user-agent"])
print("H: ", h.get("http://httpbin.org/user-agent").json()["user-agent"])

print("--------------")
print("C: ", c.get("http://httpbin.org/headers").json()["headers"])
print("H: ", h.get("http://httpbin.org/headers").json()["headers"])


