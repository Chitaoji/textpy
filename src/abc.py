"""
Contains abstract classes: PyText and Docstring.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import logging
import re
from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Union,
    overload,
)

import black
from typing_extensions import ParamSpec, Self

from .imports import Imports
from .interaction import (
    NULL,
    FileEditor,
    FindTextResult,
    Replacer,
    TextFinding,
    display_params,
    make_html_tree,
)
from .utils.re_extensions import SmartPattern, line_findall, pattern_inreg

if TYPE_CHECKING:
    from re import Pattern

    from ._typing import PatternType, ReplType
    from .text import PyContent


__all__ = ["PyText", "Docstring"]


P = ParamSpec("P")


class PyText(ABC, Generic[P]):
    """
    Could be a python module, file, function, class, method or property.

    Parameters
    ----------
    path_or_text : Union[Path, str]
        File path, module path or file text.
    parent : PyText, optional
        Parent node (if exists), by default None.
    start_line : int, optional
        Starting line number, by default None.
    home : Union[Path, str, None], optional
        Specifies the home path; only takes effect when `path_or_text` is
        relative; by default None.
    encoding : str, optional
        Specifies encoding, by default None.

    """

    def __init__(
        self,
        path_or_text: Union[Path, str],
        *,
        parent: Optional["PyText"] = None,
        start_line: Optional[int] = None,
        home: Union[Path, str, None] = None,
        encoding: Optional[str] = None,
        ignore: Set[str] = ...,
        mask: Optional[Self] = None,
    ) -> None:
        self.text: str = ""
        self.name: str = ""
        self.path = Path(NULL + ".py")

        self.parent = parent
        self.spaces = 0

        if start_line is None:
            self.start_line = 1 if parent is None else parent.start_line
        else:
            self.start_line = start_line

        if parent is None:
            self.home = as_path(Path(""), home=home)
            self.encoding = encoding
            self.ignore = ignore
        else:
            self.home = parent.home
            self.encoding = parent.encoding
            self.ignore = parent.ignore

        self._header: Optional[Any] = None
        self.__pytext_post_init__(path_or_text)

        if mask:
            self.path = mask.path
            self.name = mask.name
            self.parent = mask.parent
            self.home = mask.home

    def __repr__(self) -> None:
        return f"{self.__class__.__name__}({self.absname!r})"

    def _repr_mimebundle_(self, *_, **__) -> Optional[Dict[str, Any]]:
        if display_params.use_mimebundle:
            return {"text/html": self.to_html()}

    def __truediv__(self, __value: "str") -> "PyText":
        return self.jumpto(__value)

    @abstractmethod
    def __pytext_post_init__(self, path_or_text: Union[Path, str]) -> None:
        """
        Post init.

        Parameters
        ----------
        path_or_text : Union[Path, str]
            File path, module path or file text.

        """

    def __eq__(self, __other: Self) -> bool:
        return self.abspath == __other.abspath

    def __gt__(self, __other: Self) -> bool:
        return self.abspath > __other.abspath

    def __ge__(self, __other: Self) -> bool:
        return self.abspath >= __other.abspath

    def to_html(self) -> str:
        """Return an html string for representation."""
        return make_html_tree(self)

    @cached_property
    @abstractmethod
    def doc(self) -> "Docstring":
        """
        Docstring of a module / class / function / method.

        Returns
        -------
        Docstring
            An instance of `Docstring`.

        """

    @cached_property
    @abstractmethod
    def header(self) -> "PyContent":
        """
        Header of a module / function / class / method.

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
        List[PyText]
            List of the children nodes.

        """
        return []

    @cached_property
    def children_names(self) -> List[str]:
        """
        Children names.

        NOTE: This takes up additional memory space.

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

        NOTE: This takes up additional memory space.

        Returns
        -------
        Dict[str, PyText]
            Dictionary of children nodes.

        """
        children_dict: Dict[str, "PyText"] = {}
        null_cnt: int = 0
        for child, childname in zip(self.children, self.children_names):
            if childname == NULL:
                childname = f"NULL_{null_cnt}"
                null_cnt += 1
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
        return "." + self.absname.partition(".")[-1]

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
        Find the relative path to the working environment. If is directory,
        try to find a '__init__.py' first.

        Returns
        -------
        Path
            The relative path to the working environment.

        """
        if self.is_dir():
            return self.header.execpath
        try:
            return self.abspath.relative_to(self.abspath.cwd())
        except ValueError:
            return self.abspath

    def is_file(self) -> bool:
        """Returns whether self is an instance of `PyFile`."""
        return self.__class__.__name__ == "PyFile"

    def is_dir(self) -> bool:
        """Returns whether self is an instance of `PyDir`."""
        return self.__class__.__name__ == "PyDir"

    def check_format(self) -> None:
        """
        Checks the format of files. Logs warning if a file does not comply
        with Black formatter's default rules.

        """
        if self.is_dir():
            for c in self.children:
                c.check_format()
        elif self.is_file() and black_format(self.text).strip() != self.text:
            logging.warning(
                "file does not comply with Black formatter's default rules: '%s'",
                self.path,
            )

    @overload
    def findall(
        self, pattern: "PatternType", /, *_: P.args, **kwargs: P.kwargs
    ) -> FindTextResult: ...
    def findall(
        self, pattern, /, based_on: Replacer = None, **kwargs
    ) -> FindTextResult:
        """
        Finds all non-overlapping matches of `pattern`.

        Parameters
        ----------
        pattern : Union[str, Pattern[str], SmartPattern[str]]
            String pattern.
        whole_word : bool, optional
            Whether to match whole words only, by default False.
        dotall : bool, optional
            Whether the "." matches any character at all, including a newline,
            by default False.
        case_sensitive : bool, optional
            Specifies case sensitivity, by default True.
        regex : bool, optional
            Whether to enable regular expressions, by default True.

        Returns
        -------
        FindTextResult
            Searching result.

        """
        pattern = self.__pattern_trans(pattern, **kwargs)
        res = FindTextResult()
        if based_on and self.is_file():
            latest = self
            for e in based_on.editors:
                if e.pyfile == self and not e.is_based_on:
                    latest = self.__class__(e.new_text, mask=self)
                    break
            res.join(latest.findall(pattern))
        elif not self.children:
            for nline, g in line_findall(self.__pattern_expand(pattern), self.text):
                if g:
                    res.append(
                        TextFinding(self, pattern, self.start_line + nline - 1, g)
                    )
        else:
            res.join(self.header.findall(pattern, based_on=based_on))
            for c in self.children:
                res.join(c.findall(pattern, based_on=based_on))
        return res

    @overload
    def replace(
        self,
        pattern: "PatternType",
        repl: "ReplType",
        overwrite: bool = True,
        /,
        *_: P.args,
        **kwargs: P.kwargs,
    ) -> "Replacer": ...
    def replace(
        self,
        pattern,
        repl,
        /,
        overwrite=True,
        based_on: Optional[Replacer] = None,
        **kwargs,
    ) -> "Replacer":
        """
        Finds all non-overlapping matches of `pattern`, and replace them with
        `repl`. If you want the replacement to take effect on files, use
        `.confirm()` immediately after this method (e.g.
        `.replace("a", "b").confirm()`).

        Parameters
        ----------
        pattern : Union[str, Pattern[str], SmartPattern[str]]
            String pattern.
        repl : ReplType
            Speficies the string to replace the patterns. If Callable, should
            be a function that receives the Match object, and gives back
            the replacement string to be used.
        overwrite : bool, optional
            Determines whether to overwrite the original files. If False, the
            replacement will take effect on copyed files, by default True.
        whole_word : bool, optional
            Whether to match whole words only, by default False.
        dotall : bool, optional
            Whether the "." matches any character at all, including a newline,
            by default False.
        case_sensitive : bool, optional
            Specifies case sensitivity, by default True.
        regex : bool, optional
            Whether to enable regular expressions, by default True.

        Returns
        -------
        Replacer
            Text replacer.

        """
        pattern = self.__pattern_trans(pattern, **kwargs)
        replacer = Replacer()
        if self.path.suffix == ".py":
            old = None
            if based_on:
                for e in based_on.editors:
                    if e.pyfile == self and not e.is_based_on:
                        old = e
                        break
            editor = FileEditor(self, overwrite=overwrite, based_on=old)
            if editor.replace(pattern, repl) > 0:
                replacer.append(editor)
        else:
            for c in self.children:
                replacer.join(
                    c.replace(
                        pattern,
                        repl,
                        overwrite=overwrite,
                        based_on=based_on,
                        **kwargs,
                    )
                )
        return replacer

    @overload
    def delete(
        self,
        pattern: "PatternType",
        overwrite: bool = True,
        /,
        *_: P.args,
        **kwargs: P.kwargs,
    ) -> "Replacer": ...
    def delete(self, pattern, /, overwrite=True, based_on=None, **kwargs) -> "Replacer":
        """
        An alternative to `.replace(pattern, "", *args, **kwargs)`

        Parameters
        ----------
        pattern : Union[str, Pattern[str], SmartPattern[str]]
            String pattern.
        overwrite : bool, optional
            Determines whether to overwrite the original files. If False, the
            replacement will take effect on copyed files, by default True.
        whole_word : bool, optional
            Whether to match whole words only, by default False.
        dotall : bool, optional
            Whether the "." matches any character at all, including a newline,
            by default False.
        case_sensitive : bool, optional
            Specifies case sensitivity, by default True.
        regex : bool, optional
            Whether to enable regular expressions, by default True.

        Returns
        -------
        Replacer
            Text replacer.

        """
        return self.replace(pattern, "", overwrite, based_on=based_on, **kwargs)

    @cached_property
    def imports(self) -> Imports:
        """Import infomation of the module."""
        return Imports(self)

    @staticmethod
    def __pattern_trans(
        pattern: "PatternType",
        whole_word: bool = False,
        dotall: bool = False,
        case_sensitive: bool = True,
        regex: bool = True,
    ) -> Union["Pattern[str]", SmartPattern[str]]:
        if isinstance(pattern, re.Pattern):
            p, f = pattern.pattern, pattern.flags
        elif isinstance(pattern, SmartPattern):
            p, f = pattern.pattern, pattern.flags
        elif isinstance(pattern, str):
            p, f = pattern, 0
        else:
            raise TypeError(
                f"'pattern' can not be instance of {p.__class__.__name__!r}"
            )
        if not regex:
            p = pattern_inreg(p)
        if not case_sensitive:
            f = f | re.I
        if whole_word:
            p = "\\b" + p + "\\b"
        if dotall:
            f = f | re.DOTALL
        if isinstance(pattern, SmartPattern):
            return SmartPattern(
                p, flags=f, ignore=pattern.ignore, mark_ignore=pattern.mark_ignore
            )
        return re.compile(p, flags=f)

    @staticmethod
    def __pattern_expand(
        pattern: Union["Pattern[str]", SmartPattern[str]]
    ) -> Union["Pattern[str]", SmartPattern[str]]:
        if pattern.flags & re.DOTALL:
            new_pattern = "[^\n]*" + pattern.pattern + "[^\n]*"
        else:
            new_pattern = ".*" + pattern.pattern + ".*"
        if isinstance(pattern, re.Pattern):
            return re.compile(new_pattern, flags=pattern.flags)
        return SmartPattern(
            new_pattern,
            flags=pattern.flags,
            ignore=pattern.ignore,
            mark_ignore=pattern.mark_ignore,
        )

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
        if not target:
            return self
        if target == NULL:
            raise ValueError("can not jump to NULL")
        if target.startswith(("/", "\\")):
            raise ValueError(f"can not jump to absolute path: {target!r}")
        splits = re.sub("[/\\\\]+", ".", target).split(".", maxsplit=1)
        a, b = (splits[0], "") if len(splits) == 1 else splits
        if not a:
            if self.parent is not None:
                return self.parent.jumpto(b)
            raise ValueError(f"{self.absname!r} hasn't got a parent")
        to_find = {a[:-2], a} if a.endswith("()") else {a, a + "()"}
        for i in range(len(self.children) - 1, -1, -1):
            if self.children[i].name in to_find:
                return self.children[i].jumpto(b)
        if self.name in to_find:
            return self.jumpto(b)
        if a == "py" and self.is_file():
            return self.jumpto(b)
        raise ValueError(f"{a!r} is not a child of {self.absname!r}")

    def track(self) -> List["PyText"]:
        """
        Returns a list of all the parents and `self`.

        Returns
        -------
        List[PyText]
            List of `PyText` instances.

        """
        tracks: List["PyText"] = []
        obj: Optional["PyText"] = self
        while obj is not None:
            tracks.append(obj)
            obj = obj.parent
        tracks.reverse()
        return tracks


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

    def __repr__(self) -> str:
        return self.text

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


def black_format(string: str) -> str:
    """Reformat a string using Black and return new contents."""
    return black.format_str(string, mode=black.FileMode())


# pylint: disable=unused-argument
def _defaults(
    whole_word: bool = False,
    dotall: bool = False,
    case_sensitive: bool = True,
    regex: bool = True,
    based_on: Optional[Replacer] = None,
) -> None: ...
