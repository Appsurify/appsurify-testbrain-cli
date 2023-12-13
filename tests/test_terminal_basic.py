import pytest
import subprocess


def test_echo_null_byte(fp):
    fp.register(["echo", "-ne", "\x00"], stdout=bytes.fromhex("00"))

    process = subprocess.Popen(
        ["echo", "-ne", "\x00"],
        stdout=subprocess.PIPE,
    )
    out, _ = process.communicate()

    assert process.returncode == 0
    assert out == b"\x00"
