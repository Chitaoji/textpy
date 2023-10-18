import warnings

__all__ = []

# import `re_extended` if exists
try:
    from . import re_extended

    __all__.extend(re_extended.__all__)
    from .re_extended import *

except ImportError as e:
    if isinstance(e, ModuleNotFoundError):
        raise e
    else:
        warnings.warn(e.msg, Warning)
