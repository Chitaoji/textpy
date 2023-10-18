import warnings

__all__ = []

# import `abc` if exists
try:
    from . import abc

    __all__.extend(abc.__all__)
    from .abc import *

except ImportError as e:
    if isinstance(e, ModuleNotFoundError):
        raise e
    else:
        warnings.warn(e.msg, Warning)

# import `core` if exists
try:
    from . import core

    __all__.extend(core.__all__)
    from .core import *

except ImportError as e:
    if isinstance(e, ModuleNotFoundError):
        raise e
    else:
        warnings.warn(e.msg, Warning)

# import `element` if exists
try:
    from . import element

    __all__.extend(element.__all__)
    from .element import *

except ImportError as e:
    if isinstance(e, ModuleNotFoundError):
        raise e
    else:
        warnings.warn(e.msg, Warning)

# import `format` if exists
try:
    from . import format

    __all__.extend(format.__all__)
    from .format import *

except ImportError as e:
    if isinstance(e, ModuleNotFoundError):
        raise e
    else:
        warnings.warn(e.msg, Warning)
