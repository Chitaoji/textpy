'''
# textpy
Reads a python file/module and statically analyzes it. This works well with Jupyter extensions in
VScode, and has better performance when the file/module is formatted with *PEP-8*.

## Examples
To demonstrate the usage of this module, we put a file named `myfile.py` under `./examples/` (you
can find it in the repository, or create a new file of your own):

```py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional


class MyBook:
    """
    A book that records a story.

    Parameters
    ----------
    story : str, optional
        Story to record, by default None.

    """

    def __init__(self, story: Optional[str] = None) -> None:
        if story is None:
            self.content = "This book is empty."
        self.content = story


def print_my_book(book: MyBook) -> None:
    """
    Print a book.

    Parameters
    ----------
    book : MyBook
        A book.

    """
    print(book.content)
```

Run the following codes to find all the occurrences of the pattern "content" in `myfile.py`:

```py
>>> from textpy import textpy
>>> res = textpy("./examples/myfile.py").findall("content", styler=False)
>>> res
examples/myfile.py:20: '            self.content = "This book is empty."'
examples/myfile.py:21: '        self.content = story'
examples/myfile.py:34: '    print(book.content)'
```

Also, when using a Jupyter notebook in VScode, you can run a cell like this:

```py
>>> from textpy import textpy
>>> textpy("./examples/myfile.py").findall("content")
```


Note that in the Jupyter notebook case, the matched substrings are **clickable**, linking to where
the patterns were found.

Now suppose you've got a python module consists of a few files, for example, our `textpy` module
itself, you can do almost the same thing by giving the module path:

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
