"""Setup the package."""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import io
import os
import re
import sys
from shutil import rmtree
from typing import List, Union

from setuptools import Command, find_packages, setup

# Package meta-data.
NAME = "textpy"
DESCRIPTION = "Reads a python file/module and statically analyzes it."
URL = "https://github.com/Chitaoji/textpy"
EMAIL = "2360742040@qq.com"
AUTHOR = "Chitaoji"
REQUIRES_PYTHON = ">=3.8.13"
VERSION = None
REQUIRED = ["lazyr", "pandas"]
EXTRAS = {}


here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        LONG_DESCRIPTION = "\n" + f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = DESCRIPTION


# Load the package's __version__.py module as a dictionary.
about = {}
python_exec = exec
if not VERSION:
    PROJECT_SLUG = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(
        os.path.join(here, PROJECT_SLUG, "__version__.py"), encoding="utf-8"
    ) as f:
        python_exec(f.read(), about)
else:
    about["__version__"] = VERSION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print(f"\033[1m{s}\033[0m")

    def initialize_options(self):
        """Initializes options."""

    def finalize_options(self):
        """Finalizes options."""

    def run(self):
        """Runs commands."""
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system(f"{sys.executable} setup.py sdist bdist_wheel --universal")

        self.status("Uploading the package to PyPI via Twine…")
        os.system("twine upload dist/*")

        self.status("Pushing git tags…")
        os.system(f"git tag v{about['__version__']}")
        os.system("git push --tags")

        sys.exit()


def rsplit(
    pattern: Union[str, re.Pattern],
    string: str,
    maxsplit: int = 0,
    flags: Union[int, re.RegexFlag] = 0,
) -> List[str]:
    """
    Split the string by the occurrences of the pattern. Differences to
    `re.split` that the text of all groups in the pattern are also
    returned, each followed by a substring on its right, connected with
    `""`'s.

    Parameters
    ----------
    pattern : Union[str, re.Pattern]
        Pattern string.
    string : str
        String to be splitted.
    maxsplit : int, optional
        Max number of splits, if specified to be 0, there will be no
        more limits, by default 0.
    flags : Union[int, re.RegexFlag], optional
        Regex flag, by default 0.

    Returns
    -------
    List[str]
        List of substrings.

    """
    splits: List[str] = []
    searched = re.search(pattern, string, flags=flags)
    left: str = ""
    while searched:
        span = searched.span()
        splits.append(left + string[: span[0]])
        left = searched.group()
        string = string[span[1] :]
        if len(splits) >= maxsplit > 0:
            break
        searched = re.search(pattern, string, flags=flags)
    splits.append(left + string)
    return splits


def readme2doc(readme: str) -> str:
    """
    Takes a readme string as input and returns a modified version of the
    readme string without certain sections.

    Parameters
    ----------
    readme : str
        A string containing the content of a README file.

    Returns
    -------
    str
        A modified version of the readme string.

    """
    doc = ""
    for i in rsplit("\n## ", readme):
        head = re.search(" .*\n", i).group()[1:-1]
        if head not in {"Installation", "Requirements", "History"}:
            doc += i
    doc = re.sub("<!--html-->.*<!--/html-->", "", doc, flags=re.DOTALL)
    return (
        "\n".join(
            x
            if len(x) <= 100
            else x[: (i := x.rfind(" ", None, 100))] + "\n" + x[i + 1 :]
            for x in doc.splitlines()
        )
        + "\n\n"
    )


# Import the __init__.py and change the module docstring.
try:
    with io.open(os.path.join(here, NAME, "__init__.py"), "r", encoding="utf-8") as f:
        module_file = f.read()
    doc_new = readme2doc(LONG_DESCRIPTION)
    module_file = re.sub('^""".*"""', f'"""{doc_new}"""', module_file, flags=re.DOTALL)
    module_file = re.sub("^'''.*'''", f"'''{doc_new}'''", module_file, flags=re.DOTALL)
    with io.open(os.path.join(here, NAME, "__init__.py"), "w", encoding="utf-8") as f:
        f.write(module_file)
except FileNotFoundError:
    pass


setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["examples"]),
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="BSD",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
)
