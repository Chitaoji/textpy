"""
Contains typing classes.

NOTE: this module is not intended to be imported at runtime.

"""

from typing import TYPE_CHECKING, Any, Literal

import loggings

from .texttree import PyDir, PyFile

if TYPE_CHECKING:

    from re_extensions._typing import PatternType, ReplType

    from .abc import Replacer
    from .imports import ImportHistory


loggings.warning("this module is not intended to be imported at runtime")

HistoryField = Literal["where", "frm", "name", "as_name", "type_check_only"]
HistoryGroups = dict[Any, "HistoryGroups | list[ImportHistory]"]
PyModule = PyDir | PyFile
