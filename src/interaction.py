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
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    get_args,
)

import pandas as pd
from typing_extensions import Self

from .re_extensions import smart_finditer, smart_split, smart_sub
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

    def defaults(self) -> Dict[str, Any]:
        """Returns the default values as a dict."""
        fields: Dict[str, "Field"] = getattr(self.__class__, "__dataclass_fields__")
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

    def astuple(self) -> Tuple["TextTree", "PatternType", int, str]:
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
        self.res: List[TextFinding] = []
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
            new = smart_sub(p, partial(self.reprfunc, res), " " * t.spaces + _line)
            string += re.sub("\\\\x1b\\[", "\033[", new.__repr__())
        return string.lstrip()

    def _repr_mimebundle_(self, *_, **__) -> Optional[Dict[str, Any]]:
        if display_params.use_mimebundle:
            return {"text/html": self.to_html()}

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
            splits = smart_split(p, _line)
            text = ""
            for j, x in enumerate(smart_finditer(p, _line)):
                text += make_plain_text(splits[j]) + self.stylfunc(res, x)
            df.iloc[i, 1] = text + make_plain_text(splits[-1])
        return df.style.hide(axis=0).set_table_styles(
            [
                {"selector": "th", "props": [("text-align", "center")]},
                {"selector": "td", "props": [("text-align", "left")]},
            ]
        )

    def to_html(self) -> str:
        """Return an HTML string for representation."""
        html_maker = HTMLTableMaker(
            index=range(len(self.res)), columns=["source", "match"]
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
            splits = smart_split(p, _line)
            text = ""
            for j, x in enumerate(smart_finditer(p, _line)):
                text += make_plain_text(splits[j]) + self.stylfunc(res, x)
            html_maker[i, 1] = text + make_plain_text(splits[-1])
        return html_maker.make()

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


@dataclass
class HTMLTableMaker:
    """
    Make an HTML table.

    Parameters
    ----------
    index : list
        Table index.
    columns : list
        Table columns.

    """

    index: list
    columns: list

    def __post_init__(self):
        self.data = [
            ["" for _ in range(len(self.columns))] for _ in range(len(self.index))
        ]

    def __getitem__(self, __key: Tuple[int, int]) -> str:
        return self.data[__key[0]][__key[1]]

    def __setitem__(self, __key: Tuple[int, int], __value: str) -> None:
        self.data[__key[0]][__key[1]] = __value

    def make(self) -> str:
        """Make a string of the HTML table."""
        tclass = display_params.table_style
        if tclass == "classic":
            tstyle = """<style type="text/css">
.table-classic th {
  text-align: center;
}
.table-classic td {
  text-align: left;
}
</style>
<table class="table-classic">"""
        else:
            tstyle = "<table>"
        thead = "\n      ".join(f"<th>{x}</th>" for x in self.columns)
        rows = []
        for x in self.data:
            row = "</td>\n      <td>".join(x)
            rows.append("    <tr>\n      <td>" + row + "</td>\n    </tr>\n")
        tbody = "".join(rows)
        return f"""{tstyle}
  <thead>
    <tr>
      {thead}
    </tr>
  </thead>
  <tbody>
{tbody}  </tbody>
</table>
"""


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
    """Text replacer, only as a return of `TextTree.replace()`."""

    def __init__(self):
        self.editors: List[FileEditor] = []
        self.__confirmed = False

    def __repr__(self) -> str:
        return repr(self.__find_text_result)

    def _repr_mimebundle_(self, *_, **__) -> Optional[Dict[str, Any]]:
        if display_params.use_mimebundle:
            return {"text/html": self.to_html()}

    def __bool__(self) -> bool:
        return bool(self.editors)

    def to_html(self) -> str:
        """Return an HTML string for representation."""
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


def make_html_tree(tree: "TextTree") -> str:
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
    if display_params.tree_style == "plain":
        tstyle = "<ul>"
    else:
        tstyle = """<style type="text/css">
.tree-vertical,
.tree-vertical ul.m,
.tree-vertical li.m {
    margin: 0;
    padding: 0;
    position: relative;
}
.tree-vertical {
    margin: 0 0 1em;
    text-align: center;
}
.tree-vertical,
.tree-vertical ul.m {
    display: table;
}
.tree-vertical ul.m {
    width: 100%;
}
.tree-vertical li.m {
    display: table-cell;
    padding: .5em 0;
    vertical-align: top;
}
.tree-vertical ul.s,
.tree-vertical li.s {
    text-align: left;
}
.tree-vertical li.m:before {
    outline: solid 1px #666;
    content: "";
    left: 0;
    position: absolute;
    right: 0;
    top: 0;
}
.tree-vertical li.m:first-child:before {
    left: 50%;
}
.tree-vertical li.m:last-child:before {
    right: 50%;
}
.tree-vertical li.m>details>summary,
.tree-vertical li.m>span {
    border: solid .1em #666;
    border-radius: .2em;
    display: inline-block;
    margin: 0 .2em .5em;
    padding: .2em .5em;
    position: relative;
}
.tree-vertical li>details>summary { 
    white-space: nowrap;
}
.tree-vertical li.m>details>summary {
    cursor: pointer;
}
.tree-vertical li.m>details>summary>span.open,
.tree-vertical li.m>details[open]>summary>span.closed {
    display: none;
}
.tree-vertical li.m>details[open]>summary>span.open {
    display: inline;
}
.tree-vertical ul.m:before,
.tree-vertical li.m>details>summary:before,
.tree-vertical li.m>span:before {
    outline: solid 1px #666;
    content: "";
    height: .5em;
    left: 50%;
    position: absolute;
}
.tree-vertical ul.m:before {
    top: -.5em;
}
.tree-vertical li.m>details>summary:before,
.tree-vertical li.m>span:before {
    top: -.56em;
    height: .45em;
}
.tree-vertical>li.m {
    margin-top: 0;
}
.tree-vertical>li.m:before,
.tree-vertical>li.m:after,
.tree-vertical>li.m>details>summary:before,
.tree-vertical>li.m>span:before {
    outline: none;
}
</style>
<ul class="tree-vertical">"""
    return f"{tstyle}\n{__get_li(tree)}\n</ul>"


def __get_li(tree: "TextTree", main: bool = True) -> str:
    triangle = (
        ""
        if display_params.tree_style == "plain"
        else '<span class="open">▼ </span><span class="closed">▶ </span>'
    )
    if tree.is_dir() and tree.children:
        tchidren = "\n".join(__get_li(x) for x in tree.children)
        return (
            f'<li class="m"><details><summary>{triangle}{make_plain_text(tree.name)}'
            f'</summary>\n<ul class="m">\n{tchidren}\n</ul>\n</details></li>'
        )

    li_class = "m" if main else "s"
    ul_class = "m" if display_params.tree_style == "vertical" else "s"
    triangle = triangle if main else ""
    if tree.children:
        tchidren = "\n".join(
            __get_li(x, main=ul_class == "m")
            for x in tree.children
            if x.name != NULL and __is_public(x.name)
        )
        if tchidren:
            name = make_plain_text(tree.name) + (".py" if tree.is_file() else "")
            return (
                f'<li class="{li_class}"><details><summary>{triangle}{name}</summary>'
                f'\n<ul class="{ul_class}">\n{tchidren}\n</ul>\n</details></li>'
            )
    name = make_plain_text(tree.name) + (".py" if tree.is_file() else "")
    return f'<li class="{li_class}"><span>{name}</span></li>'


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


def __is_public(name: str) -> bool:
    if not name.startswith("_"):
        return True
    if name.startswith("__"):
        return name.endswith(("__", "__()"))
    return False
