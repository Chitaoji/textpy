"""
Contains tools for import analyzing: Imports.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import re
from typing import TYPE_CHECKING, List, NamedTuple, Optional

from typing_extensions import Self

if TYPE_CHECKING:
    from .abc import PyText

__all__ = []


class ImportHistory(NamedTuple):
    """Import history."""

    where: str
    fro: Optional[str]
    name: str
    as_name: Optional[str]
    type_checking: bool

    def __eq__(self, __other: Self) -> bool:
        if self.fro.startswith("."):
            return False
        return self.fro == __other.fro and self.name == __other.name

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
    obj : PyText
        `PyText` object.

    """

    def __init__(self, obj: "PyText") -> None:
        self.pytext_obj = obj
        if obj.is_dir():
            self.children = [Imports(x) for x in obj.children]
            self.history = []
            for c in self.children:
                self.history.extend(c.history)
        else:  # obj.is_file()
            self.children = []
            self.history = self.__get_history()

    def __get_history(self) -> List[ImportHistory]:
        pattern = (
            "(?: *from +)?(?:([.\\w]+) )?(?: *import +)"
            "((?:[.\\w]+(?: +as +)?(?:[.\\w]+)? *,? *)+)"
        )
        hist: List = []
        text = re.sub(
            "\nif +TYPE_CHECKING *:(\n+    .*)+(\nelse *:)?", "", self.pytext_obj.text
        )
        for line in text.splitlines():
            if matched := re.match(pattern, line):
                fro, imported = matched.groups()
                hist.append(
                    ImportHistory(self.pytext_obj.absname, fro, name, as_name, False)
                )
        return hist
