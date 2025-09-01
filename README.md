# textpy
Reads a python module and statically analyzes it. This works well with jupyter extensions in *VS Code*, and will have better performance when the module files are formatted with *PEP-8*.

## Installation
```sh
$ pip install textpy
```

## Requirements
```txt
lazyr
typing-extensions
black
colorama
htmlmaster
re_extensions
```
**NOTE:** *pandas*>=1.4.0 is recommended but not necessary.

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
<td><a href="examples/myfile.py#L1" style="text-decoration:none;color:inherit">myfile</a>.<a href="examples/myfile.py#L7" style="text-decoration:none;color:inherit">MyBook</a>:<a href="examples/myfile.py#L7" style="text-decoration:none;color:inherit">7</a></td>
<td>class <a href="examples/myfile.py#L7" style="text-decoration:none;color:#cccccc;background-color:#505050">MyBook</a>:</td>
</tr>
<tr>
<td><a href="examples/myfile.py#L1" style="text-decoration:none;color:inherit">myfile</a>.<a href="examples/myfile.py#L24" style="text-decoration:none;color:inherit">print_my_book()</a>:<a href="examples/myfile.py#L24" style="text-decoration:none;color:inherit">24</a></td>
<td>def print_my_book(book: <a href="examples/myfile.py#L24" style="text-decoration:none;color:#cccccc;background-color:#505050">MyBook</a>) -&gt; None:</td>
</tr>
<tr>
<td><a href="examples/myfile.py#L1" style="text-decoration:none;color:inherit">myfile</a>.<a href="examples/myfile.py#L24" style="text-decoration:none;color:inherit">print_my_book()</a>:<a href="examples/myfile.py#L30" style="text-decoration:none;color:inherit">30</a></td>
<td>    book : <a href="examples/myfile.py#L30" style="text-decoration:none;color:#cccccc;background-color:#505050">MyBook</a></td>
</tr>
</tbody>
</table>

In this case, the matched substrings are **clickable**, linking to where the patterns were found.

## Usage
### tx.module()
The previous demonstration introduced the core function `tx.module()`. The return value of `tx.module()` is a subinstance of the abstract class `tx.TextTree`, which supports various text manipulation methods:
```py
>>> isinstance(myfile, tx.TextTree)
True
```
Sometimes, your python module may contain not just one file, but don't worry, since `tx.module()` provides support for complex file hierarchies. If the path points to a single file, the return type will be `PyFile`; otherwise, the return type will be `PyDir` - both of which are subclasses of `tx.TextTree`.

In conclusion, once you've got a python package, you can simply give the package dirpath to `tx.module()`, and do things like before:

```py
>>> pkg_dir = "" # type any path here
>>> pattern = "" # type any regex pattern here

>>> res = tx.module(pkg_dir).findall(pattern)
```

### tx.TextTree.findall()
As mentioned before, user can use `.findall()` to find all non-overlapping matches of some pattern in a python module.
```py
>>> myfile.findall("optional")
examples/myfile.py:13: '    story : str, <optional>'
```
The object returned by `.findall()` has a `_repr_mimebundle_()` method to beautify the representation inside a jupyter notebook. However, you can compulsively disable this feature by setting `display_params.use_mimebundle` to False:
```py
>>> from textpy import display_params
>>> display_params.use_mimebundle = False
``` 
In addition, the `.findall()` method has some optional parameters to customize the pattern, including `whole_word=`, `case_sensitive=`, and `regex=`.
```py
>>> myfile.findall("mybook", case_sensitive=False, regex=False, whole_word=True)
examples/myfile.py:7: 'class <MyBook>:'
examples/myfile.py:24: 'def print_my_book(book: <MyBook>) -> None:'
examples/myfile.py:30: '    book : <MyBook>'
```

### tx.TextTree.replace()
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
At this point, the replacement has not actually taken effect yet. Use `.confirm()` to confirm the changes and write them to the file(s):
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

## History
### v0.2.3
* Compatible with `htmlmaster==0.0.4`.

### v0.2.2
* Compatible with `htmlmaster==0.0.2`.

### v0.2.1
* New module-level functions `tx.file()` and `tx.fromstr()`.
* Removed the deprecated function `tx.textpy()`.
* Removed `utils.re_extensions` as a submodule, related utils are now directly import from the package `re_extensions`. User can use an instance of `re_extensions.SmartPattern` as the pattern for `TextTree.findall()`, `TextTree.replace()`, and `TextTree.delete()`.
* After this version, the required Python version is updated to >=3.12.7. Download and install v0.1.32 if the user is under lower Python version (>=3.8.13).

### v0.1.32
* Added `dist` in `DEFAULT_IGNORED_PATHS`.

### v0.1.31
* Got ANSI escapes to work on Windows.

### v0.1.30
* New optional paramter `include=` for `tx.module()`.
* Renamed `tx.PyText` to `tx.TextTree`; the name `PyText` will be deprecated.

### v0.1.29
* Updated `PyText.check_format()`, which now returns a boolean value instead of None.
* Updated the `ignore=` parameter for `tx.module()`, which now accepts a list of path-patterns. Paths matching any of these patterns will be ignored when searching for files.

### v0.1.28
* Fixed issue: failed to display special characters in `*._repr_mimebundle_()`.

### v0.1.27
* New gloabal parameters: `tree_style=`, `table_style=`, `use_mimebundle=`, and `skip_line_numbers=` - find them under `tx.display_params`.
* Defined `display_params.defaults()` for users to get the default values of the parameters.
* New subclass `PyProperty` inherited from `PyMethod`. Class properties will be stored in instances of `PyProperty` instead of `PyMethod` in the future.
* Updated the method `PyText.jumpto()`: it now allows "/" as delimiters (in addition to "."); if a class or callable is defined more than once, jump to the last (previously first) place where it was defined. 
* `PyText` has a `_repr_mimebundle_()` method now.
* New property `PyText.imports`.
* Created a utility class `HTMLTableMaker` in place of `Styler`; this significantly reduces the running overhead of `*._repr_mimebundle_()`.

### v0.1.26
* Updated with the package `re_extensions`: 
  * bugfix for `rsplit()`;
  * new string operation `quote_collapse()`.

### v0.1.25
* Updated `utils.re_extensions`: 
  * **Important:** we've decided to extract `utils.re_extensions` into an independent package named `re_extensions` (presently at v0.0.3), so any future updates should be looked up in https://github.com/Chitaoji/re-extensions instead; we will stay in sync with it, however;
  * `real_findall()` now returns match objects instead of spans and groups;
  * `smart_sub()` accepts a new optional parameter called `count=`;
  * `SmartPattern` supports [] to indicate a Unicode (str) or bytes pattern (like what `re.Pattern` does);
  * new regex operations `smart_split()`, `smart_findall()`, `line_findall()`, `smart_subn()`, and `smart_fullmatch()`;
  * created a namespace `Smart` for all the smart operations;
  * bugfixes for `rsplit()`, `lsplit()`, and `smart_sub()`.
* Reduced the running cost of `PyText.findall()` by taking advantage of the new regex operation `line_findall()`.

### v0.1.24
* New methods `PyText.is_file()` and `PyText.is_dir()` to find out whether the instance represents a file / directory.
* New method `PyText.check_format()` for format checking.
* Defined the comparison ordering methods `__eq__()`, `__gt__()`, and `__ge__()` for `PyText`. They compares two `PyText` object via their absolute paths.
* Updated `utils.re_extensions`: 
  * new regex operations `smart_search()`, `smart_match()`, and `smart_sub()`;
  * new string operation `counted_strip()`;
  * new utility classes `SmartPattern` and `SmartMatch`.
  * new utility functions `find_right_bracket()` and `find_left_bracket()`.

### v0.1.23
* New string operation `utils.re_extensions.word_wrap()`.
* Various improvements.

### v0.1.22
* The module-level function `tx.textpy()` is going to be deprecated to avoid conflicts with the package name `textpy`. Please use `tx.module()` insead.
* New methods `PyText.replace()` and `PyText.delete()`.
* New class `Replacer` as the return type of `PyText.replace()`, with public methods `.confirm()`, `.rollback()`, etc.
* Added a dunder method `PyText.__truediv__()` as an alternative to `PyText.jumpto()`.
* New subclass `PyContent` inherited from `PyText`. A `PyContent` object stores a part of a file that is not storable by instances of other subclasses.

### v0.1.21
* Improved behavior of clickables.

### v0.1.20
* Fixed issue: incorrect file links in the output of `TextPy.findall()`;

### v0.1.19
* Various improvements.

### v0.1.18
* Updated LICENSE.

### v0.1.17
* Refactored README.md.

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
  * `Path` object is now acceptable as the positional argument;
  * new optional parameter `home=` for specifying the home path.
* More flexible presentation of output from `TextPy.findall()`.

### v0.1.4
* Fixed a display issue of README.md on PyPI.

### v0.1.3
* Initial release.