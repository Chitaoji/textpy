# textpy
Reads a python file/module and statically analyzes it, this works well with Jupyter extensions in VScode.

## Installation

```sh
pip install textpy
```

## Requirements
```txt
pandas>=1.4.0 
# A lower version is also acceptable, but some features will be invalid.
```

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

Run the following codes to find all the occurrences of the pattern `"va"` in `myfile.py`:

```py
from textpy import textpy

res = textpy("./examples/myfile.py").findall("va", styler=False)
print(res)
# Output:
# examples/myfile.py:10: '        self.var_1 = "hahaha"'
# examples/myfile.py:11: '        self.var_2 = "blabla"'
# examples/myfile.py:24: '    print(a.var_1, a.var_2)'
```

Also, when using a Jupyter notebook in VScode, you can run a cell like this:

```py
from textpy import textpy

textpy("./examples/myfile.py").findall("va")
```

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
          style='text-decoration:none;color:inherit'>10</a></td>
      <td id="T_eb71c_row0_col1" class="data row0 col1"> self.<a href='examples/myfile.py'
          style='text-decoration:none;color:#cccccc;background-color:#595959'>va</a>r_1 = "hahaha"</td>
    </tr>
    <tr>
      <td id="T_eb71c_row1_col0" class="data row1 col0"><a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>myfile</a>.<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>MyClass</a>.<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>__init__</a>:<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>11</a></td>
      <td id="T_eb71c_row1_col1" class="data row1 col1"> self.<a href='examples/myfile.py'
          style='text-decoration:none;color:#cccccc;background-color:#595959'>va</a>r_2 = "blabla"</td>
    </tr>
    <tr>
      <td id="T_eb71c_row2_col0" class="data row2 col0"><a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>myfile</a>.<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>print_my_class</a>:<a href='examples/myfile.py'
          style='text-decoration:none;color:inherit'>24</a></td>
      <td id="T_eb71c_row2_col1" class="data row2 col1"> print(a.<a href='examples/myfile.py'
          style='text-decoration:none;color:#cccccc;background-color:#595959'>va</a>r_1, a.<a href='examples/myfile.py'
          style='text-decoration:none;color:#cccccc;background-color:#595959'>va</a>r_2)</td>
    </tr>
  </tbody>
</table>

Note that in the Jupyter notebook case, the matched substrings are **clickable**, linking to where the patterns were found.

Now suppose you've got a python module consists of a few files, for example, our `textpy` module itself, you can do almost the same thing:

```py
module_path = "textpy/" # you can type any path here
pattern = "note.*k" # type any regular expression here

res = textpy(module_path).findall("note.*k", styler=False, line_numbers=False)
print(res)
# Output:
# textpy/abc.py: '            in a Jupyter notebook, this only takes effect when'
# textpy/abc.py: '        in a Jupyter notebook.'
```

## See Also
### Github repository
* https://github.com/Chitaoji/textpy/

### PyPI project
* https://pypi.org/project/textpy/

## License
This project falls under the BSD 2-Clause License.

## History

### v0.1.16
* Lazily imported *pandas*

### v0.1.15
* Reduced the time cost for importing.

### v0.1.12
* New optional parameters for `textpy.TextPy.findall` :
  * `whole_word` : whether to match whole words only.
  * `case_sensitive` : specifies case sensitivity.

### v0.1.10
* New optional parameter for `textpy.textpy` :
  * `encoding` : specifies encoding.

### v0.1.9
* Removing unnecessary dependencies.

### v0.1.8
* Bugfix for Windows.

### v0.1.5
* Compatible with *pandas* versions lower than 1.4.0.
* Updated `textpy.textpy` :
  * `Path` objects are now acceptable as parameters.
  * New optional parameter `home` to specify the home path.
* More flexible presentation of output when using `textpy.TextPy.findall`.

### v0.1.4
* Fixed a display problem of `README.md` on PyPI.

### v0.1.3
* Initial release.
