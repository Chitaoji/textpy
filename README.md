# textpy
Reads a python file/module and statically analyzes it. This works well with Jupyter extensions in VScode, and has better performance when the file/module is formatted with *PEP-8*.

## Installation
```sh
$ pip install textpy
```

## Requirements
```txt
lazyr>=0.0.16
pandas>=1.4.0 # A lower version is also acceptable, but some features will be invalid
Jinja2
```

## Examples
To demonstrate the usage of this module, we put a file named `myfile.py` under `./examples/` (you can find it in the repository, or create a new file of your own):

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
<!--html-->
and the output will be like:

<table id="T_eb71c">
  <thead>
    <tr>
      <th id="T_eb71c_level0_col0" class="col_heading level0 col0">source</th>
      <th id="T_eb71c_level0_col1" class="col_heading level0 col1">match</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td id="T_eb71c_row0_col0" class="data row0 col0"><a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>myfile</a>.<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>MyClass</a>.<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>__init__</a>:<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>20</a></td>
      <td id="T_eb71c_row0_col1" class="data row0 col1"> self.<a href='examples/myfile.py'
          style='text-decoration:none;color:#cccccc;background-color:#505050'>content</a> = "This book is empty."</td>
    </tr>
    <tr>
      <td id="T_eb71c_row1_col0" class="data row1 col0"><a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>myfile</a>.<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>MyClass</a>.<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>__init__</a>:<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>21</a></td>
      <td id="T_eb71c_row1_col1" class="data row1 col1"> self.<a href='examples/myfile.py'
          style='text-decoration:none;color:#cccccc;background-color:#505050'>content</a> = story</td>
    </tr>
    <tr>
      <td id="T_eb71c_row2_col0" class="data row2 col0"><a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>myfile</a>.<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>print_my_class</a>:<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>34</a></td>
      <td id="T_eb71c_row2_col1" class="data row2 col1"> print(book.<a href='examples/myfile.py'
          style='text-decoration:none;color:#cccccc;background-color:#505050'>content</a>)</td>
    </tr>
  </tbody>
</table>
<!--/html-->

Note that in the Jupyter notebook case, the matched substrings are **clickable**, linking to where the patterns were found.

Now suppose you've got a python module consists of a few files, for example, our `textpy` module itself, you can do almost the same thing by giving the module path:

```py
>>> module_path = "textpy/" # you can type any path here
>>> pattern = "note.*k" # type any regular expression here

>>> res = textpy(module_path).findall("note.*k", styler=False, line_numbers=False)
>>> res
textpy/abc.py: '            in a Jupyter notebook, this only takes effect when'
textpy/abc.py: '        in a Jupyter notebook.'
textpy/__init__.py: 'Also, when using a Jupyter notebook in VScode, you can run a cell like this:'
textpy/__init__.py: 'Note that in the Jupyter notebook case, the matched substrings are **clickable**, linking to where'
textpy/__init__.py: '>>> pattern = "note.*k" # type any regular expression here'
textpy/__init__.py: '>>> res = textpy(module_path).findall("note.*k", styler=False, line_numbers=False)'
```

## See Also
### Github repository
* https://github.com/Chitaoji/textpy/

### PyPI project
* https://pypi.org/project/textpy/

## License
This project falls under the BSD 3-Clause License.

## History
### v0.1.22
* New method `TextPy.replace()` for text replacing.
* Added a new dunder method `PyText.__truediv__()` as an alternative to `.jumpto()`.
* New class `PyComponent` for storing components of a file, class, or function.

### v0.1.21
* Improved behavior of clickables.

### v0.1.20
* Fixed issues:
  * Incorrectly displaying file paths in the output of `TextPy.findall(styler=False)`;
  * Expired file links in the output of `TextPy.findall(styler=True, line_numbers=False)`.

### v0.1.19
* Various improvements.

### v0.1.18
* Updated LICENSE.

### v0.1.17
* Refactored README.

### v0.1.16
* Lazily imported *pandas* to reduce the time cost for importing.

### v0.1.12
* New optional parameters for `TextPy.findall()` :
  * `whole_word=` : whether to match whole words only;
  * `case_sensitive=` : specifies case sensitivity.

### v0.1.10
* New optional parameter `encoding=` for `textpy()`.

### v0.1.9
* Removed unnecessary dependencies.

### v0.1.8
* Bugfix under Windows system.

### v0.1.5
* Provided compatibility with *pandas* versions lower than 1.4.0.
* Updated `textpy()` :
  * `Path` objects are now acceptable as parameters.
  * New optional parameter `home` to specify the home path.
* More flexible presentation of output from `TextPy.findall()`.

### v0.1.4
* Fixed a display issue of README on PyPI.

### v0.1.3
* Initial release.
