"""
Contains the core of textpy: module().

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional, Union

from typing_extensions import deprecated

from .abc import P, as_path
from .texttree import PyDir, PyFile

if TYPE_CHECKING:
    from ._typing import _defaults
    from .abc import TextTree
else:
    _defaults = ...  # pylint: disable=invalid-name

__all__ = ["module", "textpy", "DEFAULT_IGNORE_PATHS"]

DEFAULT_IGNORE_PATHS = ["build", ".git", ".github"]


def module(
    path_or_text: Union[Path, str],
    home: Optional[Union[Path, str]] = None,
    encoding: Optional[str] = None,
    ignore: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    *,
    _: Callable[P, None] = _defaults,
) -> "TextTree[P]":
    """
    Statically analyzes a python file or a python module. Each python file
    is recommended to be formatted with `PEP-8`, otherwise the analyzing
    result could be surprising.

    Parameters
    ----------
    path_or_text : Union[Path, str]
        File path, module path or file text.
    home : Union[Path, str], optional
        Specifies the home path when `path_or_text` is relative, by default
        None.
    encoding : str, optional
        Specifies encoding, by default None.
    ignore : List[str], optional
        Subpaths to ignore (prior to `include`), by default
        `DEFAULT_IGNORE_PATHS`.
    include : List[str], optional
        Non-python files to include, by default None.

    Returns
    -------
    TextTree
        A class written for python code analysis.

    Raises
    ------
    ValueError
        Raised when `path` is not found.

    See Also
    --------
    PyDir : Stores a directory.
    PyFile : Stores a python file.
    PyModule : PyDIr | PyFile.
    PyFunc : Stores the code and docstring of a function.
    PyClass : Stores the code and docstring of a class.
    PyMethod : Stores the code and docstring of a class method.
    PyProperty : Stores the code and docstring of a class property.
    PyContent : Stores other infomation.
    NonPyFile : Stores a non-python file.
    NumpyFormatDocstring : Stores a numpy-formatted docstring.

    """
    path_or_text = as_path(path_or_text, home=home)
    if encoding is None:
        encoding = sys.getdefaultencoding()
    if isinstance(path_or_text, str) or path_or_text.is_file():
        return PyFile(path_or_text, home=home, encoding=encoding)
    if path_or_text.is_dir():
        ignore = DEFAULT_IGNORE_PATHS if ignore is None else ignore
        return PyDir(
            path_or_text, home=home, encoding=encoding, ignore=ignore, include=include
        )
    raise FileExistsError(f"file not exists: '{path_or_text}'")


textpy = deprecated(
    "tx.textpy() is deprecated and will be removed in a future version "
    "- use tx.module() instead"
)(module)


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
