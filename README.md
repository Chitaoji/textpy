# textpy
Reads a python file/module and statically analyzes it.

## Installation

```sh
pip install textpy
```

## Requirements
```txt
pandas>=1.4.0 # A lower version is also acceptable, but some features will be invalid
attrs>=23.1.0
```

## Examples
Create a new file named `this_is_a_file.py` under dir `./examples/`:

```py
# ./examples/this_is_a_file.py
from typing import *


class MyClass:
    def __init__(self):
        """Write something."""
        self.var_1 = "hahaha"
        self.var_2 = "blabla"


def myfunction(a: MyClass):
    """
    Print something.

    Parameters
    ----------
    a : ThisIsAClass
        An object.

    """
    print(a.var_1, a.var_2)
```

Run the following codes to find all the occurrences of the pattern `"var"` in `this_is_a_file.py`:

```py
from textpy import textpy

textpy.textpy("./examples/this_is_a_file.py").findall("var", styler=False)
print(res)
# Output:
# examples/this_is_a_file.py '        self.var_1 = "hahaha"'
# examples/this_is_a_file.py '        self.var_2 = "blabla"'
# examples/this_is_a_file.py '    print(a.var_1, a.var_2)'
```

Also, when using a Jupyter notebook, you can run a cell like this:

```py
from textpy import textpy

textpy("./examples/this_is_a_file.py").findall("var")
```

and the output will be like:

<table id="T_ea36f">
  <thead>
    <tr>
      <th id="T_ea36f_level0_col0" class="col_heading level0 col0" >source</th>
      <th id="T_ea36f_level0_col1" class="col_heading level0 col1" >match</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td id="T_ea36f_row0_col0" class="data row0 col0" ><a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>this_is_a_file</a>.<a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>MyClass</a>.<a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>__init__</a>:<a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>8</a></td>
      <td id="T_ea36f_row0_col1" class="data row0 col1" >    self.<a href='examples/this_is_a_file.py' style='text-decoration:none;color:#cccccc;background-color:#595959'>var</a>_1 = "hahaha"</td>
    </tr>
    <tr>
      <td id="T_ea36f_row1_col0" class="data row1 col0" ><a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>this_is_a_file</a>.<a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>MyClass</a>.<a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>__init__</a>:<a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>9</a></td>
      <td id="T_ea36f_row1_col1" class="data row1 col1" >    self.<a href='examples/this_is_a_file.py' style='text-decoration:none;color:#cccccc;background-color:#595959'>var</a>_2 = "blabla"</td>
    </tr>
    <tr>
      <td id="T_ea36f_row2_col0" class="data row2 col0" ><a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>this_is_a_file</a>.<a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>myfunction</a>:<a href='examples/this_is_a_file.py' style='text-decoration:none;color:inherit'>22</a></td>
      <td id="T_ea36f_row2_col1" class="data row2 col1" >    print(a.<a href='examples/this_is_a_file.py' style='text-decoration:none;color:#cccccc;background-color:#595959'>var</a>_1, a.<a href='examples/this_is_a_file.py' style='text-decoration:none;color:#cccccc;background-color:#595959'>var</a>_2)</td>
    </tr>
  </tbody>
</table>

Note that in the Jupyter notebook case, the matched substrings are **clickable**, linking to where the patterns were found.

Now suppose you've got a python module consists of a few files, for example, our `textpy` module itself, you can do almost the same thing:

```py
module_path = "textpy/" # you can type any path here
pattern = "note.*k" # type any regular expression here

res = textpy(module_path).findall(pattern, styler=False)
print(res)
# Output:
# textpy_local/textpy/abc.py '            in a Jupyter notebook, by default True.'
# textpy_local/textpy/abc.py '        in a Jupyter notebook.'
```
## License
This project falls under the BSD 2-Clause License.

## History

### v0.1.5 (not published yet)
* Compatible with pandas version lower than 1.4.0.
* Now `textpy.textpy` accepts either a string or a `Path` object as its parameter.

### v0.1.4
* Fixed the display of images on PyPI.

### v0.1.3
* Initial release.
