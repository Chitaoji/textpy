import re
from functools import cached_property
from typing import *

from .abc import Docstring
from .utils.re_extended import rsplit

__all__ = ["NumpyFormatDocstring"]


class NumpyFormatDocstring(Docstring):
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
