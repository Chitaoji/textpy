"""
Contains interaction tools: display_params.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import logging
import re
from dataclasses import dataclass
from functools import cached_property, partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Literal, Optional, get_args

import pandas as pd
from htmlmaster import HTMLTableMaker, HTMLTreeMaker
from re_extensions import smart
from typing_extensions import Self

from .css import TABLE_CSS_STYLE, TREE_CSS_STYLE
from .utils.validator import SimpleValidator

if TYPE_CHECKING:
    from dataclasses import Field
    from re import Match

    from pandas.io.formats.style import Styler

    from ._typing import PatternType, ReplType
    from .abc import TextTree
    from .texttree import PyFile


__all__ = ["display_params"]

NULL = "NULL"  # Path stems or filenames should avoid this.
ColorSchemeStr = Literal["dark", "modern", "high-intensty", "no-color"]
TreeStyleStr = Literal["mixed", "vertical", "plain"]
TableStyleStr = Literal["classic", "plain"]


@dataclass
class DisplayParams:
    """Parameters for displaying."""

    color_scheme: ColorSchemeStr = SimpleValidator(
        str, literal=get_args(ColorSchemeStr), default="dark"
    )
    tree_style: TreeStyleStr = SimpleValidator(
        str, literal=get_args(TreeStyleStr), default="mixed"
    )
    table_style: TableStyleStr = SimpleValidator(
        str, literal=get_args(TableStyleStr), default="classic"
    )
    use_mimebundle: bool = SimpleValidator(bool, default=True)
    skip_line_numbers: bool = SimpleValidator(bool, default=False)

    def defaults(self) -> dict[str, Any]:
        """Returns the default values as a dict."""
        fields: dict[str, "Field"] = getattr(self.__class__, "__dataclass_fields__")
        return {k: getattr(v.default, "default") for k, v in fields.items()}


display_params = DisplayParams()


@dataclass
class TextFinding:
    """Finding of text."""

    obj: "TextTree"
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

    def astuple(self) -> tuple["TextTree", "PatternType", int, str]:
        """Converts `self` to a tuple."""
        return self.obj, self.pattern, self.nline, self.linestr


class FindTextResult:
    """Result of text finding, only as a return of `TextTree.findall()`."""

    def __init__(
        self,
        *,
        stylfunc: Optional[Callable] = None,
        reprfunc: Optional[Callable] = None,
    ) -> None:
        self.res: list[TextFinding] = []
        self.stylfunc = stylfunc if stylfunc else self.__style_match
        self.reprfunc = reprfunc if reprfunc else self.__default_repr

    def __repr__(self) -> str:
        string: str = ""
        for res in sorted(self.res):
            t, p, n, _line = res.astuple()
            if display_params.skip_line_numbers:
                string += f"\n{t.relpath}: "
            else:
                string += f"\n{t.relpath}:{n}: "
            new = smart.sub(p, partial(self.reprfunc, res), " " * t.spaces + _line)
            string += re.sub("\\\\x1b\\[", "\033[", new.__repr__())
        return string.lstrip()

    def _repr_mimebundle_(self, *_, **__) -> Optional[dict[str, str]]:
        if display_params.use_mimebundle:
            return {"text/html": self.to_html().make()}
        return None

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

    def extend(self, findings: list[TextFinding]) -> None:
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

    def to_styler(self) -> "Styler":
        """
        Return a pandas styler for representation.

        Returns
        -------
        Styler
            Pandas styler.

        """
        df = pd.DataFrame("", index=range(len(self.res)), columns=["source", "match"])
        for i, res in enumerate(sorted(self.res)):
            t, p, n, _line = res.astuple()
            df.iloc[i, 0] = ".".join(
                [self.__style_source(x) for x in t.track()]
            ).replace(".NULL", "")
            if not display_params.skip_line_numbers:
                df.iloc[i, 0] += ":" + make_ahref(
                    f"{t.execpath}:{n}", str(n), color="inherit"
                )
            splits = smart.split(p, _line)
            text = ""
            for j, x in enumerate(smart.finditer(p, _line)):
                text += make_plain_text(splits[j]) + self.stylfunc(res, x)
            df.iloc[i, 1] = text + make_plain_text(splits[-1])
        return df.style.hide(axis=0).set_table_styles(
            [
                {"selector": "th", "props": [("text-align", "center")]},
                {"selector": "td", "props": [("text-align", "left")]},
            ]
        )

    def to_html(self) -> HTMLTableMaker:
        """Return an HTML text for representing self."""
        tclass = (
            "textpy-table-classic"
            if display_params.table_style == "classic"
            else "textpy-table-plain"
        )
        style = TABLE_CSS_STYLE if display_params.table_style == "classic" else ""
        html_maker = HTMLTableMaker(
            index=range(len(self.res)),
            columns=["source", "match"],
            maincls=tclass,
            style=style,
        )
        for i, res in enumerate(sorted(self.res)):
            t, p, n, _line = res.astuple()
            html_maker[i, 0] = ".".join(
                [self.__style_source(x) for x in t.track()]
            ).replace(".NULL", "")
            if not display_params.skip_line_numbers:
                html_maker[i, 0] += ":" + make_ahref(
                    f"{t.execpath}:{n}", str(n), color="inherit"
                )
            splits = smart.split(p, _line)
            text = ""
            for j, x in enumerate(smart.finditer(p, _line)):
                text += make_plain_text(splits[j]) + self.stylfunc(res, x)
            html_maker[i, 1] = text + make_plain_text(splits[-1])
        return html_maker

    @staticmethod
    def __default_repr(_: TextFinding, m: "Match[str]", /) -> str:
        if display_params.color_scheme == "no-color":
            return f"<{m.group()}>"
        return f"\033[100m{m.group()}\033[0m"

    @staticmethod
    def __style_source(x: "TextTree", /) -> str:
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
                make_plain_text(m.group()),
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
        Editor to be based on.

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
        self.new_text = smart.sub(
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
    """Text replacer, only as a return of `TextTree.replace()`."""

    def __init__(self):
        self.editors: list[FileEditor] = []
        self.__confirmed = False

    def __repr__(self) -> str:
        return repr(self.__find_text_result)

    def _repr_mimebundle_(self, *_, **__) -> Optional[dict[str, str]]:
        if display_params.use_mimebundle:
            return {"text/html": self.to_html().make()}
        return None

    def __bool__(self) -> bool:
        return bool(self.editors)

    def to_html(self) -> HTMLTableMaker:
        """Return an HTML text for representing self."""
        return self.__find_text_result.to_html()

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

    def confirm(self) -> dict[str, list[str]]:
        """
        Confirm the replacement.

        NOTE: This may overwrite existing files, so be VERY CAREFUL!

        Returns
        -------
        dict[str, list[str]]
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

    def rollback(self, force: bool = False) -> dict[str, list[str]]:
        """
        Rollback the replacement.

        Parameters
        ----------
        force : bool, optional
            Determines whether to forcedly rollback the files regardless
            of whether they've been modified, by default False.

        Returns
        -------
        dict[str, list[str]]
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
    ) -> dict[str, list[str]]:
        info: dict[str, list[str]] = {"successful": [], "failed": []}
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

    def __style(self, r: TextFinding, m: "Match[str]", /) -> str:
        url = f"{r.obj.execpath}:{r.nline}:{1+r.obj.spaces+m.start()}"
        bgc = get_bg_colors()
        before = (
            ""
            if m.group() == ""
            else make_ahref(
                url, make_plain_text(m.group()), color="#cccccc", bg_color=bgc[1]
            )
        )
        if (new := self.editors[r.order].counted_repl(m)) == "":
            return before
        if display_params.color_scheme == "no-color" and before != "":
            new = "/" + new
        return before + make_ahref(
            url, make_plain_text(new), color="#cccccc", bg_color=bgc[2]
        )

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
            new_res = pyfile.findall(e.pattern)
            new_res.set_order(i)
            res.join(new_res)
        return res


def make_html_tree(tree: "TextTree") -> HTMLTreeMaker:
    """
    Make an HTML tree.

    Parameters
    ----------
    tree : TextTree
        A python module / class / function / method.

    Returns
    -------
    str
        Html string.

    """
    maker = __make_node(tree)
    if display_params.tree_style == "plain":
        maker.set_maincls("textpy-tree-plain")
    else:
        maker.set_maincls("textpy-tree-vertical")
        maker.setstyle(TREE_CSS_STYLE)
    return maker


def __make_node(tree: "TextTree", main: bool = True) -> HTMLTreeMaker:
    triangle = (
        ""
        if display_params.tree_style == "plain"
        else '<span class="open">▼ </span><span class="closed">▶ </span>'
    )
    if tree.is_dir() and tree.children:
        maker = HTMLTreeMaker(f"{triangle}{make_plain_text(tree.name)}", level_open=0)
        for x in tree.children:
            maker.add(__make_node(x))
        return maker

    li_class = "m" if main else "s"
    ul_class = "m" if display_params.tree_style == "vertical" else "s"
    triangle = triangle if main else ""
    if tree.children:
        maker = HTMLTreeMaker(licls=li_class, ulcls=ul_class, level_open=0)
        for x in tree.children:
            if x.name != NULL and __is_public(x.name):
                maker.add(__make_node(x, main=ul_class == "m"))
        if maker.has_child():
            name = make_plain_text(tree.name) + (".py" if tree.is_file() else "")
            maker.setval(f"{triangle}{name}")
            return maker
    name = make_plain_text(tree.name) + (".py" if tree.is_file() else "")
    return HTMLTreeMaker(name, li_class, level_open=0)


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
        href = f'href="{url}" '
    return f'<a {href}style="{style}">{text}</a>'


def make_plain_text(text: str) -> str:
    """Turn HTML entities into plain text."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def get_bg_colors() -> tuple[str, str, str]:
    """
    Get background colors.

    Returns
    -------
    tuple[str,str,str]
        Background colors.

    """
    if display_params.color_scheme == "dark":
        return ["#505050", "#4d2f2f", "#2f4d2f"]
    if display_params.color_scheme == "modern":
        return ["#505050", "#701414", "#4e5d2d"]
    if display_params.color_scheme == "high-intensty":
        return ["#505050", "#701414", "#147014"]
    return ["#505050", "#505050", "#505050"]


def __is_public(name: str) -> bool:
    if not name.startswith("_"):
        return True
    if name.startswith("__"):
        return name.endswith(("__", "__()"))
    return False
