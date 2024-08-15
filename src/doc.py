"""
Contains a docstring class: NumpyFormatDocstring.

NOTE: this module is private. All functions and objects are available in the main
`textpy` namespace - use that instead.

"""

import re
from functools import cached_property
from typing import Dict

from .abc import Docstring
from .re_extensions import rsplit

__all__ = ["NumpyFormatDocstring"]


class NumpyFormatDocstring(Docstring):
    """
    Stores a numpy-formatted docstring.

    """

    @cached_property
    def sections(self) -> Dict[str, str]:
        details: Dict[str, str] = {}
        for i, _str in enumerate(rsplit(".*\n-+\n", self.text)):
            if i == 0:
                details["_header_"] = _str.strip()
            else:
                _key, _value = re.split("\n-+\n", _str, maxsplit=1)
                details[_key] = _value.strip()
        return details
