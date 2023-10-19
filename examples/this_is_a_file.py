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
