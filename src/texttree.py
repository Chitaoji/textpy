"""
Contains subclasses of TextTree: PyDir, PyFile, PyClass, etc.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import re
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from .abc import TextTree, as_path
from .doc import NumpyFormatDocstring
from .interaction import NULL
from .re_extensions import counted_strip, line_count, line_count_iter, rsplit

if TYPE_CHECKING:
    from .abc import Docstring

__all__ = [
    "PyDir",
    "PyFile",
    "PyClass",
    "PyFunc",
    "PyMethod",
    "PyProperty",
    "PyContent",
]


class PyDir(TextTree):
    """Stores a directory of python files."""

    def __texttree_post_init__(self, path_or_text: Union[Path, str]) -> None:
        self.path = as_path(path_or_text, home=self.home)
        if not self.path.is_dir():
            raise NotADirectoryError(f"not a dicretory: {self.path}")
        self.name = self.path.stem

    @cached_property
    def doc(self) -> "Docstring":
        try:
            _doc = self.jumpto("__init__").doc.text
        except ValueError:
            _doc = ""
        return NumpyFormatDocstring(_doc, parent=self)

    @cached_property
    def header(self) -> "PyContent":
        if self._header is None:
            _ = self.children
        if self._header:
            return PyContent("", parent=self, mask=self._header)
        return PyContent("", parent=self)

    @cached_property
    def children(self) -> List[TextTree]:
        children: List[TextTree] = []
        self._header = ""
        for _path in sorted(self.path.iterdir()):
            if self.ignore and any(_path.match(x) for x in self.ignore):
                continue
            if _path.suffix == ".py":
                children.append(PyFile(_path, parent=self))
                if _path.stem == "__init__":
                    self._header = children[-1]
            elif _path.is_dir():
                _module = PyDir(
                    _path, parent=self, ignore=self.ignore, include=self.include
                )
                if len(_module.children) > 0:
                    children.append(_module)
            elif self.include and any(_path.match(y) for y in self.include):
                children.append(NonPyFile(_path, parent=self))
        return children

    def is_dir(self) -> bool:
        return True


class PyFile(TextTree):
    """Stores the code of a python file."""

    def __texttree_post_init__(self, path_or_text: Union[Path, str]) -> None:
        if isinstance(path_or_text, Path):
            self.path = as_path(path_or_text, home=self.home)
            self.text, n, _ = counted_strip(self.path.read_text(encoding=self.encoding))
        else:
            self.text, n, _ = counted_strip(path_or_text)  # in this situation, once
            # argument 'path_or_text' is str, it will be regarded as text content even
            # if can represent an existing path

        self.start_line += n
        self.name = self.path.stem

    @cached_property
    def doc(self) -> "Docstring":
        if self.header.text == "":
            _doc = ""
        else:
            _doc = self.header.text[3:-3]
        return NumpyFormatDocstring(_doc, parent=self)

    @cached_property
    def header(self) -> "PyContent":
        if self._header is None:
            _ = self.children
        return PyContent(self._header, parent=self)

    @cached_property
    def children(self) -> List[TextTree]:
        children: List[TextTree] = []

        matched = re.match('""".*?"""', self.text, re.DOTALL)
        if not matched:
            matched = re.match("'''.*?'''", self.text, re.DOTALL)
        if matched:
            self._header = matched.group()
            text = self.text[matched.end() :]
        else:
            self._header = ""
            text = self.text

        header_lines = line_count(self._header)
        stored, dec, s = "", "", ""
        for n, s in line_count_iter(rsplit("\n[^\\s)\\]}]", text)):
            start_line = header_lines + n
            if re.match("\ndef ", s):
                if stored:
                    children.append(
                        PyContent(
                            stored,
                            parent=self,
                            start_line=start_line - line_count(stored + dec),
                        )
                    )
                    stored = ""
                children.append(
                    PyFunc(
                        dec + s, parent=self, start_line=start_line - line_count(dec)
                    )
                )
                dec = ""
            elif re.match("\nclass ", s):
                if stored:
                    children.append(
                        PyContent(
                            stored,
                            parent=self,
                            start_line=start_line - line_count(stored + dec),
                        )
                    )
                    stored = ""
                children.append(
                    PyClass(
                        dec + s, parent=self, start_line=start_line - line_count(dec)
                    )
                )
                dec = ""
            elif re.match("\n@", s):
                dec += s
            else:
                stored += s
        if stored:
            children.append(
                PyContent(
                    stored,
                    parent=self,
                    start_line=start_line - line_count(stored) + line_count(s) - 1,
                )
            )
        return children

    def is_file(self) -> bool:
        return True


class PyClass(TextTree):
    """Stores the code and docstring of a class."""

    def __texttree_post_init__(self, path_or_text: Union[Path, str]) -> None:
        self.text, n, _ = counted_strip(path_or_text)
        self.start_line += n
        self.name = re.search("class .*?[(:]", self.text).group()[6:-1]

    @cached_property
    def doc(self) -> "Docstring":
        searched = re.search('""".*?"""', self.header.text, re.DOTALL)
        if searched:
            _doc = re.sub("\n    ", "\n", searched.group()[3:-3])
        else:
            _doc = ""
        if not _doc:
            try:
                _doc = self.jumpto("__init__").doc.text
            except ValueError:
                ...
        return NumpyFormatDocstring(_doc, parent=self)

    @cached_property
    def header(self) -> "PyContent":
        if self._header is None:
            _ = self.children
        return PyContent(self._header, parent=self)

    @cached_property
    def children(self) -> List[TextTree]:
        children: List[TextTree] = []
        sub_text = re.sub("\n    ", "\n", self.text)
        _cnt: int = 0
        for i, _str in line_count_iter(rsplit("(?:\n@.*)*\ndef ", sub_text)):
            if _cnt == 0:
                self._header = _str.replace("\n", "\n    ")
            elif _str.startswith(("\n@property", "\n@cached_property")):
                children.append(
                    PyProperty(_str, parent=self, start_line=self.start_line + i - 1)
                )
            else:
                children.append(
                    PyMethod(_str, parent=self, start_line=self.start_line + i - 1)
                )
            _cnt += 1
        return children


class PyFunc(TextTree):
    """Stores the code and docstring of a function."""

    def __texttree_post_init__(self, path_or_text: Union[Path, str]) -> None:
        self.text, n, _ = counted_strip(path_or_text)
        self.start_line += n
        self.name = re.search("def .*?\\(", self.text).group()[4:-1] + "()"

    @cached_property
    def doc(self) -> "Docstring":
        searched = re.search('""".*?"""', self.text, re.DOTALL)
        if searched:
            _doc = re.sub("\n    ", "\n", searched.group()[3:-3])
        else:
            _doc = ""
        return NumpyFormatDocstring(_doc, parent=self)

    @cached_property
    def header(self) -> "PyContent":
        _header = re.search(".*\n[^\\s][^\n]*", self.text, re.DOTALL).group()
        return PyContent(_header, parent=self)


class PyMethod(PyFunc):
    """Stores the code and docstring of a class method."""

    def __texttree_post_init__(self, path_or_text: Union[Path, str]) -> None:
        super().__texttree_post_init__(path_or_text=path_or_text)
        self.spaces = 4


class PyProperty(PyMethod):
    """Stores the code and docstring of a class property."""

    def __texttree_post_init__(self, path_or_text: Union[Path, str]) -> None:
        super().__texttree_post_init__(path_or_text=path_or_text)
        self.name = self.name[:-2]


class PyContent(TextTree):
    """
    Stores a part of a file that is not storable by instances of other
    subclasses.

    """

    def __texttree_post_init__(self, path_or_text: Union[Path, str]) -> None:
        self.text, n, _ = counted_strip(path_or_text)
        self.start_line += n
        self.name = NULL

    @cached_property
    def doc(self) -> "Docstring":
        return NumpyFormatDocstring("", parent=self)

    @cached_property
    def header(self) -> "PyContent":
        return self


class NonPyFile(TextTree):
    """Stores a non-python file."""

    def __texttree_post_init__(self, path_or_text: Union[Path, str]) -> None:
        if isinstance(path_or_text, Path):
            self.path = as_path(path_or_text, home=self.home)
            self.text, n, _ = counted_strip(self.path.read_text(encoding=self.encoding))
        else:
            self.text, n, _ = counted_strip(path_or_text)

        self.start_line += n
        self.name = self.path.name

    @cached_property
    def doc(self) -> "Docstring":
        return NumpyFormatDocstring("", parent=self)

    @cached_property
    def header(self) -> "PyContent":
        return self
