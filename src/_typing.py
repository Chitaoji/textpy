"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Union

if TYPE_CHECKING:

    from .imports import ImportHistory
    from .re_extensions import _typing

    PatternType, ReplType = _typing.PatternType, _typing.ReplType


logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)

HistoryKey = Literal["where", "fro", "name", "as_name", "type_checking"]
HistoryGroups = Dict[Any, Union["HistoryGroups", List["ImportHistory"]]]
