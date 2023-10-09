import click
from testbrain.core.command import TestbrainCommand
from testbrain.core.context import TestbrainContext


__all__ = ["TestbrainCommand", "TestbrainContext"]


WAVE_ART_LINES = [
    "--------------------------------",
    "-----      ***             -----",
    "---    **  ***  ***          ---",
    "-  **  *******  ***  **        -",
    "-  **  **  ********  **        -",
    "-  ******  ***  *******   **   -",
    "-  **  **  ***  ***  *******   -",
    "-      **  ***  ***  **   **   -",
    "---        ***  ***          ---",
    "-----           ***        -----",
    "--------------------------------",
]

WAVE_ART_LINES_STYLED = click.style(" \n".join(WAVE_ART_LINES), fg=(255, 109, 10))
