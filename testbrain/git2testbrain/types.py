import pathlib

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from typing import TypeVar, Union

T_Branch = TypeVar("T_Branch", bound=str)

T_SHA = TypeVar("T_SHA", bound=str)

T_File = TypeVar("T_File", bound=str)

T_Patch = TypeVar("T_Patch", bound=str)

T_Blame = TypeVar("T_Blame", bound=str)

PathLike = TypeVar("PathLike", bound=Union[pathlib.Path, str])

Lit_change_type = Literal["A", "D", "C", "M", "R", "T", "U"]

NULL_TREE = object()
