"""
Contains abstract classes: PyText and Docstring.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""
import re
from abc import ABC, abstractmethod
from functools import cached_property, partial
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Tuple, Union, overload

import pandas as pd
from typing_extensions import Self

from .utils.re_extensions import pattern_inreg, real_findall

if TYPE_CHECKING:
    from pandas.io.formats.style import Styler


__all__ = ["PyText", "Docstring"]

NULL = "NULL"  # Path stems or filenames should avoid this.


class PyText(ABC):
    """
    Could be a python module, file, class, function, or method.

    Parameters
    ----------
    path_or_text : Union[Path, str]
        File path, module path or file text.
    parent : Optional[&quot;PyText&quot;], optional
        Parent node (if exists), by default None.
    start_line : int, optional
        Starting line number, by default 1.
    home : Union[Path, str, None], optional
        Specifies the home path if `path_or_text` is relative, by default None.
    encoding : Optional[str], optional
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

        self.parent: Optional["PyText"] = parent
        self.start_line: int = start_line
        self.home: Path = as_path(Path(""), home=home)
        self.encoding: Optional[str] = encoding
        self.spaces: int = 0

        self._header: Optional[str] = None
        self.text_init(path_or_text)

    def __repr__(self) -> None:
        return f"{self.__class__.__name__}('{self.absname}')"

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
        TextPy
            An instance of `TextPy`.

        """

    @cached_property
    def children(self) -> List["PyText"]:
        """
        Children nodes.

        Returns
        -------
        Dict[str, TextPy]
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
        Dict[str, TextPy]
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
        pattern: Union[str, re.Pattern],
        whole_word: bool = False,
        case_sensitive: bool = True,
        regex: bool = True,
        styler: Literal[True] = True,
        line_numbers: bool = True,
    ) -> "Styler":
        ...

    @overload
    def findall(
        self,
        pattern: Union[str, re.Pattern],
        whole_word: bool = False,
        case_sensitive: bool = True,
        regex: bool = True,
        styler: Literal[False] = False,
        line_numbers: bool = True,
    ) -> "FindTextResult":
        ...

    def findall(
        self,
        pattern: Union[str, re.Pattern],
        whole_word: bool = False,
        case_sensitive: bool = True,
        regex: bool = True,
        styler: bool = True,
        line_numbers: bool = True,
    ) -> Union["Styler", "FindTextResult"]:
        """
        Finds all non-overlapping matches of `pattern`.

        Parameters
        ----------
        pattern : Union[str, re.Pattern]
            Regex pattern.
        whole_word : bool, optional
            Whether to match whole words only, by default False.
        case_sensitive : bool, optional
            Specifies case sensitivity, by default True.
        regex : bool, optional
            Whether to enable regular expressions, by default True.
        styler : bool, optional
            Whether to return a `Styler` object in convenience of displaying
            in a Jupyter notebook, this only takes effect when
            `pandas.__version__ >= 1.4.0`, by default True.
        line_numbers : bool, optional
            Whether to display the line numbers, by default True.

        Returns
        -------
        Union[Styler, FindTextResult]
            Searching result.

        """
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

        res = FindTextResult(pattern, line_numbers=line_numbers)
        if not self.children:
            to_match = self.text
            for nline, _, group in real_findall(
                ".*" + pattern.pattern + ".*",
                to_match,
                linemode=True,
                flags=pattern.flags,
            ):
                if group != "":
                    res.append((self, self.start_line + nline - 1, group))
        else:
            res = res.join(self.header.findall(pattern, styler=False))
            for c in self.children:
                res = res.join(c.findall(pattern, styler=False))
        return res.to_styler() if styler and pd.__version__ >= "1.4.0" else res

    def jumpto(self, target: str) -> "PyText":
        """
        Jump to another `TextPy` instance.

        Parameters
        ----------
        target : str
            Relative name of the target instance.

        Returns
        -------
        TextPy
            An instance of `TextPy`.

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

    def as_header(self) -> Self:
        """
        Declare `self` as a class header (rather than the class itself).

        Returns
        -------
        self
            An instance of self.

        """
        self.name = NULL
        return self

    def track(self) -> List["PyText"]:
        """
        Returns a list of all the parents and `self`.

        Returns
        -------
        List[TextPy]
            List of `TextPy` instances.

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
    parent : Optional[PyText], optional
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
    """
    Result of text finding, only as a return of `TextPy.findall`.

    Parameters
    ----------
    pattern : Union[str, re.Pattern]
        Regex pattern.
    line_numbers : bool, optional
        Whether to display the line numbers, by default True.

    """

    def __init__(
        self, pattern: Union[str, re.Pattern], line_numbers: bool = True
    ) -> None:
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
        finding : Tuple[TextPy, int, str]
            Contains a `TextPy` instance, the line number where pattern
            is found, and a matched string.

        """
        self.res.append(finding)

    def extend(self, findings: List[Tuple[PyText, int, str]]) -> None:
        """
        Extend a few new findings.

        Parameters
        ----------
        findings : List[Tuple[TextPy, int, str]]
            A finding contains a `TextPy` instance, the line number where
            pattern is found, and a matched string.

        """
        self.res.extend(findings)

    def join(self, other: "FindTextResult") -> "FindTextResult":
        """
        Joins two `FindTextResult` instance, only works when they share the
        same `pattern`.

        Parameters
        ----------
        other : FindTextResult
            The other instance.

        Returns
        -------
        FindTextResult
            A new instance.

        Raises
        ------
        ValueError
            Raised when the two instances have different patterns.

        """
        if other.pattern != self.pattern:
            raise ValueError("joined instances must have the same pattern")
        obj = self.__class__(self.pattern, line_numbers=self.line_numbers)
        obj.extend(self.res + other.res)
        return obj

    def to_styler(self) -> "Styler":
        """
        Convert `self` to a `Styler` of dataframe in convenience of displaying
        in a Jupyter notebook.

        Returns
        -------
        Styler
            A `Styler` of dataframe.

        """
        df = pd.DataFrame("", index=range(len(self.res)), columns=["source", "match"])
        for i, r in enumerate(self.res):
            _tp, _n, _match = r
            df.iloc[i, 0] = ".".join(
                [self.__display_source(x) for x in _tp.track()]
            ).replace(".NULL", "")
            if self.line_numbers:
                df.iloc[i, 0] += ":" + make_ahref(
                    f"{_tp.execpath}:{_n}", str(_n), color="inherit"
                )
            df.iloc[i, 1] = re.sub(
                self.pattern, partial(self.__display_match, r), _match
            )
        return (
            df.style.hide(axis=0)
            .set_properties(**{"text-align": "left"})
            .set_table_styles([dict(selector="th", props=[("text-align", "center")])])
        )

    def __display_source(self, x: PyText) -> str:
        return (
            NULL
            if x.name == NULL
            else make_ahref(
                f"{x.execpath}:{x.start_line}:{1+x.spaces}", x.name, color="inherit"
            )
        )

    def __display_match(self, r: Tuple[PyText, int, str], m: re.Match) -> str:
        return (
            ""
            if m.group() == ""
            else make_ahref(
                f"{r[0].execpath}:{r[1]}:{1+r[0].spaces+m.span()[0]}",
                m.group(),
                color="#cccccc",
                background_color="#595959",
            )
        )


def make_ahref(
    url: str,
    display: str,
    color: Optional[str] = None,
    background_color: Optional[str] = None,
) -> str:
    """
    Makes an HTML <a> tag.

    Parameters
    ----------
    url : str
        URL to link.
    display : str
        Word to display.
    color : Optional[str], optional
        Text color, by default None.
    background_color : Optional[str], optional
        Background color, by default None.

    Returns
    -------
    str
        An HTML <a> tag.

    """
    style_list = ["text-decoration:none"]
    if color is not None:
        style_list.append(f"color:{color}")
    if background_color is not None:
        style_list.append(f"background-color:{background_color}")
    style = ";".join(style_list)
    if Path(url).stem == NULL:
        href = ""
    else:
        href = f"href='{url}' "
    return f"<a {href}style='{style}'>{display}</a>"


@overload
def as_path(path_or_text: Path, home: Union[Path, str, None] = None) -> Path:
    ...


@overload
def as_path(path_or_text: str, home: Union[Path, str, None] = None) -> Union[Path, str]:
    ...


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
