"""
Experimental properties of textpy: back_to_py38(), etc.

"""

from typing import TYPE_CHECKING, Callable, List, Tuple, Union

from .interaction import Replacer, display_params

if TYPE_CHECKING:
    from re import Match

    from .abc import PyText
    from .utils.re_extensions import PatternStr

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


def __type_hint_generics(module: "PyText") -> Replacer:
    """See PEP 585."""
    replacer = Replacer()
    pairs: List[Tuple["PatternStr", Union[str, Callable[["Match[str]"], str]]]] = [
        ("list\\[.*?\\]", lambda m: "L" + m.group()[1:]),
        ("tuple\\[.*?\\]", lambda m: "T" + m.group()[1:]),
        ("dict\\[.*?\\]", lambda m: "D" + m.group()[1:]),
        ("set\\[.*?\\]", lambda m: "S" + m.group()[1:]),
        ("frozenset\\[.*?\\]", lambda m: "FrozenSet" + m.group()[9:]),
        ("type\\[.*?\\]", lambda m: "T" + m.group()[1:]),
    ]
    for p in pairs:
        replacer.join(module.replace(*p))
    return replacer
