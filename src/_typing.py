"""
Contains typing classes.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Literal, Union

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from re import Match, Pattern, RegexFlag

    from hintwith import hintwith

    from .imports import ImportHistory
    from .utils.re_extensions import (
        SmartMatch,
        SmartPattern,
        line_findall,
        lsplit,
        real_findall,
        rsplit,
        smart_findall,
        smart_fullmatch,
        smart_match,
        smart_search,
        smart_split,
        smart_sub,
        smart_subn,
    )

logging.warning(
    "importing from '._typing' - this module is not intended for direct import, "
    "therefore unexpected errors may occur"
)
PatternType = Union[str, "Pattern[str]", "SmartPattern[str]"]
MatchType = Union["Match[str]", "SmartMatch[str]", None]
ReplType = Union[str, Callable[["Match[str]"], str]]
FlagType = Union[int, "RegexFlag"]
HistoryKey = Literal["where", "fro", "name", "as_name", "type_checking"]
HistoryGroups = Dict[Any, Union["HistoryGroups", List["ImportHistory"]]]


class Smart:
    """Namespace for smart operations."""

    Pattern: TypeAlias = "SmartPattern"
    Match: TypeAlias = "SmartMatch"

    if TYPE_CHECKING:
        # pylint: disable=missing-function-docstring
        @staticmethod
        @hintwith(smart_search, True)
        def search(): ...
        @staticmethod
        @hintwith(smart_match, True)
        def match(): ...
        @staticmethod
        @hintwith(smart_fullmatch, True)
        def fullmatch(): ...
        @staticmethod
        @hintwith(smart_sub, True)
        def sub(): ...
        @staticmethod
        @hintwith(smart_subn, True)
        def subn(): ...
        @staticmethod
        @hintwith(smart_split, True)
        def split(): ...
        @staticmethod
        @hintwith(rsplit, True)
        def rsplit(): ...
        @staticmethod
        @hintwith(lsplit, True)
        def lsplit(): ...
        @staticmethod
        @hintwith(smart_findall, True)
        def findall(): ...
        @staticmethod
        @hintwith(line_findall, True)
        def line_findall(): ...
        @staticmethod
        @hintwith(real_findall, True)
        def real_findall(): ...

        # pylint: enable=missing-function-docstring
