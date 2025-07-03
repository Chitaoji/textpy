'''
# textpy
Reads a python module and statically analyzes it. This works well with jupyter
extensions in *VS Code*, and will have better performance when the module files are
formatted with *PEP-8*.

## Quick Start
To demonstrate the usage of this module, we put a file named `myfile.py` under
`./examples/` (you can find it in the repository, or create a new file of your own):
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
Run the following codes to find all the occurrences of some pattern (for example,
"MyBook") in `myfile.py`:
```py
>>> import textpy as tx
>>> myfile = tx.module("./examples/myfile.py") # reads the python module

>>> myfile.findall("MyBook")
examples/myfile.py:7: 'class <MyBook>:'
examples/myfile.py:24: 'def print_my_book(book: <MyBook>) -> None:'
examples/myfile.py:30: '    book : <MyBook>'
```
If you are using a jupyter notebook, you can run a cell like this:
```py
>>> myfile.findall("MyBook")
```

<table class="textpy-table-classic">
<thead>
<tr>
<th>source</th>
<th>match</th>
</tr>
</thead>
<tbody>
<tr>
<td><a href="examples/myfile.py#L1" style="text-
decoration:none;color:inherit">myfile</a>.<a href="examples/myfile.py#L7" style="text-
decoration:none;color:inherit">MyBook</a>:<a href="examples/myfile.py#L7" style="text-
decoration:none;color:inherit">7</a></td>
<td>class <a href="examples/myfile.py#L7" style="text-
decoration:none;color:#cccccc;background-color:#505050">MyBook</a>:</td>
</tr>
<tr>
<td><a href="examples/myfile.py#L1" style="text-
decoration:none;color:inherit">myfile</a>.<a href="examples/myfile.py#L24" style="text-
decoration:none;color:inherit">print_my_book()</a>:<a href="examples/myfile.py#L24"
style="text-decoration:none;color:inherit">24</a></td>
<td>def print_my_book(book: <a href="examples/myfile.py#L24" style="text-
decoration:none;color:#cccccc;background-color:#505050">MyBook</a>) -&gt; None:</td>
</tr>
<tr>
<td><a href="examples/myfile.py#L1" style="text-
decoration:none;color:inherit">myfile</a>.<a href="examples/myfile.py#L24" style="text-
decoration:none;color:inherit">print_my_book()</a>:<a href="examples/myfile.py#L30"
style="text-decoration:none;color:inherit">30</a></td>
<td>    book : <a href="examples/myfile.py#L30" style="text-
decoration:none;color:#cccccc;background-color:#505050">MyBook</a></td>
</tr>
</tbody>
</table>

In this case, the matched substrings are **clickable**, linking to where the patterns
were found.

## Usage
### tx.module()
The previous demonstration introduced the core function `tx.module()`. The return value
of `tx.module()` is a subinstance of the abstract class `tx.TextTree`, which supports
various text manipulation methods:
```py
>>> isinstance(myfile, tx.TextTree)
True
```
Sometimes, your python module may contain not just one file, but don't worry, since
`tx.module()` provides support for complex file hierarchies. If the path points to a
single file, the return type will be `PyFile`; otherwise, the return type will be
`PyDir` - both of which are subclasses of `tx.TextTree`.

In conclusion, once you've got a python package, you can simply give the package dirpath
to `tx.module()`, and do things like before:

```py
>>> pkg_dir = "" # type any path here
>>> pattern = "" # type any regex pattern here

>>> res = tx.module(pkg_dir).findall(pattern)
```

### tx.TextTree.findall()
As mentioned before, user can use `.findall()` to find all non-overlapping matches of
some pattern in a python module.
```py
>>> myfile.findall("optional")
examples/myfile.py:13: '    story : str, <optional>'
```
The object returned by `.findall()` has a `_repr_mimebundle_()` method to beautify the
representation inside a jupyter notebook. However, you can compulsively disable this
feature by setting `display_params.use_mimebundle` to False:
```py
>>> from textpy import display_params
>>> display_params.use_mimebundle = False
```
In addition, the `.findall()` method has some optional parameters to customize the
pattern, including `whole_word=`, `case_sensitive=`, and `regex=`.
```py
>>> myfile.findall("mybook", case_sensitive=False, regex=False, whole_word=True)
examples/myfile.py:7: 'class <MyBook>:'
examples/myfile.py:24: 'def print_my_book(book: <MyBook>) -> None:'
examples/myfile.py:30: '    book : <MyBook>'
```

### tx.TextTree.replace()
Use `.replace()` to find all non-overlapping matches of some pattern, and replace them
with another string:
```py
>>> replacer = myfile.replace("book", "magazine")
>>> replacer
examples/myfile.py:9: '    A <book/magazine> that records a story.'
examples/myfile.py:20: '            self.content = "This <book/magazine> is empty."'
examples/myfile.py:24: 'def print_my_<book/magazine>(<book/magazine>: MyBook) -> None:'
examples/myfile.py:26: '    Print a <book/magazine>.'
examples/myfile.py:30: '    <book/magazine> : MyBook'
examples/myfile.py:31: '        A <book/magazine>.'
examples/myfile.py:34: '    print(<book/magazine>.content)'
```
At this point, the replacement has not actually taken effect yet. Use `.confirm()` to
confirm the changes and write them to the file(s):
```py
>>> replacer.confirm()
{'successful': ['examples/myfile.py'], 'failed': []}
```
If you want to rollback the changes, run:
```py
>>> replacer.rollback()
{'successful': ['examples/myfile.py'], 'failed': []}
```

### tx.TextTree.delete()
Use `.delete()` to find all non-overlapping matches of some pattern, and delete them:
```py
>>> deleter = myfile.delete("book")
>>> deleter
examples/myfile.py:9: '    A <book> that records a story.'
examples/myfile.py:20: '            self.content = "This <book> is empty."'
examples/myfile.py:24: 'def print_my_<book>(<book>: MyBook) -> None:'
examples/myfile.py:26: '    Print a <book>.'
examples/myfile.py:30: '    <book> : MyBook'
examples/myfile.py:31: '        A <book>.'
examples/myfile.py:34: '    print(<book>.content)'

>>> deleter.confirm()
{'successful': ['examples/myfile.py'], 'failed': []}

>>> deleter.rollback()
{'successful': ['examples/myfile.py'], 'failed': []}
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

lazyr.VERBOSE = 0

lazyr.register("pandas")
lazyr.register("black")

# pylint: disable=wrong-import-position
from . import abc, core, doc, interaction, texttree, utils
from .__version__ import __version__
from .abc import *
from .core import *
from .doc import *
from .interaction import *
from .texttree import *

__all__ = ["utils"]
__all__.extend(abc.__all__)
__all__.extend(core.__all__)
__all__.extend(interaction.__all__)
__all__.extend(doc.__all__)
__all__.extend(texttree.__all__)
