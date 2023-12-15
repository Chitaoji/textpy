'''
# textpy
Reads a python file/module and statically analyzes it. This works well with Jupyter extensions in
VScode, and have better performance when the file/module is formatted with *PEP-8*.

## Examples
Create a new file named `myfile.py` under `./examples/` (or any dir, just for an example):

```py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import *


class MyClass:
    def __init__(self):
        """Write something."""
        self.var_1 = "hahaha"
        self.var_2 = "blabla"


def print_my_class(a: MyClass):
    """
    Print something.

    Parameters
    ----------
    a : ThisIsAClass
        An object.

    """
    print(a.var_1, a.var_2)
```

Run the following codes to find all the occurrences of the pattern "va" in `myfile.py`:

```py
>>> from textpy import textpy
>>> res = textpy("./examples/myfile.py").findall("va", styler=False)
>>> res
examples/myfile.py:10: '        self.var_1 = "hahaha"'
examples/myfile.py:11: '        self.var_2 = "blabla"'
examples/myfile.py:24: '    print(a.var_1, a.var_2)'
```

Also, when using a Jupyter notebook in VScode, you can run a cell like this:

```py
>>> from textpy import textpy
>>> textpy("./examples/myfile.py").findall("va")
```

Note that in the Jupyter notebook case, the matched substrings are **clickable**, linking to where
the patterns were found.

Now suppose you've got a python module consists of a few files, for example, our `textpy` module
itself, you can do almost the same thing:

```py
>>> module_path = "textpy/" # you can type any path here
>>> pattern = "note.*k" # type any regular expression here

>>> res = textpy(module_path).findall("note.*k", styler=False, line_numbers=False)
>>> res
textpy/abc.py: '            in a Jupyter notebook, this only takes effect when'
textpy/abc.py: '        in a Jupyter notebook.'
textpy/__init__.py: 'Also, when using a Jupyter notebook in VScode, you can run a cell like this:'
textpy/__init__.py: 'Note that in the Jupyter notebook case, the matched substrings are
**clickable**, linking to where'
textpy/__init__.py: '>>> pattern = "note.*k" # type any regular expression here'
textpy/__init__.py: '>>> res = textpy(module_path).findall("note.*k", styler=False,
line_numbers=False)'
```

## See Also
### Github repository
* https://github.com/Chitaoji/textpy/

### PyPI project
* https://pypi.org/project/textpy/

## License
This project falls under the BSD 3-Clause License.

'''
import lazyr

VERBOSE = 0

lazyr.register("pandas", verbose=VERBOSE)

# pylint: disable=wrong-import-position
from . import abc, core, doc, text
from .__version__ import __version__
from .abc import *
from .core import *
from .doc import *
from .text import *

__all__ = []
__all__.extend(abc.__all__)
__all__.extend(core.__all__)
__all__.extend(doc.__all__)
__all__.extend(text.__all__)
