# textpy
Reads a python file/module and statically analyzes it.

## Installation

```sh
pip install textpy
```

## Examples
Create a new file named `this_is_a_file.py`:

```py
class ThisIsAClass:
    def __init__(self):
        """Write something."""
        self.var_1 = "hahaha"
        self.var_2 = "blabla"


def this_is_a_function(a: ThisIsAClass):
    """
    Write something.

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

res = textpy("this_is_a_file.py").findall("var", styler=False)
print(res)
# Output:
# this_is_a_file.py:4: '        self.var_1 = "hahaha"'
# this_is_a_file.py:5: '        self.var_2 = "blabla"'
# this_is_a_file.py:18: '    print(a.var_1, a.var_2)'
```

Also, when using a Jupyter notebook, you can run a cell like this:

```py
from textpy import textpy

textpy("this_is_a_file.py").findall("var")
```

and the output will be like:

![](https://raw.githubusercontent.com/Chitaoji/textpy/v0.1.3/images/example_1.png)

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

### v0.1.4
* Fixed the display of images on PyPI.

### v0.1.3
* Initial release.
