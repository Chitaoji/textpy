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
    Any,
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

from .utils.validator import SimpleValidator

if TYPE_CHECKING:
    from re import Match

    from pandas.io.formats.style import Styler

    from .abc import PyText
    from .text import PyFile
    from .utils.re_extensions import PatternStr


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
    pattern: "PatternStr"
    nline: int
    linestr: str
    extra: Any = None

    def to_tuple(self) -> Tuple["PyText", "PatternStr", int, str]:
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
        self.extra: List[Any] = []

    def __repr__(self) -> str:
        string: str = ""
        for i, res in enumerate(self.res):
            t, p, n, _line = res.to_tuple()
            string += f"\n{t.relpath}" + f":{n}" * display_params.line_numbers + ": "
            new = re.sub(
                p, partial(self._repr, extra=self.extra[i]), " " * t.spaces + _line
            )
            string += re.sub("\\\\x1b\\[", "\033[", new.__repr__())
        return string.lstrip()

    def __default_repr(self, m: "Match[str]", /, **_) -> str:
        if display_params.color_scheme == "no-color":
            return f"<{m.group()}>"
        return f"\033[100m{m.group()}\033[0m"

    def append(self, finding: TextFinding, *, extra: Any = None) -> None:
        """
        Append a new finding.

        Parameters
        ----------
        finding : TextFinding
            TextFinding object.
        extra : Any, optional
            Extra infomation, by default None.

        """
        self.res.append(finding)
        self.extra.append(extra)

    def extend(self, findings: List[TextFinding], *, extra: Any = None) -> None:
        """
        Extend a few new findings.

        Parameters
        ----------
        findings : TextFinding
            List of TextFinding objects.
        extra : Any, optional
            Extra infomation, by default None.

        """
        self.res.extend(findings)
        self.extra.extend([extra] * len(findings))

    def join(self, other: Self, *, extra: Any = None) -> None:
        """
        Joins the other instance of self.__class__.

        Parameters
        ----------
        other : Self
            The other instance.
        extra : Any, optional
            Extra infomation, by default None.

        """
        if extra is None:
            self.extend(other.res)
            self.extra.extend(other.extra)
        else:
            self.extend(other.res, extra=extra)

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
            t, p, n, _line = res.to_tuple()
            df.iloc[i, 0] = ".".join(
                [self.__style_source(x) for x in t.track()]
            ).replace(".NULL", "")
            if display_params.line_numbers:
                df.iloc[i, 0] += ":" + make_ahref(
                    f"{t.execpath}:{n}", str(n), color="inherit"
                )
            df.iloc[i, 1] = re.sub(
                p, partial(self.styl, res, extra=self.extra[i]), _line
            )
        return (
            df.style.hide(axis=0)
            .set_properties(**{"text-align": "left"})
            .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])
        )

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
    def __style_match(r: TextFinding, m: "Match[str]", /, **_) -> str:
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


class PyEditor:
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
        self.pattern: "PatternStr" = ""
        self.based_on = based_on
        self.is_based_on = False
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

    def replace(
        self, pattern: "PatternStr", repl: Union[str, Callable[["Match[str]"], str]]
    ) -> int:
        """
        Replace patterns with replacement.

        Parameters
        ----------
        pattern : PatternStr
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
        self.new_text = re.sub(
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
        self.editors: List[PyEditor] = []
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
        if not display_params.enable_styler:
            return self
        styler = self.__find_text_result.to_styler()
        setattr(styler, "confirm", self.confirm)
        setattr(styler, "rollback", self.rollback)
        setattr(styler, "to_replacer", lambda: self)
        return styler

    def to_replacer(self) -> Self:
        """
        Returns self.

        Returns
        -------
        Self
            An instance of self.

        """
        return self

    def __style(self, r: TextFinding, m: "Match[str]", /, extra: int = 0) -> str:
        url = f"{r.obj.execpath}:{r.nline}:{1+r.obj.spaces+m.start()}"
        bgc = get_bg_colors()
        before = (
            ""
            if m.group() == ""
            else make_ahref(url, m.group(), color="#cccccc", bg_color=bgc[1])
        )
        if (new := self.editors[extra].counted_repl(m)) == "":
            return before
        if display_params.color_scheme == "no-color" and before != "":
            new = "/" + new
        return before + make_ahref(url, new, color="#cccccc", bg_color=bgc[2])

    def __repr(self, m: "Match[str]", /, extra: int = 0) -> str:
        new = self.editors[extra].counted_repl(m)
        if display_params.color_scheme == "no-color":
            return f"<{m.group()}/{new}>" if new else f"<{m.group()}>"
        before = f"\033[48;5;088m{m.group()}\033[0m"
        return before + f"\033[48;5;028m{new}\033[0m" if new else before

    @cached_property
    def __find_text_result(self) -> FindTextResult:
        res = FindTextResult(stylfunc=self.__style, reprfunc=self.__repr)
        for i, e in enumerate(self.editors):
            if e.based_on:
                pyfile = e.pyfile.__class__(
                    e.based_on.new_text, path_mask=e.pyfile.path
                )
            else:
                pyfile = e.pyfile
            res.join(pyfile.findall(e.pattern, styler=False), extra=i)
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
