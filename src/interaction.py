"""
Contains display tools: .

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import logging
import re
from dataclasses import dataclass
from functools import cached_property, partial
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Literal, Optional, Tuple, Union

import pandas as pd
from typing_extensions import Self

if TYPE_CHECKING:
    from re import Match, Pattern

    from pandas.io.formats.style import Styler

    from .abc import PyText
    from .text import PyFile

NULL = "NULL"  # Path stems or filenames should avoid this.

__all__ = ["display_params"]


@dataclass(slots=True)
class DisplayParams:
    """
    Params for displaying.

    """

    color_scheme: Literal["dark", "modern", "high-intensty", "no-color"] = "dark"
    enable_styler: bool = True
    line_numbers: bool = True


display_params = DisplayParams()


class FindTextResult:
    """Result of text finding, only as a return of `PyText.findall()`."""

    def __init__(
        self,
        pattern: Union[str, "Pattern[str]"],
        *,
        styl: Optional[Callable] = None,
        repre: Optional[Callable] = None,
    ) -> None:
        self.res: List[Tuple[PyText, int, str]] = []
        self.pattern = pattern
        self.styl = styl
        self.repre = repre

    def __repr__(self) -> str:
        string: str = ""
        for t, n, _line in self.res:
            string += f"\n{t.relpath}" + f":{n}" * display_params.line_numbers + ": "
            f: Callable[["Match[str]"], str] = (
                self.repre if self.repre else self.__default_repr
            )
            new = re.sub(self.pattern, f, " " * t.spaces + _line)
            string += re.sub("\\\\x1b\\[", "\033[", new.__repr__())
        return string.lstrip()

    def __default_repr(self, m: "Match[str]") -> str:
        if display_params.color_scheme == "no-color":
            return f"<{m.group()}>"
        return f"\033[100m{m.group()}\033[0m"

    def append(self, finding: Tuple["PyText", int, str]) -> None:
        """
        Append a new finding.

        Parameters
        ----------
        finding : Tuple[PyText, int, str]
            Contains a `PyText` instance, the line number where pattern
            is found, and a matched string.

        """
        self.res.append(finding)

    def extend(self, findings: List[Tuple["PyText", int, str]]) -> None:
        """
        Extend a few new findings.

        Parameters
        ----------
        findings : List[Tuple[PyText, int, str]]
            A finding contains a `PyText` instance, the line number where
            pattern is found, and a matched string.

        """
        self.res.extend(findings)

    def join(self, other: Self) -> None:
        """
        Joins the other instance of self.__class__.

        Parameters
        ----------
        other : Self
            The other instance.

        """
        self.extend(other.res)

    def to_styler(self) -> "Styler":
        """
        Return a `Styler` of dataframe to beautify the representation in a
        Jupyter notebook.

        Returns
        -------
        Styler
            A `Styler` of dataframe.

        """
        df = pd.DataFrame("", index=range(len(self.res)), columns=["source", "match"])
        for i, res in enumerate(self.res):
            t, n, _line = res
            df.iloc[i, 0] = ".".join(
                [self.__style_source(x) for x in t.track()]
            ).replace(".NULL", "")
            if display_params.line_numbers:
                df.iloc[i, 0] += ":" + make_ahref(
                    f"{t.execpath}:{n}", str(n), color="inherit"
                )
            f = partial(self.styl if self.styl else self.__style_match, res)
            df.iloc[i, 1] = re.sub(self.pattern, f, _line)
        return (
            df.style.hide(axis=0)
            .set_properties(**{"text-align": "left"})
            .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])
        )

    @staticmethod
    def __style_source(x: "PyText") -> str:
        return (
            NULL
            if x.name == NULL
            else make_ahref(
                f"{x.execpath}:{x.start_line}:{1+x.spaces}", x.name, color="inherit"
            )
        )

    @staticmethod
    def __style_match(r: Tuple["PyText", int, str], m: "Match[str]") -> str:
        return (
            ""
            if m.group() == ""
            else make_ahref(
                f"{r[0].execpath}:{r[1]}:{1+r[0].spaces+m.start()}",
                m.group(),
                color="#cccccc",
                bg_color=get_bg_colors()[0],
            )
        )


class PyEditor:
    """
    Python file editor.

    Parameters
    ----------
    pyfile : PyFile
        PyFile object.
    overwrite : bool, optional
        Determines whether to overwrite the original file, by default True.

    Raises
    ------
    ValueError
        Not a python file.

    """

    def __init__(self, pyfile: "PyFile", overwrite: bool = True) -> None:
        if pyfile.path.stem == NULL:
            raise ValueError(f"not a python file: {pyfile}")
        path = pyfile.path
        if not overwrite:
            while path.exists():
                path = path.parent / (path.stem + "_copy.py")

        self.path = path
        self.pyfile = pyfile
        self.overwrite = overwrite
        self.new_text = ""
        self.__repl: Union[str, Callable[["Match[str]"], str]] = ""
        self.__count: int = 0

    def read(self) -> str:
        """
        Read text.

        Returns
        -------
        str
            Text.

        """
        return self.path.read_text(encoding=self.pyfile.encoding).strip()

    def write(self, text: str) -> None:
        """
        Write text.

        Parameters
        ----------
        text : str
            Text to write.

        """
        self.path.write_text(text + "\n", encoding=self.pyfile.encoding)

    def compare(self, text: str) -> bool:
        """
        Compares whether the file is different from `text`.

        Parameters
        ----------
        text : str
            Text to compare with.

        Returns
        -------
        bool
            Whether the file is different.

        """
        if self.overwrite:
            return self.read() == text
        return True

    def replace(
        self,
        pattern: Union[str, "Pattern[str]"],
        repl: Union[str, Callable[["Match[str]"], str]],
    ) -> int:
        """
        Replace patterns with replacement.

        Parameters
        ----------
        pattern : Union[str, Pattern[str]]
            String pattern.
        repl : Union[str, Callable[[Match[str]], str]]
            Replacement.

        Returns
        -------
        int
            How many patterns are replaced.

        """
        self.__count = 0
        self.__repl = repl
        self.new_text = re.sub(pattern, self.counted_repl, self.pyfile.text)
        return self.__count

    def counted_repl(self, x: "Match[str]") -> str:
        """Counts and returns replacement."""
        self.__count += 1
        return self.__repl if isinstance(self.__repl, str) else self.__repl(x)


class Replacer:
    """Text replacer, only as a return of `PyText.replace()`."""

    def __init__(self, pattern: Union[str, "Pattern[str]"]):
        self.editors: List[PyEditor] = []
        self.pattern = pattern
        self.__confirmed = False

    def __repr__(self) -> str:
        return repr(self.__find_text_result)

    def append(self, editor: PyEditor) -> None:
        """
        Append an editor.

        Parameters
        ----------
        editor : PyEditor
            Python file editor.

        """
        self.editors.append(editor)

    def join(self, other: Self) -> Self:
        """
        Joins the other instance of self.__class__.

        Parameters
        ----------
        other : Self
            The other instance.

        """
        self.editors.extend(other.editors)

    def confirm(self) -> Dict[str, List[str]]:
        """
        Confirm the replacement.

        NOTE: This may overwrite existing files, so be VERY CAREFUL!

        Returns
        -------
        Dict[str, List[str]]
            Infomation dictionary.

        Raises
        ------
        TypeError
            Raised when replacement is confirmed repeatedly.

        """
        if self.__confirmed:
            raise TypeError("replacement has been confirmed already")
        self.__confirmed = True
        return self.__overwrite(
            log="\nTry running 'tx.module(...).replace(...)' again."
        )

    def rollback(self, force: bool = False) -> Dict[str, List[str]]:
        """
        Rollback the replacement.

        Parameters
        ----------
        force : bool, optional
            Determines whether to forcedly rollback the files regardless
            of whether they've been modified, by default False.

        Returns
        -------
        Dict[str, List[str]]
            Infomation dictionary.

        Raises
        ------
        TypeError
            Raised when there's no need to rollback.

        """
        if not self.__confirmed:
            raise TypeError(
                "no need to rollback - replacement is not confirmed yet, "
                "or has been rolled back already"
            )
        self.__confirmed = False
        return self.__overwrite(
            rb=True, fc=force, log="\nTry running '.rollback(force=True)' again."
        )

    def __overwrite(
        self, rb: bool = False, fc: bool = False, log: str = ""
    ) -> Dict[str, List[str]]:
        info: Dict[str, List[str]] = {"successful": [], "failed": []}
        for e in self.editors:
            if fc or e.compare(e.new_text if rb else e.pyfile.text):
                e.write(e.pyfile.text if rb else e.new_text)
                info["successful"].append(str(e.path))
            else:
                info["failed"].append(str(e.path))
        if info["failed"]:
            logging.warning(
                "failed to overwrite the following files because they've "
                "been modified since last time:\n    - %s%s",
                "\n    - ".join(info["failed"]),
                log,
            )
        return info

    def to_styler(self) -> "Styler":
        """
        Return a `Styler` of dataframe to beautify the representation in a
        Jupyter notebook.

        Returns
        -------
        Styler
            A `Styler` of dataframe.

        """
        styler = self.__find_text_result.to_styler()
        setattr(styler, "confirm", self.confirm)
        setattr(styler, "rollback", self.rollback)
        return styler

    def __style_repl(self, r: Tuple["PyText", int, str], m: "Match[str]") -> str:
        url = f"{r[0].execpath}:{r[1]}:{1+r[0].spaces+m.start()}"
        bgc = get_bg_colors()
        before = (
            ""
            if m.group() == ""
            else make_ahref(url, m.group(), color="#cccccc", bg_color=bgc[1])
        )
        if (new := self.editors[0].counted_repl(m)) == "":
            return before
        if display_params.color_scheme == "no-color" and before != "":
            new = "/" + new
        return before + make_ahref(url, new, color="#cccccc", bg_color=bgc[2])

    def __repr_repl(self, m: "Match[str]") -> str:
        new = self.editors[0].counted_repl(m)
        if display_params.color_scheme == "no-color":
            return f"<{m.group()}/{new}>" if new else f"<{m.group()}>"
        before = f"\033[48;5;088m{m.group()}\033[0m"
        return before + f"\033[48;5;028m{new}\033[0m" if new else before

    @cached_property
    def __find_text_result(self) -> FindTextResult:
        res = FindTextResult(
            self.pattern, styl=self.__style_repl, repre=self.__repr_repl
        )
        for e in self.editors:
            res.join(e.pyfile.findall(self.pattern, styler=False))
        return res


def make_ahref(
    url: str, text: str, color: Optional[str] = None, bg_color: Optional[str] = None
) -> str:
    """
    Makes an HTML <a> tag.

    Parameters
    ----------
    url : str
        URL to link.
    text : str
        Text to display.
    color : str, optional
        Text color, by default None.
    bg_color : str, optional
        Background color, by default None.

    Returns
    -------
    str
        An HTML <a> tag.

    """
    style: str = "text-decoration:none"
    if color is not None:
        style += f";color:{color}"
    if bg_color is not None:
        style += f";background-color:{bg_color}"
    if Path(url).stem == NULL:
        href = ""
    else:
        href = f"href='{url}' "
    return f"<a {href}style='{style}'>{text}</a>"


def get_bg_colors() -> Tuple[str, str, str]:
    """
    Get background colors.

    Returns
    -------
    Tuple[str,str,str]
        Background colors.

    Raises
    ------
    ValueError
        Unrecognized color-scheme.

    """
    if display_params.color_scheme == "dark":
        return ["#505050", "#4d2f2f", "#2f4d2f"]
    if display_params.color_scheme == "modern":
        return ["#505050", "#701414", "#4e5d2d"]
    if display_params.color_scheme == "high-intensty":
        return ["#505050", "#701414", "#147014"]
    if display_params.color_scheme == "no-color":
        return ["#505050", "#505050", "#505050"]
    raise ValueError(f"unrecognized color-scheme: {display_params.color_scheme!r}")
