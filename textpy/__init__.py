import warnings

import lazyr

from .__version__ import __version__

__all__ = []

lazyr.register("pandas")

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

# import `docfmt` if exists
try:
    from . import docfmt

    __all__.extend(docfmt.__all__)
    from .docfmt import *

except ImportError as e:
    if isinstance(e, ModuleNotFoundError):
        raise e
    else:
        warnings.warn(e.msg, Warning)
