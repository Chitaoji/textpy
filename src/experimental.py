"""
Experimental properties of textpy: back_to_py38(), etc.

"""

from typing import TYPE_CHECKING, List, Tuple

from .interaction import Replacer, display_params

if TYPE_CHECKING:
    from .abc import PyText
    from .utils.re_extensions import PatternStr, ReprStr

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
    features_to_rollback = [__type_hint_generics]
    styler, display_params.enable_styler = display_params.enable_styler, False
    replacer = Replacer()
    for f in features_to_rollback:
        replacer.join(f(module))
    display_params.enable_styler = styler
    return replacer.to_styler()


def __union_types(module: "PyText") -> Replacer:
    """See PEP 604."""
    replacer = Replacer()
    return replacer


def __type_hint_generics(module: "PyText") -> Replacer:
    """See PEP 585."""
    replacer = Replacer()
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


def __type_hint_generics_0(replaced: str, to_replace: str) -> Tuple[str, "ReprStr"]:
    return (
        f"(?:(->|:)[^=\n]*?\\W|\n\\s*){replaced}[\\[\\]),:]",
        lambda m: m.group()[: -1 - len(replaced)] + to_replace + m.group()[-1],
    )
