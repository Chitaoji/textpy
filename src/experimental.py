"""
Experimental properties of textpy: back_to_py38(), etc.

"""

import re
from typing import TYPE_CHECKING, List, Tuple

from .interaction import Replacer
from .re_extensions import SmartPattern

if TYPE_CHECKING:
    from ._typing import ReplType
    from .abc import TextTree

__all__ = ["back_to_py38"]


def back_to_py38(module: "TextTree") -> Replacer:
    """
    Try to make a module executable in py38 by rolling back the features that
    only make sense in py39 or later.

    Parameters
    ----------
    module : TextTree
        TextTree object.

    """
    features_to_rollback = [__union_types, __type_hint_generics]
    replacer = Replacer()
    for f in features_to_rollback:
        replacer = f(module, replacer)
    return replacer


def __union_types(module: "TextTree", replacer: Replacer) -> Replacer:
    """See PEP 604."""
    new_replacer = module.replace(
        SmartPattern('[^:=>\\[\\]()"\\{\\}\n,|]*{}\\s*\\|[^:=>\\[\\]()\\{\\}"\n,]*{}'),
        lambda x: "Union[" + re.sub("\\s*\\|\\s*", ", ", x.group()).strip() + "]",
        based_on=replacer,
    )
    replacer.join(new_replacer)
    return replacer


def __type_hint_generics(module: "TextTree", replacer: Replacer) -> Replacer:
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
        while r := module.replace(*__type_hint_pairs(*p), based_on=replacer):
            replacer.join(r)
    return replacer


def __type_hint_pairs(replaced: str, to_replace: str) -> Tuple[str, "ReplType"]:
    return (
        f"((->|:)[^=\n]*?\\W|\n\\s*){replaced}[\\[\\]),:]",
        lambda m: m.group()[: -1 - len(replaced)] + to_replace + m.group()[-1],
    )
