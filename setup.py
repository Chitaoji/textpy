"""
Setup the package.

To use the full functionality of this file, you must:

```sh
$ pip install pyyaml
$ pip install twine
$ pip install wheel
```
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, Final, List, Optional, Union

import yaml
from setuptools import Command, find_packages, setup

here = Path(__file__).parent

# Load the package's meta-data from metadata.yml.
yml: Dict[str, Any] = yaml.safe_load((here / "metadata.yml").read_text())
NAME: Final[str] = yml["NAME"]
VERSION: Final[Optional[str]] = yml["VERSION"]
SUMMARY: Final[str] = yml["SUMMARY"]
HOMEPAGE: Final[str] = yml["HOMEPAGE"]
AUTHOR: Final[str] = yml["AUTHOR"]
AUTHOR_EMAIL: Final[str] = yml["AUTHOR_EMAIL"]
REQUIRES_PYTHON: Final[str] = yml["REQUIRES_PYTHON"]
REQUIRES: Final[List[str]] = yml["REQUIRES"]
EXTRAS: Final[Dict] = yml["EXTRAS"]
PACKAGE_DIR = "src"

# Import the README and use it as the long-description.
try:
    long_description = "\n" + (here / "README.md").read_text()
except FileNotFoundError:
    long_description = SUMMARY


# Load the package's __version__.py module as a dictionary.
about = {}
python_exec = exec
if not VERSION:
    try:
        python_exec((here / PACKAGE_DIR / "__version__.py").read_text(), about)
    except FileNotFoundError:
        about["__version__"] = "0.0.0"
else:
    about["__version__"] = VERSION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Print things in bold."""
        print(f"\033[1m{s}\033[0m")

    def initialize_options(self):
        """Initialize options."""

    def finalize_options(self):
        """Finalize options."""

    def run(self):
        """Run commands."""
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
    `re.split()` that all groups in the pattern are also returned, each
    connected with the substring on its right.

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


def __maxsplit(string: str, maximum: int = 1):
    head, tail = string, ""
    if len(string) > maximum:
        if (i := string.rfind(" ", None, 1 + maximum)) > 0 and (
            l := string[:i]
        ).strip():
            head, tail = l, string[1 + i :]
        elif (j := string.find(" ", 1 + maximum)) > 0:
            head, tail = string[:j], string[1 + j :]
    return head.rstrip(), tail.strip()


def word_wrap(string: str, maximum: int = 100) -> str:
    """
    Takes a string as input and wraps the text into multiple lines,
    ensuring that each line has a maximum length of characters.

    Parameters
    ----------
    string : str
        The input text that needs to be word-wrapped.
    maximum : int, optional
        Specifies the maximum length of each line in the word-wrapped
        string, by default 100.

    Returns
    -------
        A string with the input string wrapped to a maximum line length
        of 100 characters.

    """
    if maximum < 1:
        raise ValueError(f"expected maximum > 0, got {maximum} instead")
    lines: List[str] = []
    for x in string.splitlines():
        while True:
            l, x = __maxsplit(x, maximum=maximum)
            lines.append(l)
            if not x:
                break
    return "\n".join(lines)


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
    return word_wrap(doc) + "\n\n"


class ReadmeFormatError(Exception):
    """Raised when the README has a wrong format."""


if __name__ == "__main__":
    # Import the __init__.py and change the module docstring.
    try:
        init_path = here / PACKAGE_DIR / "__init__.py"
        module_file = init_path.read_text()
        new_doc = readme2doc(long_description)  # pylint: disable=invalid-name
        if "'''" in new_doc and '"""' in new_doc:
            raise ReadmeFormatError("Both \"\"\" and ''' are found in the README")
        if '"""' in new_doc:
            new_doc = f"'''{new_doc}'''"
        else:
            new_doc = f'"""{new_doc}"""'
        module_file = re.sub(
            "^\"\"\".*\"\"\"|^'''.*'''|^", new_doc, module_file, flags=re.DOTALL
        )
        init_path.write_text(module_file)
    except FileNotFoundError:
        pass

    # Where the magic happens.
    setup(
        name=NAME,
        version=about["__version__"],
        description=SUMMARY,
        long_description=long_description,
        long_description_content_type="text/markdown",
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        python_requires=REQUIRES_PYTHON,
        url=HOMEPAGE,
        packages=[
            x.replace(PACKAGE_DIR, NAME) for x in find_packages(exclude=["examples"])
        ],
        package_dir={NAME: PACKAGE_DIR},
        install_requires=REQUIRES,
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
