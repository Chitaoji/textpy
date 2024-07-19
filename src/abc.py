"""
Contains abstract classes: PyText and Docstring.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import re
from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Union,
    cast,
    overload,
)

import pandas as pd
from typing_extensions import ParamSpec

from .interaction import NULL, FindTextResult, PyEditor, Replacer, display_params
from .utils.re_extensions import pattern_inreg, real_findall

if TYPE_CHECKING:
    from re import Match, Pattern


__all__ = ["PyText", "Docstring"]

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
        self.spaces = 0
        if parent is None:
            self.home = as_path(Path(""), home=home)
            self.encoding = encoding
        else:
            self.home = parent.home
            self.encoding = parent.encoding

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
        elif self.name == "NULL":
            return self.parent.absname
        return self.parent.absname + "." + self.name

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
    def findall(self, pattern, /, styler=True, **kwargs) -> "FindTextResult":
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

        Returns
        -------
        FindTextResult
            Searching result.

        """
        pattern = self.__pattern_trans(pattern, **kwargs)
        res = FindTextResult(pattern)
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
        if styler and display_params.enable_styler and pd.__version__ >= "1.4.0":
            return res.to_styler()
        return res

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
        self, pattern, repl, /, overwrite=True, styler=True, **kwargs
    ) -> "Replacer":
        """
        Finds all non-overlapping matches of `pattern`, and replace them with
        `repl`. If you want the replacement to take effect on files, use
        `.confirm()` immediately after this method (e.g.
        `.replace("a", "b").confirm()`).

        Parameters
        ----------
        pattern : Union[str, Pattern[str]]
            String pattern.
        repl : Union[str, Callable[[str], str]]
            Speficies the string to replace the patterns. If Callable, should
            be a function that receives the Match object, and gives back
            the replacement string to be used.
        overwrite : bool, optional
            Determines whether to overwrite the original files. If False, the
            replacement will take effect on copyed files, by default True.
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

        Returns
        -------
        Replacer
            Text replacer.

        """
        pattern = self.__pattern_trans(pattern, **kwargs)
        replacer = Replacer(pattern)
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
        if styler and display_params.enable_styler:
            return cast("Replacer", replacer.to_styler())
        return replacer

    @overload
    def delete(
        self,
        pattern: Union[str, "Pattern[str]"],
        overwrite: bool = True,
        /,
        *_: P.args,
        **kwargs: P.kwargs,
    ) -> "Replacer": ...
    def delete(self, pattern, /, overwrite=True, styler=True, **kwargs) -> "Replacer":
        """
        An alternative to `.replace(pattern, "", *args, **kwargs)`

        Parameters
        ----------
        pattern : Union[str, Pattern[str]]
            String pattern.
        overwrite : bool, optional
            Determines whether to overwrite the original files. If False, the
            replacement will take effect on copyed files, by default True.
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

        Returns
        -------
        Replacer
            Text replacer.

        """
        return self.replace(pattern, "", overwrite, styler=styler, **kwargs)

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


# pylint: disable=unused-argument
def _ignore(
    whole_word: bool = False,
    case_sensitive: bool = True,
    regex: bool = True,
    styler: bool = True,
) -> None: ...
