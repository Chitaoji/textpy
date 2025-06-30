"""
Contains typing classes.

NOTE: this module is not intended to be imported at runtime.

"""

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Union

import loggings

from .texttree import PyDir, PyFile

if TYPE_CHECKING:

    from .abc import Replacer
    from .imports import ImportHistory
    from .re_extensions._typing import PatternType, ReplType


loggings.warning("this module is not intended to be imported at runtime")

HistoryField = Literal["where", "frm", "name", "as_name", "type_check_only"]
HistoryGroups = Dict[Any, Union["HistoryGroups", List["ImportHistory"]]]
PyModule = PyDir | PyFile
