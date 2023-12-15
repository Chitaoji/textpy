"""
Contains the core of textpy: textpy().

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""
from pathlib import Path
from typing import Optional, Union

from .abc import PyText, as_path
from .text import PyFile, PyModule

__all__ = ["textpy"]


def textpy(
    path_or_text: Union[Path, str],
    home: Union[Path, str, None] = None,
    encoding: Optional[str] = None,
) -> PyText:
    """
    Statically analyzes a python file or a python module. Each python
    file is recommended to be formatted with `PEP-8`, otherwise the
    analyzing output could be surprising.

    Parameters
    ----------
    path_or_text : Union[Path, str]
        File path, module path or file text.
    home : Union[Path, str, None], optional
        Specifies the home path when `path_or_text` is relative, by
        default None.
    encoding : Optional[str]
        Specifies encoding, by default None.

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
    PyModule : Contains a python module.
    PyFile : Contains the code of a python file.
    PyClass : Contains the code and docstring of a class.
    PyMethod : Contains the code and docstring of a class method.
    PyFunc : Contains the code and docstring of a function.
    NumpyFormatDocstring : Stores a numpy-formatted docstring.

    """
    path_or_text = as_path(path_or_text, home=home)
    if isinstance(path_or_text, str) or path_or_text.is_file():
        return PyFile(path_or_text, home=home, encoding=encoding)
    if path_or_text.is_dir():
        return PyModule(path_or_text, home=home, encoding=encoding)
    raise FileExistsError(f"file not exists: '{path_or_text}'")
