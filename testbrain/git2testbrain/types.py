import os
import sys
import pathlib
from enum import Enum
from typing import (
    Dict,
    NoReturn,
    Sequence as Sequence,
    Tuple,
    Iterator,
    Iterable,
    cast,
    Match,
    Union,
    Any,
    Optional,
    List,
    Callable,
    TYPE_CHECKING,
    TypeVar,
    NewType,
)  # noqa: F401

if sys.version_info >= (3, 12):
    from typing import (
        Literal,
        TypedDict,
        Protocol,
        SupportsIndex as SupportsIndex,
        runtime_checkable,
    )  # noqa: F401
else:
    from typing_extensions import (
        Literal,
        SupportsIndex as SupportsIndex,
        TypedDict,
        Protocol,
        runtime_checkable,
    )  # noqa: F401


T_Branch = TypeVar("T_Branch", bound=str)

T_SHA = TypeVar("T_SHA", bound=str)

T_File = TypeVar("T_File", bound=str)

T_Patch = TypeVar("T_Patch", bound=str)

T_Diff = TypeVar("T_Diff", bound="Diff")

T_Blame = TypeVar("T_Blame", bound=str)

PathLike = TypeVar("PathLike", bound=Union[pathlib.Path, str])

Lit_change_type = Literal["A", "D", "C", "M", "R", "T", "U"]

NULL_TREE = object()
