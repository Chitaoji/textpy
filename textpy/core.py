from pathlib import Path
from typing import *

from .abc import PyText
from .element import PyFile, PyModule, as_path

__all__ = ["textpy"]


def textpy(
    path_or_text: Union[Path, str], home: Union[Path, str, None] = None
) -> PyText:
    """
    Statically analyzes a python file or a python module. Each python
    file is recommended to be formatted with `black` and `Auto Docstring
    (numpy format)`, otherwise unexpected errors may occur.

    Parameters
    ----------
    path_or_text : Union[Path, str]
        File path, module path or file text.
    home : Union[Path, str, None], optional
        Specifies the home path if `path_or_text` is relative, by
        default None.

    Returns
    -------
    TextPy
        A class written for python code analysis.

    Raises
    ------
    ValueError
        Raised when `path` is not found.

    See Also
    --------
    PyModule : Corresponds to a python module.
    PyFile : Contains the text of a python file.
    PyClass : Contains the text of a class and its docstring.
    PyMethod : Contains the text of a class method and its docstring.
    PyFunc : Contains the text of a function and its docstring.
    NumpyFormatDocstring : Stores a numpy-formatted docstring.

    """
    path_or_text = as_path(path_or_text, home=home)
    if isinstance(path_or_text, str) or path_or_text.is_file():
        return PyFile(path_or_text, home=home)
    elif path_or_text.is_dir():
        return PyModule(path_or_text, home=home)
    else:
        raise ValueError(f"path not exists: {path_or_text}")
