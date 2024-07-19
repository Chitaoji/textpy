"""
Contains subclasses of PyText: PyDir, PyFile, PyClass, etc.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import re
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from .abc import PyText, as_path
from .doc import NumpyFormatDocstring
from .interaction import NULL
from .utils.re_extensions import line_count_iter, rsplit

if TYPE_CHECKING:
    from .abc import Docstring

__all__ = ["PyDir", "PyFile", "PyClass", "PyFunc", "PyMethod", "PyContent"]


class PyDir(PyText):
    """Stores a directory of python files."""

    def text_init(self, path_or_text: Union[Path, str]) -> None:
        self.path = as_path(path_or_text, home=self.home)
        if not self.path.is_dir():
            raise NotADirectoryError(f"not a dicretory: '{self.path}'")
        self.name = self.path.stem

    @cached_property
    def doc(self) -> "Docstring":
        return NumpyFormatDocstring("", parent=self)

    @cached_property
    def header(self) -> PyText:
        return PyFile("", parent=self)

    @cached_property
    def children(self) -> List[PyText]:
        children: List[PyText] = []
        for _path in self.path.iterdir():
            if _path.suffix == ".py":
                children.append(PyFile(_path, parent=self))
            elif _path.is_dir():
                _module = PyDir(_path, parent=self)
                if len(_module.children) > 0:
                    children.append(_module)
        return children


class PyFile(PyText):
    """Stores the code of a python file."""

    def text_init(self, path_or_text: Union[Path, str]) -> None:
        if isinstance(path_or_text, Path):
            self.path = as_path(path_or_text, home=self.home)
            self.text = self.path.read_text(encoding=self.encoding).strip()
        else:
            self.text = path_or_text.strip()  # in this situation, once argument
            # 'path_or_text' is str, it will be regarded as text content even if can
            # represent an existing path

        self.name = self.path.stem

    @cached_property
    def doc(self) -> "Docstring":
        return NumpyFormatDocstring("", parent=self)

    @cached_property
    def header(self) -> PyText:
        if self._header is None:
            _ = self.children
        return PyContent(self._header, parent=self)

    @cached_property
    def children(self) -> List[PyText]:
        children: List[PyText] = []
        _cnt: int = 0
        self._header = ""
        for i, _str in line_count_iter(rsplit("\n\n\n+[^\\s]", self.text)):
            _str = "\n" + _str.strip()
            start_line = int(i + 3 * (_cnt > 0))
            if re.match("(?:\n@.*)*\ndef ", _str):
                children.append(PyFunc(_str, parent=self, start_line=start_line))
            elif re.match("(?:\n@.*)*\nclass ", _str):
                children.append(PyClass(_str, parent=self, start_line=start_line))
            elif _cnt == 0:
                self._header = _str
            else:
                children.append(PyFile(_str, parent=self, start_line=start_line))
            _cnt += 1
        return children


class PyClass(PyText):
    """Stores the code and docstring of a class."""

    def text_init(self, path_or_text: Union[Path, str]) -> None:
        self.text = path_or_text.strip()
        self.name = re.search("class .*?[(:]", self.text).group()[6:-1]

    @cached_property
    def doc(self) -> "Docstring":
        if "__init__" in self.children_names and (
            t := self.jumpto("__init__").doc.text
        ):
            _doc = t
        else:
            _doc = self.header.text
        return NumpyFormatDocstring(_doc, parent=self)

    @cached_property
    def header(self) -> PyText:
        if self._header is None:
            _ = self.children
        return PyContent(self._header, parent=self, start_line=self.start_line)

    @cached_property
    def children(self) -> List[PyText]:
        children: List[PyText] = []
        sub_text = re.sub("\n    ", "\n", self.text)
        _cnt: int = 0
        for i, _str in line_count_iter(rsplit("(?:\n@.*)*\ndef ", sub_text)):
            if _cnt == 0:
                self._header = _str.replace("\n", "\n    ")
            else:
                children.append(
                    PyMethod(_str, parent=self, start_line=self.start_line + i)
                )
            _cnt += 1
        return children


class PyFunc(PyText):
    """Stores the code and docstring of a function."""

    def text_init(self, path_or_text: Union[Path, str]) -> None:
        self.text = path_or_text.strip()
        self.name = re.search("def .*?\\(", self.text).group()[4:-1]

    @cached_property
    def doc(self) -> "Docstring":
        searched = re.search('""".*?"""', self.text, re.DOTALL)
        if searched:
            _doc = re.sub("\n    ", "\n", searched.group()[3:-3])
        else:
            _doc = ""
        return NumpyFormatDocstring(_doc, parent=self)

    @cached_property
    def header(self) -> PyText:
        _header = re.search(".*\n[^\\s][^\n]*", self.text, re.DOTALL).group()
        return PyContent(_header, parent=self)


class PyMethod(PyFunc):
    """Stores the code and docstring of a class method."""

    def text_init(self, path_or_text: Union[Path, str]) -> None:
        super().text_init(path_or_text=path_or_text)
        self.spaces = 4


class PyContent(PyText):
    """
    Stores a part of a file that is not storable by instances of other
    subclasses.

    """

    def text_init(self, path_or_text: Union[Path, str]) -> None:
        self.text = path_or_text.strip()
        self.name = NULL

    @cached_property
    def doc(self) -> "Docstring":
        return NumpyFormatDocstring(self.text, parent=self)

    @cached_property
    def header(self) -> PyText:
        return self
