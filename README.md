# textpy
Reads a python module and statically analyzes it. This works well with Jupyter extensions in VScode, and will have better performance when the module files are formatted with *PEP-8*.

## Installation
```sh
$ pip install textpy
```

## Requirements
```txt
lazyr>=0.0.16
pandas
Jinja2
```
NOTE: pandas>=1.4.0 is recommended. Lower versions of pandas are also available, but some properties of this package will be affected.

## Quick Start
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
Run the following codes to find all the occurrences of some pattern (for example, "MyBook") in `myfile.py`:
```py
>>> import textpy as tx
>>> myfile = tx.module("./examples/myfile.py") # reads the python module

>>> myfile.findall("MyBook", styler=False)
examples/myfile.py:7: 'class <MyBook>:'
examples/myfile.py:24: 'def print_my_book(book: <MyBook>) -> None:'
examples/myfile.py:30: '    book : <MyBook>'
```
If you are using a Jupyter notebook in VS Code, you can run a cell like this:
```py
>>> myfile.findall("content")
```
<!--html-->
<table id="T_19b39">
  <thead>
    <tr>
      <th id="T_19b39_level0_col0" class="col_heading level0 col0" >source</th>
      <th id="T_19b39_level0_col1" class="col_heading level0 col1" >match</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td id="T_19b39_row0_col0" class="data row0 col0" ><a href='examples/myfile.py' style='text-decoration:none;color:inherit'>myfile</a>.<a href='examples/myfile.py' style='text-decoration:none;color:inherit'>MyBook</a>:<a href='examples/myfile.py' style='text-decoration:none;color:inherit'>7</a></td>
      <td id="T_19b39_row0_col1" class="data row0 col1" >class <a href='examples/myfile.py' style='text-decoration:none;color:#cccccc;background-color:#505050'>MyBook</a>:</td>
    </tr>
    <tr>
      <td id="T_19b39_row1_col0" class="data row1 col0" ><a href='examples/myfile.py' style='text-decoration:none;color:inherit'>myfile</a>.<a href='examples/myfile.py' style='text-decoration:none;color:inherit'>print_my_book()</a>:<a href='examples/myfile.py' style='text-decoration:none;color:inherit'>24</a></td>
      <td id="T_19b39_row1_col1" class="data row1 col1" >def print_my_book(book: <a href='examples/myfile.py' style='text-decoration:none;color:#cccccc;background-color:#505050'>MyBook</a>) -> None:</td>
    </tr>
    <tr>
      <td id="T_19b39_row2_col0" class="data row2 col0" ><a href='examples/myfile.py' style='text-decoration:none;color:inherit'>myfile</a>.<a href='examples/myfile.py' style='text-decoration:none;color:inherit'>print_my_book()</a>:<a href='examples/myfile.py' style='text-decoration:none;color:inherit'>30</a></td>
      <td id="T_19b39_row2_col1" class="data row2 col1" >    book : <a href='examples/myfile.py' style='text-decoration:none;color:#cccccc;background-color:#505050'>MyBook</a></td>
    </tr>
  </tbody>
</table>
<!--/html-->
Note that in the Jupyter notebook case, the matched substrings are **clickable**, linking to where the patterns were found.

## Examples
### tx.module()
The previous demonstration introduced the core function `tx.module()`. In fact, the return type of `tx.module()` is a subclass of the abstract class `PyText`, who supports various text manipulation methods:
```py
>>> isinstance(m, tx.PyText)
True
```
Sometimes, your python module may contain not just one file but multiple files and folders, but don't worry, since `tx.module()` provides support for complex file hierarchies. The return type will be either `PyDir` or `PyFile`, both subclasses of `PyText`, depending on the path type.

In conclusion, suppose you've got a python package, you can simply give the package dirpath to `tx.module()`, and do things like before:

```py
>>> pkg_dir = "examples/" # you can type any path here
>>> pattern = "" # you can type any regular expression here

>>> res = tx.module(pkg_dir).findall(pattern)
```

### tx.PyText.findall()
As mentioned before, user can use `.findall()` to find all non-overlapping matches of some pattern in a python module.
```py
>>> myfile.findall("optional", styler=False)
examples/myfile.py:13: '    story : str, <optional>'
```
The optional argument `styler=` determines whether to use a pandas `Styler` object to beautify the representation. If you are running python in the console, please always set `styler=False`. You can also disable the stylers in `display_params`, so that you don't need to repeat `styler=False` every time in the following examples:
```py
>>> from textpy import display_params
>>> display_params.enable_styler = False
``` 
In addition, the `.findall()` method has some optional parameters to customize the matching pattern, including `whole_word=`, `case_sensitive=`, and `regex=`.
```py
>>> myfile.findall("mybook", case_sensitive=False, regex=False, whole_word=True)
examples/myfile.py:7: 'class <MyBook>:'
examples/myfile.py:24: 'def print_my_book(book: <MyBook>) -> None:'
examples/myfile.py:30: '    book : <MyBook>'
```

### tx.PyText.replace()
Use `.replace()` to find all non-overlapping matches of some pattern, and replace them with another string:
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
At this point, the replacement has not yet taken effect on the files. Use `.confirm()` to confirm the changes and make them done:
```py
>>> replacer.confirm()
{'successful': ['examples/myfile.py'], 'failed': []}
```

### tx.PyText.delete()
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
```

## See Also
### Github repository
* https://github.com/Chitaoji/textpy/

### PyPI project
* https://pypi.org/project/textpy/

## License
This project falls under the BSD 3-Clause License.

## History
### v0.1.24
* New method `PyText.is_file()` and `PyText.is_dir()` to find out whether the instance represents a file / directory.
* Defined the comparison ordering methods `__eq__()`, `__gt__()`, and `__ge__()` for `PyText`. They compares two `PyText` object via their absolute paths.
* New utility function `utils.re_extensions.smart_search()` and `utils.re_extensions.smart_match()`.

### v0.1.23
* New utility function `utils.re_extensions.word_wrap()`.
* Various improvements.

### v0.1.22
* `textpy()` is going to be deprecated to avoid conflicts with the package name `textpy`. Please use `module()` insead.
* New method `PyText.replace()`, `PyText.delete()`.
* New class `Replacer` as the return type of `PyText.replace()`, with public methods `.confirm()`, `.rollback()`, etc.
* Added a dunder method `PyText.__truediv__()` as an alternative to `PyText.jumpto()`.
* New subclass `PyContent` inheriting from `PyText`. A `PyContent` object stores a part of a file that is not storable by instances of other subclasses.

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
