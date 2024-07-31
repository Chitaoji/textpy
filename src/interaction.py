"""
Contains interaction tools: display_params().

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import logging
import re
from dataclasses import dataclass
from functools import cached_property, partial
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    get_args,
)

import pandas as pd
from typing_extensions import Self

from .utils.re_extensions import smart_sub
from .utils.validator import SimpleValidator

if TYPE_CHECKING:
    from re import Match

    from pandas.io.formats.style import Styler

    from .abc import PyText
    from .text import PyFile
    from .utils.re_extensions import PatternType, ReplType


__all__ = ["display_params"]

NULL = "NULL"  # Path stems or filenames should avoid this.
ColorSchemeStr = Literal["dark", "modern", "high-intensty", "no-color"]


@dataclass
class DisplayParams:
    """
    Params for displaying.

    """

    color_scheme: ColorSchemeStr = SimpleValidator(
        literal=get_args(ColorSchemeStr), default="dark"
    )
    enable_styler: bool = SimpleValidator(bool, default=True)
    line_numbers: bool = SimpleValidator(bool, default=True)


display_params = DisplayParams()


@dataclass
class TextFinding:
    """Finding of text."""

    obj: "PyText"
    pattern: "PatternType"
    nline: int
    linestr: str
    order: int = 0

    def __eq__(self, __other: Self) -> bool:
        return (
            self.obj == __other.obj
            and self.nline == __other.nline
            and self.order == __other.order
        )

    def __gt__(self, __other: Self) -> bool:
        if self.obj > __other.obj:
            return True
        if self.obj == __other.obj:
            if self.nline > __other.nline:
                return True
            if self.nline == __other.nline and self.order > __other.order:
                return True
        return False

    def __ge__(self, __other: Self) -> bool:
        return self == __other or self > __other

    def to_tuple(self) -> Tuple["PyText", "PatternType", int, str]:
        """To tuple."""
        return self.obj, self.pattern, self.nline, self.linestr


class FindTextResult:
    """Result of text finding, only as a return of `PyText.findall()`."""

    def __init__(
        self,
        *,
        stylfunc: Optional[Callable] = None,
        reprfunc: Optional[Callable] = None,
    ) -> None:
        self.res: List[TextFinding] = []
        self.styl = stylfunc if stylfunc else self.__style_match
        self._repr = reprfunc if reprfunc else self.__default_repr

    def __repr__(self) -> str:
        string: str = ""
        for res in sorted(self.res):
            t, p, n, _line = res.to_tuple()
            string += f"\n{t.relpath}" + f":{n}" * display_params.line_numbers + ": "
            new = smart_sub(p, partial(self._repr, res), " " * t.spaces + _line)
            string += re.sub("\\\\x1b\\[", "\033[", new.__repr__())
        return string.lstrip()

    def __bool__(self) -> bool:
        return bool(self.res)

    def append(self, finding: TextFinding) -> None:
        """
        Append a new finding.

        Parameters
        ----------
        finding : TextFinding
            TextFinding object.

        """
        self.res.append(finding)

    def extend(self, findings: List[TextFinding]) -> None:
        """
        Extend a few new findings.

        Parameters
        ----------
        findings : TextFinding
            List of TextFinding objects.

        """
        self.res.extend(findings)

    def set_order(self, n: int) -> None:
        """
        Set order numbers.

        Parameters
        ----------
        n : int
            Order number.

        """
        for r in self.res:
            r.order = n

    def join(self, other: Self) -> None:
        """
        Joins the other instance of self.__class__.

        Parameters
        ----------
        other : Self
            The other instance.

        """
        self.extend(other.res)

    def to_styler(self) -> Union["Styler", Self]:
        """
        Return a `Styler` of dataframe to beautify the representation in a
        Jupyter notebook.

        Returns
        -------
        Union[Styler, Self]
            A `Styler` or an instance of self.

        """
        if not display_params.enable_styler or pd.__version__ < "1.4.0":
            return self
        df = pd.DataFrame("", index=range(len(self.res)), columns=["source", "match"])
        for i, res in enumerate(sorted(self.res)):
            t, p, n, _line = res.to_tuple()
            df.iloc[i, 0] = ".".join(
                [self.__style_source(x) for x in t.track()]
            ).replace(".NULL", "")
            if display_params.line_numbers:
                df.iloc[i, 0] += ":" + make_ahref(
                    f"{t.execpath}:{n}", str(n), color="inherit"
                )
            df.iloc[i, 1] = smart_sub(p, partial(self.styl, res), _line)
        styler = (
            df.style.hide(axis=0)
            .set_properties(**{"text-align": "left"})
            .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])
        )
        setattr(styler, "getself", lambda: self)
        return styler

    def getself(self) -> Self:
        """
        Returns self.

        Returns
        -------
        Self
            An instance of self.

        """
        return self

    @staticmethod
    def __default_repr(_: TextFinding, m: "Match[str]", /) -> str:
        if display_params.color_scheme == "no-color":
            return f"<{m.group()}>"
        return f"\033[100m{m.group()}\033[0m"

    @staticmethod
    def __style_source(x: "PyText", /) -> str:
        return (
            NULL
            if x.name == NULL
            else make_ahref(
                f"{x.execpath}:{x.start_line}:{1+x.spaces}", x.name, color="inherit"
            )
        )

    @staticmethod
    def __style_match(r: TextFinding, m: "Match[str]", /) -> str:
        return (
            ""
            if m.group() == ""
            else make_ahref(
                f"{r.obj.execpath}:{r.nline}:{1+r.obj.spaces+m.start()}",
                m.group(),
                color="#cccccc",
                bg_color=get_bg_colors()[0],
            )
        )


class FileEditor:
    """
    Python file editor.

    Parameters
    ----------
    pyfile : PyFile
        PyFile object.
    overwrite : bool, optional
        Determines whether to overwrite the original file, by default True.
    based_on : Self, optional
        Specifies another editor to base on.

    Raises
    ------
    ValueError
        Not a python file.

    """

    def __init__(
        self, pyfile: "PyFile", overwrite: bool = True, based_on: Optional[Self] = None
    ) -> None:
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
        self.pattern: "PatternType" = ""
        self.based_on = based_on
        self.is_based_on = False
        self.__repl: "ReplType" = ""
        self.__count: int = 0

    def __bool__(self) -> bool:
        return self.__count > 0

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
        if not self.is_based_on:
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

    def replace(self, pattern: "PatternType", repl: "ReplType") -> int:
        """
        Replace patterns with replacement.

        Parameters
        ----------
        pattern : PatternType
            String pattern.
        repl : ReplType
            Replacement.

        Returns
        -------
        int
            How many patterns are replaced.

        """
        self.__count = 0
        self.__repl = repl
        self.new_text = smart_sub(
            pattern,
            self.counted_repl,
            self.based_on.new_text if self.based_on else self.pyfile.text,
        )
        self.pattern = pattern
        if self.__count > 0 and self.based_on:
            self.based_on.is_based_on = True
        return self.__count

    def counted_repl(self, x: "Match[str]") -> str:
        """Counts and returns replacement."""
        self.__count += 1
        return self.__repl if isinstance(self.__repl, str) else self.__repl(x)


class Replacer:
    """Text replacer, only as a return of `PyText.replace()`."""

    def __init__(self):
        self.editors: List[FileEditor] = []
        self.__confirmed = False

    def __repr__(self) -> str:
        return repr(self.__find_text_result)

    def __bool__(self) -> bool:
        return bool(self.editors)

    def append(self, editor: FileEditor) -> None:
        """
        Append an editor.

        Parameters
        ----------
        editor : FileEditor
            Python file editor.

        """
        self.editors.append(editor)

    def join(self, other: Self) -> None:
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
            if e.is_based_on:
                continue
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

    def to_styler(self) -> Union["Styler", Self]:
        """
        Return a `Styler` of dataframe to beautify the representation in a
        Jupyter notebook.

        Returns
        -------
        Union[Styler, Self]
            A `Styler` or an instance of self.

        """
        if not display_params.enable_styler or pd.__version__ < "1.4.0":
            return self
        styler = self.__find_text_result.to_styler()
        setattr(styler, "confirm", self.confirm)
        setattr(styler, "rollback", self.rollback)
        setattr(styler, "getself", lambda: self)
        return styler

    def getself(self) -> Self:
        """
        Returns self.

        Returns
        -------
        Self
            An instance of self.

        """
        return self

    def __style(self, r: TextFinding, m: "Match[str]", /) -> str:
        url = f"{r.obj.execpath}:{r.nline}:{1+r.obj.spaces+m.start()}"
        bgc = get_bg_colors()
        before = (
            ""
            if m.group() == ""
            else make_ahref(url, m.group(), color="#cccccc", bg_color=bgc[1])
        )
        if (new := self.editors[r.order].counted_repl(m)) == "":
            return before
        if display_params.color_scheme == "no-color" and before != "":
            new = "/" + new
        return before + make_ahref(url, new, color="#cccccc", bg_color=bgc[2])

    def __repr(self, r: TextFinding, m: "Match[str]", /) -> str:
        new = self.editors[r.order].counted_repl(m)
        if display_params.color_scheme == "no-color":
            return f"<{m.group()}/{new}>" if new else f"<{m.group()}>"
        before = f"\033[48;5;088m{m.group()}\033[0m"
        return before + f"\033[48;5;028m{new}\033[0m" if new else before

    @cached_property
    def __find_text_result(self) -> FindTextResult:
        res = FindTextResult(stylfunc=self.__style, reprfunc=self.__repr)
        for i, e in enumerate(self.editors):
            if e.based_on:
                pyfile = e.pyfile.__class__(e.based_on.new_text, mask=e.pyfile)
            else:
                pyfile = e.pyfile
            new_res = pyfile.findall(e.pattern, styler=False)
            new_res.set_order(i)
            res.join(new_res)
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

    """
    if display_params.color_scheme == "dark":
        return ["#505050", "#4d2f2f", "#2f4d2f"]
    if display_params.color_scheme == "modern":
        return ["#505050", "#701414", "#4e5d2d"]
    if display_params.color_scheme == "high-intensty":
        return ["#505050", "#701414", "#147014"]
    return ["#505050", "#505050", "#505050"]
