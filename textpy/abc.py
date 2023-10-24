import re
from abc import ABC, abstractclassmethod
from functools import cached_property
from pathlib import Path
from typing import *

import pandas as pd
from pandas.io.formats.style import Styler
from typing_extensions import *

from .utils.re_extended import pattern_inreg, real_findall

__all__ = ["PyText", "Docstring"]

NULL = "NULL"  # Path stems or filenames should avoid this.


class PyText(ABC):
    text: str = ""
    name: str = ""
    path: Path = Path(NULL + ".py")
    home: Path = Path(".")
    parent: Optional["PyText"] = None
    start_line: int = 0
    spaces: int = 0
    encoding: Optional[str] = None

    @abstractclassmethod
    def __init__(self) -> None:
        """Abstract class for python code analysis."""
        pass

    def __repr__(self) -> None:
        return f"{self.__class__.__name__}('{self.absname}')"

    @cached_property
    def doc(self) -> "Docstring":
        """
        Docstring of a function / class / method.

        Returns
        -------
        Docstring
            An instance of `Docstring`.

        """
        return Docstring("")

    @cached_property
    def header(self) -> "PyText":
        """
        Header of a file / function / class / method.

        Returns
        -------
        TextPy
            An instance of `TextPy`.

        """
        return self.__class__()

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
        The full-name including all the parent's name, connected with `"."`'s.

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
        except ValueError as e:
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
        except ValueError as e:
            return self.abspath

    @overload
    def findall(
        self,
        pattern: str,
        regex: bool = True,
        styler: Literal[True] = True,
        line_numbers: bool = True,
    ) -> Styler:
        ...

    @overload
    def findall(
        self,
        pattern: str,
        regex: bool = True,
        styler: Literal[False] = False,
        line_numbers: bool = True,
    ) -> "FindTextResult":
        ...

    def findall(
        self,
        pattern: str,
        regex: bool = True,
        styler: bool = True,
        line_numbers: bool = True,
    ) -> Union[Styler, "FindTextResult"]:
        """
        Finds all non-overlapping matches of `pattern`.

        Parameters
        ----------
        pattern : str
            Pattern string.
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

        Raises
        ------
        ValueError
            Raised when `pattern` ends with a `"\\"`.

        """
        if len(pattern) > 0 and pattern[-1] == "\\":
            raise ValueError(f"pattern should not end with a '\\': {pattern}")
        if not regex:
            pattern = pattern_inreg(pattern)
        res = FindTextResult(pattern, line_numbers=line_numbers)
        if self.children == []:
            to_match = self.text
            for nline, _, group in real_findall(
                ".*" + pattern + ".*", to_match, linemode=True
            ):
                if group != "":
                    res.append((self, self.start_line + nline - 1, group))
        else:
            res = res.join(self.header.findall(pattern, styler=False))
            for c in self.children:
                res = res.join(c.findall(pattern, styler=False))
        if styler and pd.__version__ >= "1.4.0":
            return res.to_styler()
        else:
            return res

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
        splits = re.split("\.", target, maxsplit=1)
        if len(splits) == 1:
            splits.append("")
        if splits[0] == "":
            if self.parent is not None:
                return self.parent.jumpto(splits[1])
            raise ValueError(f"`{self.absname}` hasn't got a parent")
        elif splits[0] in self.children_dict:
            return self.children_dict[splits[0]].jumpto(splits[1])
        elif self.name == splits[0]:
            return self.jumpto(splits[1])
        else:
            raise ValueError(f"`{splits[0]}` is not a child of `{self.absname}`")

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
    def __init__(self, text: str, parent: Optional[PyText] = None) -> None:
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
        self.text = text.strip()
        self.parent = parent

    @property
    @abstractclassmethod
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
    def __init__(self, pattern: str, line_numbers: bool = True) -> None:
        """
        Result of text finding, only as a return of `TextPy.find_text`.

        Parameters
        ----------
        pattern : str
            Pattern string.
        line_numbers : bool, optional
            Whether to display the line numbers, by default True.

        """
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
            string += re.sub("\\\\x1b\[", "\033[", _sub.__repr__())
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

    def to_styler(self) -> Styler:
        """
        Convert `self` to a `Styler` of dataframe in convenience of displaying
        in a Jupyter notebook.

        Returns
        -------
        Styler
            A `Styler` of dataframe.

        """
        df = pd.DataFrame("", index=range(len(self.res)), columns=["source", "match"])
        for i in range(len(self.res)):
            _tp, _n, _match = self.res[i]
            df.iloc[i, 0] = ".".join(
                [
                    NULL
                    if x.name == NULL
                    else make_ahref(
                        f"{x.execpath}"
                        + f":{x.start_line}:{1+x.spaces}" * self.line_numbers,
                        x.name,
                        color="inherit",
                    )
                    for x in _tp.track()
                ]
            ).replace(".NULL", "")
            if self.line_numbers:
                df.iloc[i, 0] += ":" + make_ahref(
                    f"{_tp.execpath}:{_n}", str(_n), color="inherit"
                )
            df.iloc[i, 1] = re.sub(
                self.pattern,
                lambda x: ""
                if x.group() == ""
                else make_ahref(
                    f"{_tp.execpath}"
                    + f":{_n}:{1+_tp.spaces+x.span()[0]}" * self.line_numbers,
                    x.group(),
                    color="#cccccc",
                    background_color="#595959",
                ),
                _match,
            )
        return (
            df.style.hide(axis=0)
            .set_properties(**{"text-align": "left"})
            .set_table_styles([dict(selector="th", props=[("text-align", "center")])])
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
