import re
from functools import cached_property
from pathlib import Path
from typing import *

from .abc import NULL, Docstring, PyText
from .format import NumpyFormatDocstring
from .utils.re_extended import line_count_iter, rsplit

__all__ = ["PyModule", "PyFile", "PyClass", "PyFunc", "PyMethod"]


class PyModule(PyText):
    def __init__(
        self,
        path: Union[Path, str],
        parent: Optional[PyText] = None,
        home: Union[Path, str, None] = None,
    ):
        """
        A python module including multiple python files.

        Parameters
        ----------
        path : Union[Path, str]
            File path.
        parent : Optional[TextPy], optional
            Parent node (if exists), by default None.
        home : Union[Path, str, None], optional
            Specifies the home path if `path` is relative, by default None.

        Raises
        ------
        NotADirectoryError
            Raised when `path` is not a directory.

        """
        self.path = as_path(path, home=home)
        if not self.path.is_dir():
            raise NotADirectoryError(f"not a dicretory: '{self.path}'")
        self.name = self.path.stem
        self.parent = parent
        self.home = as_path(Path(""), home=home)

    @cached_property
    def header(self) -> PyText:
        return PyFile("", parent=self)

    @cached_property
    def children(self) -> List[PyText]:
        children: List[PyText] = []
        for _path in self.path.iterdir():
            if _path.suffix == ".py":
                children.append(PyFile(_path, parent=self, home=self.home))
            elif _path.is_dir():
                _module = PyModule(_path, parent=self, home=self.home)
                if len(_module.children) > 0:
                    children.append(_module)
        return children


class PyFile(PyText):
    def __init__(
        self,
        path_or_text: Union[Path, str],
        parent: Optional[PyText] = None,
        start_line: int = 1,
        home: Union[Path, str, None] = None,
    ):
        """
        Python file.

        Parameters
        ----------
        path_or_text : Union[Path, str]
            File path or file text.
        parent : Optional[TextPy], optional
            Parent node (if exists), by default None.
        home : Union[Path, str, None], optional
            Specifies the home path if `path_or_text` is relative, by
            default None.

        """
        self.home = as_path(Path(""), home=home)

        if isinstance(path_or_text, Path):
            if not path_or_text.is_absolute():
                self.path = self.home / path_or_text
            else:
                self.path = path_or_text
            self.text = self.path.read_text().strip()
        else:
            self.text = path_or_text.strip()

        self.name = self.path.stem
        self.parent = parent
        self.start_line = start_line
        self.__header: Optional[str] = None

    @cached_property
    def header(self) -> PyText:
        if self.__header is None:
            _ = self.children
        return self.__class__(self.__header, parent=self).as_header()

    @cached_property
    def children(self) -> List[PyText]:
        children: List[PyText] = []
        _cnt: int = 0
        self.__header = ""
        for i, _str in line_count_iter(rsplit("\n\n\n+[^\s]", self.text)):
            _str = "\n" + _str.strip()
            if re.match("(?:\n@.*)*\ndef ", _str):
                children.append(
                    PyFunc(_str, parent=self, start_line=int(i + 3 * (_cnt > 0)))
                )
            elif re.match("(?:\n@.*)*\nclass ", _str):
                children.append(
                    PyClass(_str, parent=self, start_line=int(i + 3 * (_cnt > 0)))
                )
            elif _cnt == 0:
                self.__header = _str
            else:
                children.append(
                    PyFile(_str, parent=self, start_line=int(i + 3 * (_cnt > 0)))
                )
            _cnt += 1
        return children


class PyClass(PyText):
    def __init__(
        self, text: str, parent: Optional[PyText] = None, start_line: int = 1
    ) -> None:
        """
        Python class.

        Parameters
        ----------
        text : str
            Class text.
        parent : Optional[TextPy], optional
            Parent node (if exists), by default None.
        start_line : int, optional
            Starting line number, by default 1.

        """
        self.text = text.strip()
        self.name = re.search("class .*?[(:]", self.text).group()[6:-1]
        self.parent = parent
        self.start_line = start_line
        self.__header: Optional[str] = None

    @cached_property
    def doc(self) -> Docstring:
        _init = self.jumpto("__init__")
        if "__init__" in self.children_names and _init.doc.text != "":
            _doc = _init.doc.text
        else:
            _doc = self.header.text
        return NumpyFormatDocstring(_doc, parent=self)

    @cached_property
    def header(self) -> PyText:
        if self.__header is None:
            _ = self.children
        return self.__class__(
            self.__header, parent=self, start_line=self.start_line
        ).as_header()

    @cached_property
    def children(self) -> List[PyText]:
        children: List[PyText] = []
        sub_text = re.sub("\n    ", "\n", self.text)
        _cnt: int = 0
        for i, _str in line_count_iter(rsplit("(?:\n@.*)*\ndef ", sub_text)):
            if _cnt == 0:
                self.__header = _str.replace("\n", "\n    ")
            else:
                children.append(
                    PyMethod(_str, parent=self, start_line=self.start_line + i)
                )
            _cnt += 1
        return children


class PyFunc(PyText):
    def __init__(
        self, text: str, parent: Optional[PyText] = None, start_line: int = 1
    ) -> None:
        """
        Python function.

        Parameters
        ----------
        text : str
            Funtion text.
        parent : Optional[TextPy], optional
            Parent node (if exists), by default None.
        start_line : int, optional
            Starting line number, by default 1.

        """
        self.text = text.strip()
        self.name = re.search("def .*?\(", self.text).group()[4:-1]
        self.parent = parent
        self.start_line = start_line

    @cached_property
    def doc(self) -> Docstring:
        searched = re.search('""".*?"""', self.text, re.DOTALL)
        if searched:
            _doc = re.sub("\n    ", "\n", searched.group()[3:-3])
        else:
            _doc = ""
        return NumpyFormatDocstring(_doc, parent=self)

    @cached_property
    def header(self) -> PyText:
        return re.search(".*\n[^\s][^\n]*", self.text, re.DOTALL).group()


class PyMethod(PyFunc):
    def __init__(
        self, text: str, parent: Optional[PyText] = None, start_line: int = 1
    ) -> None:
        """
        Python class method.

        Parameters
        ----------
        text : str
            Method text.
        parent : Optional[TextPy], optional
            Parent node (if exists), by default None.
        start_line : int, optional
            Starting line number, by default 1.

        """
        super().__init__(text, parent=parent, start_line=start_line)
        self.spaces = 4


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
    path, if true, convert it to a `Path` object, otherwise return
    itself. If the input is already a `Path` object, return itself,
    too.

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
    if home is None:
        home = Path("").cwd()
    else:
        home = Path(home).absolute()

    if isinstance(path_or_text, str):
        if len(path_or_text) < 256 and (home / path_or_text).exists():
            path_or_text = Path(path_or_text)
        else:
            return path_or_text

    if not path_or_text.is_absolute():
        path_or_text = home / path_or_text
    return path_or_text
