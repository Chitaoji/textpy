"""
Experimental properties of textpy: back_to_py38(), etc.

"""

import re
from typing import TYPE_CHECKING, List, Tuple

from .interaction import Replacer, display_params
from .utils.re_extensions import SmartPattern

if TYPE_CHECKING:
    from .abc import PyText
    from .utils.re_extensions import ReplType

__all__ = ["back_to_py38"]


def back_to_py38(module: "PyText") -> Replacer:
    """
    Try to make a module executable in py38 by rolling back the features that
    only make sense in py39 or later.

    Parameters
    ----------
    module : PyText
        PyText object.

    """
    features_to_rollback = [__union_types, __type_hint_generics]
    styler, display_params.enable_styler = display_params.enable_styler, False
    replacer = Replacer()
    for f in features_to_rollback:
        replacer = f(module, replacer)
    display_params.enable_styler = styler
    return replacer.to_styler()


def __union_types(module: "PyText", replacer: Replacer) -> Replacer:
    """See PEP 604."""
    new_replacer = module.replace(
        SmartPattern('[^:=>\\[\\]()"\\{\\}\n,|]*{}\\s*\\|[^:=>\\[\\]()\\{\\}"\n,]*{}'),
        lambda x: "Union[" + re.sub("\\s*\\|\\s*", ", ", x.group()).strip() + "]",
        based_on=replacer,
    )
    replacer.join(new_replacer)
    return replacer


def __type_hint_generics(module: "PyText", replacer: Replacer) -> Replacer:
    """See PEP 585."""
    pairs: List[Tuple[str, str]] = [
        ("list", "List"),
        ("tuple", "Tuple"),
        ("dict", "Dict"),
        ("set", "Set"),
        ("frozenset", "FrozenSet"),
        ("type", "Type"),
    ]
    for p in pairs:
        while r := module.replace(*__type_hint_generics_0(*p), based_on=replacer):
            replacer.join(r)
    return replacer


def __type_hint_generics_0(replaced: str, to_replace: str) -> Tuple[str, "ReplType"]:
    return (
        f"((->|:)[^=\n]*?\\W|\n\\s*){replaced}[\\[\\]),:]",
        lambda m: m.group()[: -1 - len(replaced)] + to_replace + m.group()[-1],
    )
