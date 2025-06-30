"""
Contains the core of textpy: module().

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from colorama import just_fix_windows_console

from .abc import as_path
from .texttree import PyDir, PyFile

if TYPE_CHECKING:
    from .abc import TextTree


__all__ = ["module", "file", "fromstr", "DEFAULT_IGNORED_PATHS"]

DEFAULT_IGNORED_PATHS = ["build", "dist", ".git", ".github"]

just_fix_windows_console()


def module(
    path_or_str: Union[Path, str],
    /,
    home: Optional[Union[Path, str]] = None,
    encoding: Optional[str] = None,
    ignore: Optional[list[str]] = None,
    include: Optional[list[str]] = None,
) -> "TextTree":
    """
    Statically analyzes a python file or a python module. Each python file
    is recommended to be formatted with `PEP-8`, otherwise the analyzing
    result could be surprising.

    Parameters
    ----------
    path_or_str : Union[Path, str]
        File path, module path or file string.
    home : Union[Path, str], optional
        Specifies the home path when `path_or_str` is relative, by default
        None.
    encoding : str, optional
        Specifies encoding, by default None.
    ignore : list[str], optional
        Subpaths to ignore (prior to `include`), by default
        `DEFAULT_IGNORED_PATHS`.
    include : list[str], optional
        Non-python files to include, by default None.

    Returns
    -------
    TextTree
        A class written for python code analysis.

    Raises
    ------
    FileNotFoundError
        Raised when `path` is not found.

    See Also
    --------
    PyDir : reads a directory containing python files.
    PyFile : reads a python file.
    PyModule : PyDIr | PyFile.
    PyFunc : reads the code and docstring of a function.
    PyClass : reads the code and docstring of a class.
    PyMethod : reads the code and docstring of a class method.
    PyProperty : reads the code and docstring of a class property.
    PyContent : contains other infomation.
    NonPyFile : reads a non-python file.
    NumpyFormatDocstring : reads a numpy-formatted docstring.

    """
    if encoding is None:
        encoding = sys.getdefaultencoding()
    if not (path := as_path(path_or_str, home=home)).exists():
        raise FileNotFoundError(f"file not found: '{path}'")
    if path.is_file():
        return PyFile(path, home=home, encoding=encoding)
    if ignore is None:
        ignore = getattr(
            sys.modules[__name__.rpartition(".")[0]], "DEFAULT_IGNORED_PATHS"
        )
    return PyDir(path, home=home, encoding=encoding, ignore=ignore, include=include)


def file(
    path_or_str: Union[Path, str],
    /,
    home: Optional[Union[Path, str]] = None,
    encoding: Optional[str] = None,
) -> "TextTree":
    """
    Statically analyzes a python file. The file is recommended to be
    formatted with `PEP-8`, otherwise the analyzing result could be
    surprising.

    Parameters
    ----------
    path_or_str : Union[Path, str]
        File path, module path or file string.
    home : Union[Path, str], optional
        Specifies the home path when `path_or_str` is relative, by default
        None.
    encoding : str, optional
        Specifies encoding, by default None.

    Returns
    -------
    TextTree
        A class written for python code analysis.

    Raises
    ------
    FileNotFoundError
        Raised when `path` is not found.
    IsADirectoryError
        Raised when `path` is a directory.

    See Also
    --------
    PyDir : reads a directory containing python files.
    PyFile : reads a python file.
    PyModule : PyDIr | PyFile.
    PyFunc : reads the code and docstring of a function.
    PyClass : reads the code and docstring of a class.
    PyMethod : reads the code and docstring of a class method.
    PyProperty : reads the code and docstring of a class property.
    PyContent : contains other infomation.
    NonPyFile : reads a non-python file.
    NumpyFormatDocstring : reads a numpy-formatted docstring.

    """
    if encoding is None:
        encoding = sys.getdefaultencoding()
    if not (path := as_path(path_or_str, home=home)).exists():
        raise FileNotFoundError(f"file not found: '{path}'")
    if path.is_file():
        return PyFile(path, home=home, encoding=encoding)
    raise IsADirectoryError(f"is a directory: '{path}'")


def fromstr(string: Union[Path, str], /) -> "TextTree":
    """
    Statically analyzes a python file from string. The file is
    recommended to be formatted with `PEP-8`, otherwise the analyzing
    result could be surprising.

    Parameters
    ----------
    string : Union[Path, str]
        File string.

    Returns
    -------
    TextTree
        A class written for python code analysis.

    Raises
    ------
    FileNotFoundError
        Raised when `path` is not found.
    NotADirectoryError

    See Also
    --------
    PyDir : reads a directory containing python files.
    PyFile : reads a python file.
    PyModule : PyDIr | PyFile.
    PyFunc : reads the code and docstring of a function.
    PyClass : reads the code and docstring of a class.
    PyMethod : reads the code and docstring of a class method.
    PyProperty : reads the code and docstring of a class property.
    PyContent : contains other infomation.
    NonPyFile : reads a non-python file.
    NumpyFormatDocstring : reads a numpy-formatted docstring.

    """
    return PyFile(string)


# def type_of_script() -> Literal["jupyter", "ipython", "terminal"]:
#     """Returns the type of script."""
#     if "IPython" in sys.modules:
#         ipython = sys.modules["IPython"].get_ipython()
#         ipy_str = str(type(ipython))
#         if "zmqshell" in ipy_str:
#             return "jupyter"
#         if "terminal" in ipy_str:
#             return "ipython"
#     return "terminal"
