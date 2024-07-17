"""
Contains abstract classes: PyText and Docstring.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import re
from abc import ABC, abstractmethod
from functools import cached_property, partial
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Union,
    cast,
    overload,
)

import pandas as pd
from typing_extensions import ParamSpec, Self

from .utils.re_extensions import pattern_inreg, real_findall

if TYPE_CHECKING:
    from re import Match, Pattern

    from pandas.io.formats.style import Styler

    from .text import PyFile


__all__ = ["PyText", "Docstring"]

NULL = "NULL"  # Path stems or filenames should avoid this.
P = ParamSpec("P")


class PyText(ABC, Generic[P]):
    """
    Could be a python module, file, class, function, or method.

    Parameters
    ----------
    path_or_text : Union[Path, str]
        File path, module path or file text.
    parent : PyText, optional
        Parent node (if exists), by default None.
    start_line : int, optional
        Starting line number, by default 1.
    home : Union[Path, str, None], optional
        Specifies the home path if `path_or_text` is relative, by default None.
    encoding : str, optional
        Specifies encoding, by default None.

    """

    def __init__(
        self,
        path_or_text: Union[Path, str],
        parent: Optional["PyText"] = None,
        start_line: int = 1,
        home: Union[Path, str, None] = None,
        encoding: Optional[str] = None,
    ) -> None:
        self.text: str = ""
        self.name: str = ""
        self.path: Path = Path(NULL + ".py")

        self.parent = parent
        self.start_line = start_line
        self.home = as_path(Path(""), home=home)
        self.encoding = encoding
        self.spaces = 0

        self._header: Optional[str] = None
        self.text_init(path_or_text)

    def __repr__(self) -> None:
        return f"{self.__class__.__name__}({self.absname!r})"

    def __truediv__(self, __value: "str") -> "PyText":
        return self.jumpto(__value)

    @abstractmethod
    def text_init(self, path_or_text: Union[Path, str]) -> None:
        """
        Initialize the instance.

        Parameters
        ----------
        path_or_text : Union[Path, str]
            File path, module path or file text.

        """

    @cached_property
    @abstractmethod
    def doc(self) -> "Docstring":
        """
        Docstring of a function / class / method.

        Returns
        -------
        Docstring
            An instance of `Docstring`.

        """

    @cached_property
    @abstractmethod
    def header(self) -> "PyText":
        """
        Header of a file / function / class / method.

        Returns
        -------
        PyText
            An instance of `PyText`.

        """

    @cached_property
    def children(self) -> List["PyText"]:
        """
        Children nodes.

        Returns
        -------
        Dict[str, PyText]
            List of the children nodes.

        """
        return []

    @cached_property
    def children_names(self) -> List[str]:
        """
        Children names.

        Returns
        -------
        List[str]
            List of the children nodes' names.

        """
        return [x.name for x in self.children]

    @cached_property
    def children_dict(self) -> Dict[str, "PyText"]:
        """
        Dictionary of children nodes.

        Returns
        -------
        Dict[str, PyText]
            Dictionary of children nodes.

        """
        children_dict: Dict[str, "PyText"] = {}
        for child, childname in zip(self.children, self.children_names):
            children_dict[childname] = child
        return children_dict

    @cached_property
    def absname(self) -> str:
        """
        The full-name including all the parent's name, connected with dots.

        Returns
        -------
        str
            The absolute name.

        """
        if self.parent is None:
            return self.name
        else:
            return self.parent.absname + ("." + self.name).replace(".NULL", "")

    @cached_property
    def relname(self) -> str:
        """
        Differences to `absname` that it doesn't include the top parent's name.

        Returns
        -------
        str
            The relative name.

        """
        return self.absname.split(".", maxsplit=1)[-1]

    @cached_property
    def abspath(self) -> Path:
        """
        The absolute path of `self`.

        Returns
        -------
        Path
            The absolute path.

        """
        if self.path.stem == NULL:
            return self.path if self.parent is None else self.parent.abspath
        else:
            return self.path.absolute()

    @cached_property
    def relpath(self) -> Path:
        """
        Find the relative path to `home`.

        Returns
        -------
        Path
            The relative path.

        """
        try:
            return self.abspath.relative_to(self.home.absolute())
        except ValueError:
            return self.abspath

    @cached_property
    def execpath(self) -> Path:
        """
        Find the relative path to the working environment.

        Returns
        -------
        Path
            The relative path to the working environment.

        """
        try:
            return self.abspath.relative_to(self.abspath.cwd())
        except ValueError:
            return self.abspath

    @overload
    def findall(
        self,
        pattern: Union[str, "Pattern[str]"],
        /,
        *_: P.args,
        **kwargs: P.kwargs,
    ) -> "FindTextResult": ...
    def findall(
        self, pattern, /, styler=True, line_numbers=True, **kwargs
    ) -> "FindTextResult":
        """
        Finds all non-overlapping matches of `pattern`.

        Parameters
        ----------
        pattern : Union[str, Pattern[str]]
            String pattern.
        whole_word : bool, optional
            Whether to match whole words only, by default False.
        case_sensitive : bool, optional
            Specifies case sensitivity, by default True.
        regex : bool, optional
            Whether to enable regular expressions, by default True.
        styler : bool, optional
            Whether to use a `Styler` object to beautify the representation
            of result in a Jupyter notebook, this only takes effect when
            `pandas.__version__ >= 1.4.0`, by default True.
        line_numbers : bool, optional
            Whether to display line numbers in the result, by default True.

        Returns
        -------
        FindTextResult
            Searching result.

        """
        pattern = self.__pattern_trans(pattern, **kwargs)
        res = FindTextResult(pattern, line_numbers)
        if not self.children:
            for nline, _, group in real_findall(
                ".*" + pattern.pattern + ".*",
                self.text,
                linemode=True,
                flags=pattern.flags,
            ):
                if group != "":
                    res.append((self, self.start_line + nline - 1, group))
        else:
            res.join(self.header.findall(pattern, styler=False))
            for c in self.children:
                res.join(c.findall(pattern, styler=False))
        return res.to_styler() if styler and pd.__version__ >= "1.4.0" else res

    @overload
    def replace(
        self,
        pattern: Union[str, "Pattern[str]"],
        repl: Union[str, Callable[["Match[str]"], str]],
        overwrite: bool = True,
        /,
        *_: P.args,
        **kwargs: P.kwargs,
    ) -> "Replacer": ...
    def replace(
        self, pattern, repl, /, overwrite=True, styler=True, line_numbers=True, **kwargs
    ) -> "Replacer":
        """
        Finds all non-overlapping matches of `pattern`, and replace them with
        `repl`. If you want the replacement to take effect in actual files, use
        `.confirm()` immediately after this method (e.g.
        `obj.replace("a", "b").confirm()`).

        Parameters
        ----------
        pattern : Union[str, Pattern[str]]
            String pattern.
        repl : Union[str, Callable[[str], str]]
            Speficies the string to replace the patterns. If Callable, should
            be a function that receives the Match object, and gives back
            the replacement string to be used.
        overwrite : bool, optional
            Specifies whether to overwrite the original file, by default True.
        whole_word : bool, optional
            Whether to match whole words only, by default False.
        case_sensitive : bool, optional
            Specifies case sensitivity, by default True.
        regex : bool, optional
            Whether to enable regular expressions, by default True.
        styler : bool, optional
            Whether to use a `Styler` object to beautify the representation
            of result in a Jupyter notebook, this only takes effect when
            `pandas.__version__ >= 1.4.0`, by default True.
        line_numbers : bool, optional
            Whether to display line numbers in the result, by default True.

        Returns
        -------
        Replacer
            Text replacer.

        """
        pattern = self.__pattern_trans(pattern, **kwargs)
        replacer = Replacer(pattern, line_numbers)
        if self.path.suffix == ".py":
            editor = PyEditor(self, overwrite=overwrite)
            if editor.replace(pattern, repl) > 0:
                replacer.append(editor)
        else:
            for c in self.children:
                replacer.join(
                    c.replace(
                        pattern, repl, overwrite=overwrite, styler=False, **kwargs
                    )
                )
        if styler:
            return cast("Replacer", replacer.to_styler())
        return replacer

    @staticmethod
    def __pattern_trans(
        pattern: Union[str, "Pattern[str]"],
        whole_word: bool = False,
        case_sensitive: bool = True,
        regex: bool = True,
    ) -> "Pattern[str]":
        flags: int = 0
        if isinstance(pattern, re.Pattern):
            pattern, flags = str(pattern.pattern), pattern.flags
        if not regex:
            pattern = pattern_inreg(pattern)
        if not case_sensitive:
            flags = flags | re.I
        if whole_word:
            pattern = "\\b" + pattern + "\\b"
        pattern = re.compile(pattern, flags=flags)
        return pattern

    def jumpto(self, target: str) -> "PyText":
        """
        Jump to another `PyText` instance.

        Parameters
        ----------
        target : str
            Relative name of the target instance.

        Returns
        -------
        PyText
            An instance of `PyText`.

        Raises
        ------
        ValueError
            Raised when `target` doesn't exist.

        """
        if target == "":
            return self
        splits = re.split("\\.", target, maxsplit=1)
        if len(splits) == 1:
            splits.append("")
        if splits[0] == "":
            if self.parent is not None:
                return self.parent.jumpto(splits[1])
            raise ValueError(f"'{self.absname}' hasn't got a parent")
        elif splits[0] in self.children_dict:
            return self.children_dict[splits[0]].jumpto(splits[1])
        elif self.name == splits[0]:
            return self.jumpto(splits[1])
        else:
            raise ValueError(f"'{splits[0]}' is not a child of '{self.absname}'")

    def track(self) -> List["PyText"]:
        """
        Returns a list of all the parents and `self`.

        Returns
        -------
        List[PyText]
            List of `PyText` instances.

        """
        track: List["PyText"] = []
        obj: Optional["PyText"] = self
        while obj is not None:
            track.append(obj)
            obj = obj.parent
        track.reverse()
        return track


class Docstring(ABC):
    """
    Stores the docstring of a function / class / method, then divides
    it into different sections accaording to its titles.

    Parameters
    ----------
    text : str
        Docstring text.
    parent : PyText, optional
        Parent node (if exists), by default None.

    """

    def __init__(self, text: str, parent: Optional[PyText] = None) -> None:
        self.text = text.strip()
        self.parent = parent

    @property
    @abstractmethod
    def sections(self) -> Dict[str, str]:
        """
        Returns the details of the docstring, each title corresponds to a
        paragraph of description.

        Returns
        -------
        Dict[str, str]
            Dict of titles and descriptions.

        """
        return {}


class FindTextResult:
    """Result of text finding, only as a return of `PyText.findall()`."""

    def __init__(self, pattern: Union[str, "Pattern[str]"], line_numbers: bool) -> None:
        self.pattern = pattern
        self.line_numbers = line_numbers
        self.res: List[Tuple[PyText, int, str]] = []

    def __repr__(self) -> str:
        string: str = ""
        for tp, nline, group in self.res:
            string += f"\n{tp.relpath}" + f":{nline}" * self.line_numbers + ": "
            _sub = re.sub(
                self.pattern,
                lambda x: "\033[100m" + x.group() + "\033[0m",
                " " * tp.spaces + group,
            )
            string += re.sub("\\\\x1b\\[", "\033[", _sub.__repr__())
        return string.lstrip()

    def append(self, finding: Tuple[PyText, int, str]) -> None:
        """
        Append a new finding.

        Parameters
        ----------
        finding : Tuple[PyText, int, str]
            Contains a `PyText` instance, the line number where pattern
            is found, and a matched string.

        """
        self.res.append(finding)

    def extend(self, findings: List[Tuple[PyText, int, str]]) -> None:
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
        Joins the other instance of self.__class__, only works when it
        has the same `pattern` as self.

        Parameters
        ----------
        other : Self
            The other instance.

        Raises
        ------
        ValueError
            Raised when the two instances have different patterns.

        """
        if other.pattern != self.pattern:
            raise ValueError("joined instances must have the same pattern")
        self.extend(other.res)

    def to_styler(self, match: Optional[Callable] = None) -> "Styler":
        """
        Return a `Styler` of dataframe to beautify the representation in a
        Jupyter notebook.

        Parameters
        ----------
        match : Callable, optional
            Specifies how to display the matched pattern, by default None.

        Returns
        -------
        Styler
            A `Styler` of dataframe.

        Raises
        ------
        ValueError
            Raised when `mode` is unrecognized.

        """
        df = pd.DataFrame("", index=range(len(self.res)), columns=["source", "match"])
        for i, r in enumerate(self.res):
            _tp, _n, _line = r
            df.iloc[i, 0] = ".".join(
                [self.__display_source(x) for x in _tp.track()]
            ).replace(".NULL", "")
            if self.line_numbers:
                df.iloc[i, 0] += ":" + make_ahref(
                    f"{_tp.execpath}:{_n}", str(_n), color="inherit"
                )
            f = partial(self.__display_match if match is None else match, r)
            df.iloc[i, 1] = re.sub(self.pattern, f, _line)
        return (
            df.style.hide(axis=0)
            .set_properties(**{"text-align": "left"})
            .set_table_styles([{"selector": "th", "props": [("text-align", "center")]}])
        )

    @staticmethod
    def __display_source(x: PyText) -> str:
        return (
            NULL
            if x.name == NULL
            else make_ahref(
                f"{x.execpath}:{x.start_line}:{1+x.spaces}", x.name, color="inherit"
            )
        )

    @staticmethod
    def __display_match(r: Tuple[PyText, int, str], m: "Match[str]") -> str:
        return (
            ""
            if m.group() == ""
            else make_ahref(
                f"{r[0].execpath}:{r[1]}:{1+r[0].spaces+m.span()[0]}",
                m.group(),
                color="#cccccc",
                background_color="#505050",
            )
        )


def make_ahref(
    url: str,
    text: str,
    color: Optional[str] = None,
    background_color: Optional[str] = None,
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
    background_color : str, optional
        Background color, by default None.

    Returns
    -------
    str
        An HTML <a> tag.

    """
    style: str = "text-decoration:none"
    if color is not None:
        style += f";color:{color}"
    if background_color is not None:
        style += f";background-color:{background_color}"
    if Path(url).stem == NULL:
        href = ""
    else:
        href = f"href='{url}' "
    return f"<a {href}style='{style}'>{text}</a>"


def make_span(
    text: str,
    color: Optional[str] = None,
    background_color: Optional[str] = None,
) -> str:
    """
    Makes an HTML <span> tag..

    Parameters
    ----------
    text : str
    color : str, optional
        Text color, by default None.
    background_color : str, optional
        Background color, by default None.

    Returns
    -------
    str
        An HTML <span> tag.

    """
    style: str = ""
    if color is not None:
        style += f";color:{color}"
    if background_color is not None:
        style += f";background-color:{background_color}"
    if style.startswith(";"):
        style = style[1:]
    return f"<span style='{style}'>{text}</span>"


@overload
def as_path(path_or_text: Path, home: Union[Path, str, None] = None) -> Path: ...
@overload
def as_path(
    path_or_text: str, home: Union[Path, str, None] = None
) -> Union[Path, str]: ...
def as_path(
    path_or_text: Union[Path, str], home: Union[Path, str, None] = None
) -> Union[Path, str]:
    """
    If the input is a string, check if it represents an existing
    path. If it does, convert it to a `Path` object, otherwise return
    itself. If the input is already a `Path` object, return itself
    directly.

    Parameters
    ----------
    path_or_text : Union[Path, str]
        An instance of `Path` or a string.
    home : Union[Path, str, None], optional
        Specifies the home path if `path_or_text` is relative, by
        default None.

    Returns
    -------
    Union[Path, str]
        A path or a string.

    """
    home = Path("").cwd() if home is None else Path(home).absolute()
    if isinstance(path_or_text, str):
        if len(path_or_text) < 256 and (home / path_or_text).exists():
            path_or_text = Path(path_or_text)
        else:
            return path_or_text

    if not path_or_text.is_absolute():
        path_or_text = home / path_or_text
    return path_or_text


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
        Raised when input is not a python file.

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
        self.new_text = ""
        self.__repl: Union[str, Callable[["Match[str]"], str]] = ""
        self.__count: int = 0

    def write(self, text: str) -> None:
        """
        Write text.

        Parameters
        ----------
        text : str
            Text to write.

        """
        self.path.write_text(text + "\n", encoding=self.pyfile.encoding)

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

    def __init__(self, pattern: Union[str, "Pattern[str]"], line_numbers: bool):
        self.pattern = pattern
        self.line_numbers = line_numbers
        self.editors: List[PyEditor] = []

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
        Joins the other instance of self.__class__, only works when it
        has the same `pattern` as self.

        Parameters
        ----------
        other : Self
            The other instance.

        Raises
        ------
        ValueError
            Raised when the two instances have different patterns.

        """
        if other.pattern != self.pattern:
            raise ValueError("joined instances must have the same pattern")
        self.editors.extend(other.editors)

    def confirm(self) -> None:
        """
        Confirm the replacement.

        NOTE: This may overwrite existing files, so be VERY CAREFUL!

        """
        for e in self.editors:
            e.write(e.new_text)

    def to_styler(self) -> "Styler":
        """
        Return a `Styler` of dataframe to beautify the representation in a
        Jupyter notebook.

        Returns
        -------
        Styler
            A `Styler` of dataframe.

        """
        styler = self.__find_text_result.to_styler(match=self.__display_repl)
        setattr(styler, "confirm", self.confirm)
        return styler

    def __display_repl(self, r: Tuple[PyText, int, str], m: "Match[str]") -> str:
        url = f"{r[0].execpath}:{r[1]}:{1+r[0].spaces+m.span()[0]}"
        disp = (
            ""
            if m.group() == ""
            else make_ahref(url, m.group(), color="#cccccc", background_color="#4d2f2f")
        )
        if (new := self.editors[0].counted_repl(m)) == "":
            return disp
        return disp + make_ahref(url, new, color="#cccccc", background_color="#2f4d2f")

    @cached_property
    def __find_text_result(self) -> FindTextResult:
        res = FindTextResult(self.pattern, self.line_numbers)
        for e in self.editors:
            res.join(e.pyfile.findall(self.pattern, styler=False))
        return res


# pylint: disable=unused-argument
def _ignore(
    whole_word: bool = False,
    case_sensitive: bool = True,
    regex: bool = True,
    styler: bool = True,
    line_numbers: bool = True,
) -> None: ...
