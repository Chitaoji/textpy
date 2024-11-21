"""
Contains tools for import analyzing: Imports.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import re
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional, Union

from typing_extensions import Self

from .re_extensions import quote_collapse

if TYPE_CHECKING:
    from ._typing import HistoryField, HistoryGroups
    from .abc import TextTree

__all__ = []


class ImportHistory(NamedTuple):
    """Import history."""

    where: str
    frm: Optional[str]
    name: str
    as_name: Optional[str]
    type_check_only: bool

    def __eq__(self, __other: Self) -> bool:
        if self.frm.startswith("."):
            return False
        return self.frm == __other.frm and self.name == __other.name

    def __gt__(self, __other: Self) -> bool:
        raise TypeError(
            "'>' not supported between instances of "
            f"{self.__class__.__name__!r} and {__other.__class__.__name__!r}"
        )

    def __ge__(self, __other: Self) -> bool:
        raise TypeError(
            "'<' not supported between instances of "
            f"{self.__class__.__name__!r} and {__other.__class__.__name__!r}"
        )


class Imports:
    """
    Stores the import infomation of a python module.

    Parameters
    ----------
    pymodule : TextTree
        A python module.

    """

    def __init__(self, pymodule: "TextTree") -> None:
        self.pymodule = pymodule

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} object; module={self.pymodule.absname!r}"
            f", count={len(self.history)}>"
        )

    @cached_property
    def children(self) -> List[Self]:
        """Children nodes."""
        if self.pymodule.is_dir():
            return [x.imports for x in self.pymodule.children]
        return []

    @cached_property
    def history(self) -> List[ImportHistory]:
        """Import history."""
        if self.children:
            hist = []
            for c in self.children:
                hist.extend(c.history)
            return hist
        pattern = (
            "(?: *from +)?(?:([.\\w]+) )?(?: *import +)"
            "((?:[.\\w]+(?: +as +)?(?:[.\\w]+)? *,? *)+)"
        )
        type_check_pattern = "(?:\n|^)if +TYPE_CHECKING *:(?:\n+    .*)+(?:\nelse *:)?"
        text = quote_collapse(self.pymodule.text)
        functional_text = re.sub(type_check_pattern, "", text)
        type_check_text = "".join(re.findall(type_check_pattern, text))
        hist = self.__text2hist(pattern, functional_text, False)
        hist.extend(self.__text2hist(pattern, type_check_text, True))
        return hist

    def __text2hist(
        self, pattern: str, text: str, type_check_only: bool
    ) -> List[ImportHistory]:
        hist = []
        for line in text.splitlines():
            if matched := re.match(pattern, line):
                frm, imported = matched.groups()
                for names in re.split(" *, *", imported):
                    n, a = re.match("([.\\w]+)(?: +as +)?([.\\w]+)?", names).groups()
                    hist.append(
                        ImportHistory(self.pymodule.absname, frm, n, a, type_check_only)
                    )
        return hist

    def groupby(self, *by: "HistoryField") -> "HistoryGroups":
        """
        Group the import history by some field.

        Parameters
        ----------
        *by : HistoryField
            Determines by which field(s) will the import history be grouped.

        Returns
        -------
        HistoryGroups
            Group results.

        """
        if len(by) >= 1:
            groups = self.__history_groupby(self.history, by[0])
            for key in by[1:]:
                groups = self.__history_groupby(groups, key)
            return groups
        raise ValueError("'groupby()' accepts at least 1 argument")

    @staticmethod
    def __history_groupby(
        history: Any, by: Union["HistoryField", List["HistoryField"]]
    ) -> "HistoryGroups":
        if isinstance(history, dict):
            return {k: Imports.__history_groupby(v, by) for k, v in history.items()}

        groups: Dict[Any, List[ImportHistory]] = {}
        if isinstance(by, str):
            key = ImportHistory._fields.index(by)
            for h in history:
                if (v := h[key]) not in groups:
                    groups[v] = []
                groups[v].append(h)
        else:
            keys = tuple(map(ImportHistory._fields.index, by))
            for h in history:
                values = tuple(h[k] for k in keys)
                if values not in groups:
                    groups[values] = []
                groups[values].append(h)
        return groups
