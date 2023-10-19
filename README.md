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
Create a new file named `this_is_a_file.py` under dir `./temp/`:

```py
# ./temp/this_is_a_file.py
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

textpy.textpy("./temp/this_is_a_file.py").findall("var", styler=False)
print(res)
# Output:
# temp/this_is_a_file.py:8: '        self.var_1 = "hahaha"'
# temp/this_is_a_file.py:9: '        self.var_2 = "blabla"'
# temp/this_is_a_file.py:22: '    print(a.var_1, a.var_2)'
```

Also, when using a Jupyter notebook, you can run a cell like this:

```py
from textpy import textpy

textpy("./temp/this_is_a_file.py").findall("var")
```

and the output will be like:

![](https://raw.githubusercontent.com/Chitaoji/textpy/develop/images/example_1.png)

Now suppose you've got a python module consists of a few files, for example, our `textpy` module itself, you can do almost the same thing:

```py
module_path = "textpy/" # you can type any path here
pattern = "note.*k" # type any regular expression here

res = textpy(module_path).findall(pattern, styler=False)
print(res)
# Output:
# textpy_local/textpy/abc.py:158: '            in a Jupyter notebook, by default True.'
# textpy_local/textpy/abc.py:375: '        in a Jupyter notebook.'
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
