import re
from typing import *

SpanNGroup = Tuple[Tuple[int, int], str]
LineSpanNGroup = Tuple[int, Tuple[int, int], str]

__all__ = [
    "rsplit",
    "lsplit",
    "real_findall",
    "pattern_inreg",
    "line_count",
    "line_count_iter",
]


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
    _lstr: str = ""
    while searched:
        _span = searched.span()
        splits.append(_lstr + string[: _span[0]])
        _lstr = searched.group()
        string = string[_span[1] :]
        if maxsplit > 0 and len(splits) >= maxsplit:
            break
        searched = re.search(pattern, string, flags=flags)
    splits.append(_lstr + string)
    return splits


def lsplit(
    pattern: Union[str, re.Pattern],
    string: str,
    maxsplit: int = 0,
    flags: Union[int, re.RegexFlag] = 0,
) -> List[str]:
    """
    Split the string by the occurrences of the pattern. Differences to
    `re.split` that the text of all groups in the pattern are also
    returned, each following a substring on its left, connected with
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
    while searched:
        _span = searched.span()
        splits.append(string[: _span[1]])
        string = string[_span[1] :]
        if maxsplit > 0 and len(splits) >= maxsplit:
            break
        searched = re.search(pattern, string, flags=flags)
    splits.append(string)
    return splits


def real_findall(
    pattern: Union[str, re.Pattern],
    string: str,
    flags: Union[int, re.RegexFlag] = 0,
    linemode: bool = False,
) -> List[Union[SpanNGroup, LineSpanNGroup]]:
    """
    Finds all non-overlapping matches in the string. Differences to
    `re.findall` that it also returns the spans of patterns.

    Parameters
    ----------
    pattern : Union[str, re.Pattern]
        Pattern string.
    string : str
        String to be searched.
    flags : Union[int, re.RegexFlag], optional
        Regex flag, by default 0.
    linemode : bool, optional
        If true, match the pattern on each line of the string, by
        default False.

    Returns
    -------
    List[Union[SpanNGroup, LineSpanNGroup]]
        List of finding result. If `linemode` is false, each list
        element consists of the span and the group of the pattern. If
        `linemode` is true, each list element consists of the line
        number, the span (within the line), and the group of the
        pattern instead.

    """
    finds: List[SpanNGroup] = []
    _sum: int = 0
    _line: int = 1
    _inline_pos: int = 0
    searched = re.search(pattern, string, flags=flags)
    while searched:
        _len_string = len(string)
        _span, _group = searched.span(), searched.group()
        if linemode:
            _lsting = string[: _span[0]]
            _lline = line_count(_lsting) - 1
            _line += _lline
            if _lline > 0:
                _inline_pos = 0
            _lastline_pos = len(_lsting) - 1 - _lsting.rfind("\n")
            finds.append(
                (
                    _line,
                    (
                        _inline_pos + _lastline_pos,
                        _inline_pos + _lastline_pos + _span[1] - _span[0],
                    ),
                    _group,
                )
            )
            _line += line_count(_group) - 1
            if "\n" in _group:
                _inline_pos = len(_group) - 1 - _group.rfind("\n")
            else:
                _inline_pos += max(_lastline_pos + _span[1] - _span[0], 1)
        else:
            finds.append(((_span[0] + _sum, _span[1] + _sum), _group))
            _sum += max(_span[1], 1)
        if _len_string == 0:
            break
        if _span[1] == 0:
            _line += 1 if string[0] == "\n" else 0
            string = string[1:]
        else:
            string = string[_span[1] :]
        searched = re.search(pattern, string, flags=flags)  # search again
    return finds


def pattern_inreg(pattern: str) -> str:
    """
    Invalidates the regular expressions in `pattern`.

    Parameters
    ----------
    pattern : str
        Pattern to be invalidated.

    Returns
    -------
    str
        A new pattern.

    """
    return re.sub("[$^.\[\]*+-?!{},|:#><=\\\\]", lambda x: "\\" + x.group(), pattern)


def line_count(string: str) -> int:
    """
    Counts the number of lines in a string.

    Parameters
    ----------
    string : str
        A string.

    Returns
    -------
    int
        Total number of lines.

    """
    return 1 + len(re.findall("\n", string))


def line_count_iter(iter: Iterable[str]) -> Iterable[Tuple[int, str]]:
    """
    Counts the number of lines in each string, and returns the cumsumed
    values.

    Parameters
    ----------
    iter : Iterable[str]
        An iterable of strings.

    Yields
    ------
    Tuple[int, str]
        Each time, yields the cumsumed number of lines til now together
        with a string found in `iter`, until `iter` is traversed.

    """
    _cnt = 1
    for _str in iter:
        yield _cnt, _str
        _cnt += len(re.findall("\n", _str))
