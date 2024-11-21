"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from .texttree import PyDir, PyFile

if TYPE_CHECKING:

    from .abc import Replacer
    from .imports import ImportHistory
    from .re_extensions._typing import PatternType, ReplType


logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)

HistoryField = Literal["where", "frm", "name", "as_name", "type_check_only"]
HistoryGroups = Dict[Any, Union["HistoryGroups", List["ImportHistory"]]]
PyModule = PyDir | PyFile


# pylint: disable=unused-argument
def _defaults(
    whole_word: bool = False,
    dotall: bool = False,
    case_sensitive: bool = True,
    regex: bool = True,
    based_on: Optional["Replacer"] = None,
) -> None: ...
