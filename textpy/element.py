import re
from functools import cached_property
from pathlib import Path
from typing import *

from .abc import NULL, Docstring, PyText, as_path
from .format import NumpyFormatDocstring
from .utils.re_extended import line_count_iter, rsplit

__all__ = ["PyModule", "PyFile", "PyClass", "PyFunc", "PyMethod"]


class PyModule(PyText):
    def init_attrs(self, path_or_text: Union[Path, str]) -> None:
        """
        Initialize the instance.

        Parameters
        ----------
        path_or_text : Union[Path, str]
            File path, module path or file text.

        Raises
        ------
        NotADirectoryError
            Raised when `path` is not a directory.

        """
        self.path = as_path(path_or_text, home=self.home)
        if not self.path.is_dir():
            raise NotADirectoryError(f"not a dicretory: '{self.path}'")
        self.name = self.path.stem

    @cached_property
    def header(self) -> PyText:
        return PyFile("", parent=self)

    @cached_property
    def children(self) -> List[PyText]:
        children: List[PyText] = []
        for _path in self.path.iterdir():
            if _path.suffix == ".py":
                children.append(
                    PyFile(_path, parent=self, home=self.home, encoding=self.encoding)
                )
            elif _path.is_dir():
                _module = PyModule(
                    _path, parent=self, home=self.home, encoding=self.encoding
                )
                if len(_module.children) > 0:
                    children.append(_module)
        return children


class PyFile(PyText):
    def init_attrs(self, path_or_text: Union[Path, str]) -> None:
        if isinstance(path_or_text, Path):
            if not path_or_text.is_absolute():
                self.path = self.home / path_or_text
            else:
                self.path = path_or_text
            self.text = self.path.read_text(encoding=self.encoding).strip()
        else:
            self.text = path_or_text.strip()

        self.name = self.path.stem
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
    def init_attrs(self, path_or_text: Union[Path, str]) -> None:
        self.text = path_or_text.strip()
        self.name = re.search("class .*?[(:]", self.text).group()[6:-1]
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
    def init_attrs(self, path_or_text: Union[Path, str]) -> None:
        self.text = path_or_text.strip()
        self.name = re.search("def .*?\(", self.text).group()[4:-1]

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
    def init_attrs(self, path_or_text: Union[Path, str]) -> None:
        super().init_attrs(path_or_text=path_or_text)
        self.spaces = 4
